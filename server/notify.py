"""Email through Resend (https://resend.com), sent in the background.

Set on Fly as secrets:
  RESEND_API_KEY        the API key
  ROCKETGEN_NOTIFY_TO   where new-order emails go (the owner)
  ROCKETGEN_MAIL_FROM   sender, e.g. "Rocket Builder <orders@quiverdesignworks.net>"
                        (a domain verified in Resend; until then Resend's
                        test sender onboarding@resend.dev, which can only
                        mail the Resend account's own address)

Without RESEND_API_KEY nothing is sent and the order still goes through;
the Orders page and the PC sync still show it.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import urllib.request

log = logging.getLogger("rocketbuilder.notify")


def configured() -> bool:
    return bool(os.environ.get("RESEND_API_KEY") and os.environ.get("ROCKETGEN_NOTIFY_TO"))


def _send(to: str, subject: str, text: str) -> None:
    body = json.dumps({"from": os.environ.get("ROCKETGEN_MAIL_FROM", "Rocket Builder <onboarding@resend.dev>"),
                       "to": [to], "subject": subject, "text": text}).encode()
    req = urllib.request.Request("https://api.resend.com/emails", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            log.info("email sent: %s (%s)", subject, r.status)
    except Exception as e:  # never let email break an order
        log.error("email failed: %s: %s", subject, e)


def owner(subject: str, text: str) -> None:
    """Emails the owner without holding up the request."""
    if not configured():
        log.info("email not configured; skipped: %s", subject)
        return
    threading.Thread(target=_send, args=(os.environ["ROCKETGEN_NOTIFY_TO"], subject, text), daemon=True).start()
