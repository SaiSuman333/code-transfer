# src/uimon/differ_text.py
import difflib

def text_diff_and_score(base_text: str, new_text: str):
    sm = difflib.SequenceMatcher(a=base_text, b=new_text)
    similarity = sm.ratio()  # 0..1 (1=identical)
    unified = "\n".join(difflib.unified_diff(
        base_text.splitlines(), new_text.splitlines(),
        fromfile="baseline", tofile="current", lineterm=""
    ))
    return {"similarity": float(similarity), "unified_diff": unified[:20000]}
