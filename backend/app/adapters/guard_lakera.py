"""Lakera Guard adapter — POST text to Lakera Guard v2, return flagged/allowed.

On HTTP error, timeout or quota → raise GuardUnavailable so the fallback can run.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

_LAKERA_URL = "https://api.lakera.ai/v2/guard"
_TIMEOUT = 10


class GuardUnavailable(Exception):
    """Lakera returned an error or its quota is exhausted."""


class ContentFlagged(Exception):
    """Lakera flagged the text as unsafe."""


class LakeraGuardrail:
    """Primary guardrail: Lakera Guard API."""

    def __init__(self) -> None:
        self.api_key: str | None = os.environ.get("LAKERA_API_KEY")

    @staticmethod
    def _request(req: urllib.request.Request) -> dict:
        """Fire one HTTP request, return parsed JSON. Let HTTPError propagate."""
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read())

    def check(self, text: str) -> None:
        """Raise ContentFlagged if the text is flagged, GuardUnavailable on error."""
        if not self.api_key:
            raise GuardUnavailable("LAKERA_API_KEY not set")
        body = json.dumps(
            {"messages": [{"role": "user", "content": text}], "breakdown": True},
        ).encode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        req = urllib.request.Request(
            _LAKERA_URL, data=body, headers=headers, method="POST",
        )
        try:
            data = self._request(req)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                logger.warning("lakera 429, retrying in 1 s")
                time.sleep(1)
                try:
                    req = urllib.request.Request(
                        _LAKERA_URL, data=body, headers=headers, method="POST",
                    )
                    data = self._request(req)
                except urllib.error.HTTPError as exc2:
                    raise GuardUnavailable(f"lakera HTTP {exc2.code} after retry") from exc2
                except (urllib.error.URLError, TimeoutError, OSError) as exc2:
                    raise GuardUnavailable(f"lakera network: {exc2}") from exc2
            else:
                raise GuardUnavailable(f"lakera HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise GuardUnavailable(f"lakera network: {exc}") from exc

        # Block only on prompt_attack detectors; moderation/pii/links are ignored
        has_prompt_attack_detector = False
        for entry in data.get("breakdown", []):
            if entry.get("detector_type", "").startswith("prompt_attack"):
                has_prompt_attack_detector = True
                if entry.get("detected"):
                    raise ContentFlagged("lakera flagged")
        if not has_prompt_attack_detector:
            raise GuardUnavailable("lakera project has no prompt_attack detector")
