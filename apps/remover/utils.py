"""
Core image-processing engine for Xbg Remove.

Uses `rembg` (an on-device U2-Net based model, via onnxruntime) to cut the
foreground out of an uploaded photo, exactly like the removal.ai reference
site. The first call downloads the ~170MB model file and caches it under
~/.u2net — after that everything runs fully offline, so per-image cost is
just server CPU, not a paid third-party API.
"""

import io
import logging

from PIL import Image

logger = logging.getLogger('remover')

# The rembg "new_session" object is expensive to create, so it is built
# once per worker process and reused for every request.
_session = None


def _get_session():
    global _session
    if _session is None:
        from rembg import new_session
        _session = new_session('u2net')
    return _session


def remove_background(image_bytes: bytes) -> bytes:
    """
    Takes raw image bytes, returns PNG bytes with the background removed
    (transparent alpha channel).
    """
    from rembg import remove

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
