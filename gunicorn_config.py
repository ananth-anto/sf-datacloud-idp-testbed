# Gunicorn config: redact OAuth code from /auth/callback in access logs
import os
import re
from urllib.parse import parse_qs, urlencode

from gunicorn.glogging import Logger


class RedactCallbackCodeLogger(Logger):
    """Redact OAuth 'code' query param from /auth/callback URLs in access logs."""

    def atoms(self, resp, req, environ, request_time):
        atoms = super().atoms(resp, req, environ, request_time)
        # Redact OAuth code in request line (e.g. "GET /auth/callback?code=xxx HTTP/1.1")
        raw = atoms.get("r") or ""
        if "/auth/callback" in raw and "code=" in raw:
            parts = raw.split(" ", 2)  # method, path?query, protocol
            if len(parts) == 3 and "?" in parts[1]:
                path, qs = parts[1].split("?", 1)
                parsed = parse_qs(qs, keep_blank_values=True)
                if "code" in parsed:
                    parsed["code"] = ["[REDACTED]"]
                parts[1] = path + "?" + urlencode(parsed, doseq=True)
                atoms["r"] = " ".join(parts)
            else:
                atoms["r"] = re.sub(r"code=[^&\s]+", "code=[REDACTED]", raw)
        return atoms


# Use custom logger so access logs don't contain OAuth codes
logger_class = RedactCallbackCodeLogger

# Standard settings
workers = 1
bind = "0.0.0.0:{}".format(os.environ.get("PORT", "5000"))
accesslog = "-"
errorlog = "-"
loglevel = "info"
