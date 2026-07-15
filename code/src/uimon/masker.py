# src/uimon/masker.py
def apply_masks(page, selectors):
    if not selectors: return
    css = ", ".join(selectors)
    # Blur volatile elements (timestamps/user avatar etc.)
    page.add_style_tag(content=f"{css} {{ filter: blur(6px) brightness(0.9); }}")
