from typing import Optional
from app.config import settings

# We lazily import heavy deps to keep startup fast.
def try_load_pipeline():
    try:
        from transformers import pipeline  # type: ignore
        return pipeline
    except Exception:
        return None

def caption_image(image_path: str) -> Optional[str]:
    model_name = settings.CAPTION_MODEL.strip()
    if not model_name or model_name.lower() == "disabled":
        return None
    pipeline = try_load_pipeline()
    if pipeline is None:
        # Transformers not installed or failed to import
        return None
    try:
        cap = pipeline("image-to-text", model=model_name)
        res = cap(image_path)
        if isinstance(res, list) and res:
            # Different models return different field keys; try common ones
            text = res[0].get("generated_text") or res[0].get("caption") or res[0].get("text")
            return str(text) if text else None
        return None
    except Exception:
        # If model download fails or anything else goes wrong, skip captioning
        return None
