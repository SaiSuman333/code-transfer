# src/uimon/utils.py
import yaml, re, datetime, random, string

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def new_run_id():
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    rnd = "".join(random.choices(string.ascii_lowercase+string.digits, k=4))
    return f"{ts}-{rnd}"

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"
