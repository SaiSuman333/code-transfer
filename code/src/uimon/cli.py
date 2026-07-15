# src/uimon/cli.py
import argparse, json
from pathlib import Path
from .utils import load_config, new_run_id
from .collector import capture_targets
from .differ_text import text_diff_and_score
from .differ_image import image_diff_and_score
from .rules import run_rules
from .scorer import combined_severity, combine_scores
from .reporter import build_report

def main():
    ap = argparse.ArgumentParser(prog="uimon", description="UI Change Evidence Bot")
    ap.add_argument("command", choices=["baseline", "run", "report"])
    ap.add_argument("-c", "--config", default="targets.yaml")
    args = ap.parse_args()

    cfg = load_config(args.config)

    if args.command == "baseline":
        capture_targets(cfg, baseline=True)
        print("✅ Baseline captured.")
        return

    if args.command == "run":
        run_id = new_run_id()
        run_dir = Path("runs") / run_id
        (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)

        artifacts = capture_targets(cfg, baseline=False, run_dir=run_dir / "artifacts")
        rows = []
        for art in artifacts:
            bdir = Path("baselines") / art["slug"]
            base_text = (bdir / "text.txt").read_text(encoding="utf-8", errors="ignore")
            curr_text = (art["paths"]["text"]).read_text(encoding="utf-8", errors="ignore")
            text_res = text_diff_and_score(base_text, curr_text)

            img_res = image_diff_and_score(bdir / "screenshot.png", art["paths"]["screenshot"], art["paths"]["diff"])
            combined = combine_scores(text_res["similarity"], img_res["distance"])
            severity = combined_severity(combined)

            rules_res = run_rules(art["rules"], art["latest_html"])

            rows.append({
                "name": art["name"], "url": art["url"], "slug": art["slug"], "meta": art["meta"],
                "scores": {
                    "text_similarity": text_res["similarity"],
                    "image_distance": img_res["distance"],
                    "combined": combined, "severity": severity
                },
                "rules": rules_res,
                "paths": {k: str(v) for k, v in art["paths"].items()},
                "diff_preview": {"text_unified": text_res["unified_diff"],
                                 "image_diff_path": str(art["paths"]["diff"])}
            })

        (run_dir / "run.json").write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
        report_path = build_report(run_dir, rows)
        print(f"✅ Report: {report_path}")

    if args.command == "report":
        runs = sorted(Path("runs").glob("*/run.json"))
        if not runs:
            print("No runs found. Run `python -m uimon baseline -c targets.yaml` then `python -m uimon run -c targets.yaml`.")
            return
        run_dir = runs[-1].parent
        data = json.loads((runs[-1]).read_text(encoding="utf-8"))
        report_path = build_report(run_dir, data["rows"])
        print(f"✅ Regenerated: {report_path}")
