# app/caption.py
from typing import Optional
from loguru import logger
from app.config import settings

_pipeline = None  # cache across calls

def _pick_device_arg():
    """Prefer Apple Silicon (MPS) on macOS if available, else CPU."""
    try:
        import torch  # type: ignore
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"

def caption_image(image_path: str) -> Optional[str]:
    model_name = (settings.CAPTION_MODEL or "").strip()
    if not model_name or model_name.lower() == "disabled":
        # Captioning is intentionally off
        return None

    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline  # type: ignore
        except Exception as e:
            # transformers not installed or failed to import
            return None
        try:
            device = _pick_device_arg()
            _pipeline = pipeline("image-to-text", model=model_name, device=device)
        except Exception:
            # model download or init failed
            return None

    try:
        # Slightly longer generations than default
        res = _pipeline(image_path, max_new_tokens=30)
        if isinstance(res, list) and res:
            text = res[0].get("generated_text") or res[0].get("caption") or res[0].get("text")
            return str(text) if text else None
        return None
    except Exception:
        # Any runtime failure -> skip caption silently
        return None
