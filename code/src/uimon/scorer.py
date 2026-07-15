# src/uimon/scorer.py
def combine_scores(text_similarity: float, image_distance: float, w_text=0.5, w_img=0.5):
    text_change = 1.0 - text_similarity
    combined = w_text*text_change + w_img*image_distance
    return float(min(max(combined, 0.0), 1.0))

def combined_severity(combined, low=0.25, high=0.55):
    if combined < low: return "LOW"
    if combined < high: return "MEDIUM"
    return "HIGH"
