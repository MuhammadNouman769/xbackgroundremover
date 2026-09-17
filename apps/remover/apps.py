import os
import sys

from django.apps import AppConfig

# Management commands where warming up the AI model would just waste time
# (and, on a fresh machine, force an unwanted model download).
_SKIP_WARMUP_COMMANDS = {
    'makemigrations', 'migrate', 'collectstatic', 'createsuperuser',
    'shell', 'shell_plus', 'test', 'dbshell', 'loaddata', 'dumpdata', 'check',
}


class RemoverConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.remover'
    label = 'remover'

    def ready(self):
        """
        Pre-loads the rembg model in a background thread as soon as the
        server starts, instead of on the first real visitor's request.
        This is what removes the "first click takes forever" feeling —
        by the time someone opens the site and picks an image, the model
        is usually already sitting in memory.
        """
        if len(sys.argv) > 1 and sys.argv[1] in _SKIP_WARMUP_COMMANDS:
            return
        # `runserver`'s autoreloader starts two processes; only warm up in
        # the one that actually serves requests (RUN_MAIN == 'true').
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return

        import threading

        def _warm_up():
            try:
                from .utils import _get_session
                _get_session()
            except Exception:  # noqa: BLE001 - warmup must never crash startup
                import logging
                logging.getLogger('remover').exception('Model warm-up failed')

        threading.Thread(target=_warm_up, daemon=True).start()
