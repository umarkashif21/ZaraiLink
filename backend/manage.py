"""Django's command-line utility for administrative tasks."""
import os
import sys
import warnings

warnings.filterwarnings(
    "ignore",
    message=r"for .*: copying from a non-meta parameter in the checkpoint to a meta parameter.*",
    category=UserWarning,
    module=r"torch\.nn\.modules\.module",
)


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
