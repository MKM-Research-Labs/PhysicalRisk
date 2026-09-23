# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
