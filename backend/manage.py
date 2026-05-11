"""Django's command-line utility for administrative tasks."""
import os
import re
import sys
import warnings

# Hush TensorFlow's "this binary is optimized for ..." INFO line. Must be set
# before any tensorflow import, which means before Django/our apps load.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

# Some C-extension types (Swig-generated) emit DeprecationWarnings during
# interpreter finalization, after warnings.showwarning has been torn down.
# The only way to silence those is via PYTHONWARNINGS, which is read at
# interpreter startup — so we re-exec ourselves once with it set.
if not os.environ.get("ZL_WARN_FILTER_APPLIED"):
    # Note: PYTHONWARNINGS message-match is case-sensitive starts-with, and
    # the three offenders are SwigPyPacked, SwigPyObject, swigvarlink (mixed
    # case). Match on the common case-stable prefix instead.
    _extra = "ignore:builtin type:DeprecationWarning"
    _existing = os.environ.get("PYTHONWARNINGS", "")
    os.environ["PYTHONWARNINGS"] = f"{_extra},{_existing}".rstrip(",")
    os.environ["ZL_WARN_FILTER_APPLIED"] = "1"
    os.execv(sys.executable, [sys.executable, *sys.argv])

warnings.filterwarnings(
    "ignore",
    message=r"for .*: copying from a non-meta parameter in the checkpoint to a meta parameter.*",
    category=UserWarning,
    module=r"torch\.nn\.modules\.module",
)
# Cosmetic startup warnings from third-party libs we don't control. None
# affect functionality; they just clutter the runserver banner.
warnings.filterwarnings(
    "ignore",
    message=r"Pandas requires version '1\.3\.6' or newer of 'bottleneck'.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"Unable to import Axes3D.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"`resume_download` is deprecated.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"The sentencepiece tokenizer that you are converting to a fast tokenizer.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"builtin type Swig(PyPacked|PyObject|varlink) has no __module__ attribute",
    category=DeprecationWarning,
)

# TensorFlow and other heavy libs call `warnings.resetwarnings()` during their
# own import, which wipes the filters above. Wrap `showwarning` so the Swig
# DeprecationWarnings are dropped at display time regardless of filter state.
_SUPPRESS_PATTERNS = (
    re.compile(r"builtin type \w+ has no __module__ attribute", re.IGNORECASE),
)
_orig_showwarning = warnings.showwarning


def _filtered_showwarning(message, category, filename, lineno, file=None, line=None):
    text = str(message)
    for pat in _SUPPRESS_PATTERNS:
        if pat.search(text):
            return
    _orig_showwarning(message, category, filename, lineno, file, line)


warnings.showwarning = _filtered_showwarning

# Quiet huggingface_hub's tqdm progress bars during model fetches and silence
# transformers' "Asking to truncate to max_length" info log. These are
# library-emitted noise on warmup, not actionable for the developer.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")


# Commands that meaningfully use the cache and so should ensure Redis is up.
# Other commands (migrate, makemigrations, shell, collectstatic, ...) skip the
# spawn so we don't pay for it on every CLI invocation.
_COMMANDS_NEEDING_REDIS = {"runserver", "runserver_plus"}


def _ensure_redis_running():
    """Start a Redis daemon on :6379 if nothing is listening there.

    Idempotent: if a Redis is already running (whether started by us, by a
    previous app boot, or by systemd), this is a no-op. The daemon survives
    Ctrl+C of the Django process so cache stays warm across `runserver`
    restarts; stop it explicitly with `redis-cli shutdown` when you want it
    gone.
    """
    import socket
    import shutil
    import subprocess

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        if sock.connect_ex(("127.0.0.1", 6379)) == 0:
            return  # Already up.
    finally:
        sock.close()

    binary = shutil.which("redis-server")
    if not binary:
        print(
            "[manage.py] redis-server not on PATH; Django will fall back to "
            "LocMemCache (in-process). Install Redis to enable shared cache.",
            file=sys.stderr,
        )
        return

    try:
        subprocess.run(
            [
                binary,
                "--port", "6379",
                "--daemonize", "yes",
                "--save", "",            # disable RDB snapshots — cache is ephemeral
                "--appendonly", "no",    # disable AOF — same reason
                "--dir", "/tmp",         # user-writable working dir
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        print("[manage.py] Started Redis daemon on :6379 (ephemeral, app-managed).",
              file=sys.stderr)
    except Exception as e:
        print(f"[manage.py] Could not start Redis ({type(e).__name__}: {e}); "
              "Django will fall back to LocMemCache.", file=sys.stderr)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zarailink.settings')

    # Spawn Redis only for commands that benefit from it.
    if len(sys.argv) > 1 and sys.argv[1] in _COMMANDS_NEEDING_REDIS:
        _ensure_redis_running()

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
