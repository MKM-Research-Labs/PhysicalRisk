"""Gunicorn settings for the PhysicalRisk web server.

    gunicorn --config gunicorn.conf.py wsgi:app

ONE worker with threads, carried over from the agent this replaces. The platform
holds state in its own store and the generators are long-running and CPU-bound;
adding worker processes would contend rather than help, and nothing here is serving
the kind of concurrency that would justify it.

Loopback only. The previous agent bound 0.0.0.0:5013, putting the platform on the
LAN. The other three services on this machine bind loopback and are reached through
Tailscale Serve; this one now matches, and is reachable from the machine itself
until a Serve route is added deliberately.

Logs live in ~/Library/Logs/PhysicalRisk, not in the repo. launchd cannot create an
intermediate directory for a redirect target, and the old agent pointed at a repo
`logs/` directory that a fresh clone does not contain -- so it failed on every
attempt. Keeping logs outside the working tree also survives re-cloning, which this
repo has now needed once.
"""
import os

_LOGS = os.path.expanduser("~/Library/Logs/PhysicalRisk")

bind = "127.0.0.1:5013"
workers = 1
threads = 4
worker_class = "gthread"
timeout = 60
graceful_timeout = 30
proc_name = "physicalrisk"
control_socket = os.path.expanduser("~/.gunicorn/physicalrisk.ctl")
accesslog = os.path.join(_LOGS, "access.log")
errorlog = os.path.join(_LOGS, "error.log")
loglevel = "info"
