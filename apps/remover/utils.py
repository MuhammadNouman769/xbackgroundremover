"""
Core image-processing engine for Xbg Remove.

Uses `rembg` (an on-device U2-Net based model, via onnxruntime) to cut the
foreground out of an uploaded photo, exactly like the removal.ai reference
site. The model is downloaded once (cached under ~/.u2net) and, after that,
everything runs fully offline — so per-image cost is just server CPU, not a
paid third-party API.

SPEED NOTES (why this used to feel slow, and what fixes it):
1. Model choice — 'u2net' (~170MB) is accurate but slow on CPU. We default
   to 'u2netp' (~4MB, a distilled/lighter version) which is several times
   faster with only a small quality trade-off. Override with the
   REMBG_MODEL env var if you want the heavier model back.
2. Model loading — building a session from the model file is expensive.
   It now happens ONCE per worker process (cached in `_session`) and is
   pre-warmed in a background thread when Django starts
   (see apps/remover/apps.py -> ready()), instead of happening on a real
   user's first request.
3. Image size — a 12MP phone photo has way more pixels than the model
   needs. We downscale anything larger than MAX_DIMENSION before running
   inference; this is usually the single biggest speed win for real-world
   uploads.
"""

import io
import logging

from django.conf import settings
from PIL import Image

logger = logging.getLogger('remover')

# Anything larger than this (on the longest side) gets downscaled before
# being sent through the model — inference time grows roughly with pixel
# count, so this alone can cut a multi-second wait down a lot for large
# photos, without any visible quality loss for a bg-removal use case.
MAX_DIMENSION = 1600

# The rembg "session" (loaded model) is expensive to create, so it is
# built once per worker process and reused for every request.
_session = None


def _get_model_name() -> str:
    return getattr(settings, 'REMBG_MODEL', 'u2netp')


def _get_session():
    global _session
    if _session is None:
        from rembg import new_session
        _session = new_session(_get_model_name())
    return _session


def _downscale_if_needed(image_bytes: bytes) -> bytes:
    """Shrinks large images before inference; leaves small ones untouched."""
    img = Image.open(io.BytesIO(image_bytes))
    if max(img.size) <= MAX_DIMENSION:
        return image_bytes

    img_format = img.format or 'JPEG'
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
    buffer = io.BytesIO()
    img.convert('RGB' if img_format == 'JPEG' else img.mode).save(buffer, format=img_format)
    return buffer.getvalue()


def remove_background(image_bytes: bytes) -> bytes:
    """
    Takes raw image bytes, returns PNG bytes with the background removed
    (transparent alpha channel).
    """
    from rembg import remove

    image_bytes = _downscale_if_needed(image_bytes)
    session = _get_session()
    output_bytes = remove(image_bytes, session=session)
    return output_bytes


def apply_color_background(cutout_bytes: bytes, hex_color: str) -> bytes:
    """Composites a transparent cutout onto a solid colour background."""
    hex_color = hex_color or '#FFFFFF'
    foreground = Image.open(io.BytesIO(cutout_bytes)).convert('RGBA')
    background = Image.new('RGBA', foreground.size, hex_color)
    background.alpha_composite(foreground)
    buffer = io.BytesIO()
    background.convert('RGB').save(buffer, format='PNG')
    return buffer.getvalue()


def apply_image_background(cutout_bytes: bytes, background_file) -> bytes:
    """Composites a transparent cutout onto a user-supplied background image."""
    foreground = Image.open(io.BytesIO(cutout_bytes)).convert('RGBA')
    background = Image.open(background_file).convert('RGBA')
    background = background.resize(foreground.size)
    background.alpha_composite(foreground)
    buffer = io.BytesIO()
    background.convert('RGB').save(buffer, format='PNG')
    return buffer.getvalue()


def process_image(original_file, background_type, background_color=None, background_image=None):
    """
    High-level entry point used by the view. Returns (success, result_bytes_or_None, error_message).
    """
    try:
        original_file.seek(0)
        raw_bytes = original_file.read()

        cutout_bytes = remove_background(raw_bytes)

        if background_type == 'color':
            result_bytes = apply_color_background(cutout_bytes, background_color)
        elif background_type == 'image' and background_image:
            result_bytes = apply_image_background(cutout_bytes, background_image)
        else:
            result_bytes = cutout_bytes  # transparent PNG

        return True, result_bytes, ''
    except Exception as exc:  # noqa: BLE001 - we want to log & show a friendly message
        logger.exception('Background removal failed')
        return False, None, str(exc)
