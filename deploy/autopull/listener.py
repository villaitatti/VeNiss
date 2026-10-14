#!/usr/bin/env python3
"""
Receives GitHub push webhooks for villaitatti/VeNiss. On a correctly signed
push to master it touches TRIGGER_FILE and does nothing else: the deploy
itself runs on the host from cron (see README.md).
"""

import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SECRET = os.environ["WEBHOOK_SECRET"].encode()
TRIGGER_FILE = Path(os.environ.get("TRIGGER_FILE", "/trigger/deploy"))
PATH = "/_hooks/deploy"
MAX_BODY = 1024 * 1024


class Handler(BaseHTTPRequestHandler):
    server_version = "veniss-autopull"
    sys_version = ""

    def reply(self, status, text=""):
        body = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.reply(405)

    def do_POST(self):
        if self.path != PATH:
            return self.reply(404)
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self.reply(411)
        if not 0 < length <= MAX_BODY:
            return self.reply(413)
        body = self.rfile.read(length)

        expected = "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, self.headers.get("X-Hub-Signature-256", "")):
            return self.reply(401)

        event = self.headers.get("X-GitHub-Event", "")
        if event == "ping":
            return self.reply(200, "pong")
        if event != "push":
            return self.reply(204)
        try:
            ref = json.loads(body).get("ref")
        except (ValueError, AttributeError):
            return self.reply(400)
        if ref != "refs/heads/master":
            return self.reply(204)

        TRIGGER_FILE.touch()
        self.reply(202, "deploy queued")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 9000), Handler).serve_forever()
