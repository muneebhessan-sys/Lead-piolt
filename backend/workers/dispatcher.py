from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from workers.gmail import send_gmail_safe


class CampaignDispatcher:
    """Dispatches campaign items with retry/backoff, and supports pause/resume/stop lifecycle."""

    _STATUSES = {"PENDING", "RUNNING", "PAUSED", "STOPPED", "COMPLETED", "FAILED"}
    _ACTIONS = {"pause", "resume", "stop"}

    def __init__(self) -> None:
        self._campaigns: dict[int, dict[str, Any]] = {}

    def register_campaign(
        self,
        campaign_id: int,
        name: str,
        sender_account: str,
        channel: str = "EMAIL",
    ) -> dict[str, Any]:
        """Register a new campaign in PENDING status and return its state."""
        self._campaigns[campaign_id] = {
            "id": campaign_id,
            "name": name,
            "channel": channel,
            "sender_account": sender_account,
            "status": "PENDING",
            "started_at": None,
            "completed_at": None,
            "paused_at": None,
            "error": "",
        }
        return self._campaigns[campaign_id]

    def get_campaign(self, campaign_id: int) -> dict[str, Any] | None:
        """Retrieve campaign state by ID."""
        return self._campaigns.get(campaign_id)

    def list_campaigns(self) -> list[dict[str, Any]]:
        """Return a list of all registered campaign states."""
        return list(self._campaigns.values())

    def dispatch(
        self,
        campaign_id: int,
        items: list[dict[str, Any]],
        max_concurrent: int = 5,
    ) -> dict[str, Any]:
        """Dispatch all items for a campaign, respecting pause/stop signals during iteration."""
        campaign = self._require_active(campaign_id)
        if campaign["status"] in {"STOPPED", "COMPLETED", "FAILED"}:
            raise ValueError(f"Cannot dispatch campaign in status {campaign['status']}")
        campaign["status"] = "RUNNING"
        campaign["started_at"] = datetime.now(timezone.utc).isoformat()
        campaign["paused_at"] = None
        campaign["error"] = ""
        results: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        try:
            for item in items:
                if campaign["status"] == "PAUSED":
                    break
                if campaign["status"] == "STOPPED":
                    break
                result = self._send_item_with_retry(campaign, item)
                if result.get("success"):
                    results.append(result)
                else:
                    failures.append(result)
            if campaign["status"] == "STOPPED":
                campaign["status"] = "STOPPED"
            elif campaign["status"] == "PAUSED":
                campaign["status"] = "PAUSED"
            else:
                campaign["status"] = "COMPLETED"
        except Exception as exc:
            campaign["status"] = "FAILED"
            campaign["error"] = str(exc)
        finally:
            campaign["completed_at"] = datetime.now(timezone.utc).isoformat()
        campaign["results"] = results
        campaign["failures"] = failures
        return {
            "campaign_id": campaign_id,
            "status": campaign["status"],
            "sent": len(results),
            "failed": len(failures),
            "results": results,
            "failures": failures,
        }

    def pause(self, campaign_id: int) -> dict[str, Any]:
        """Pause a running campaign; subsequent dispatches stop at the next item boundary."""
        campaign = self._require_active(campaign_id)
        if campaign["status"] != "RUNNING":
            raise ValueError(f"Cannot pause campaign in status {campaign['status']}")
        campaign["status"] = "PAUSED"
        campaign["paused_at"] = datetime.now(timezone.utc).isoformat()
        return {"campaign_id": campaign_id, "status": campaign["status"]}

    def resume(self, campaign_id: int) -> dict[str, Any]:
        """Resume a paused campaign back to RUNNING status."""
        campaign = self._require_active(campaign_id)
        if campaign["status"] != "PAUSED":
            raise ValueError(f"Cannot resume campaign in status {campaign['status']}")
        campaign["status"] = "RUNNING"
        campaign["paused_at"] = None
        return {"campaign_id": campaign_id, "status": campaign["status"]}

    def stop(self, campaign_id: int) -> dict[str, Any]:
        """Stop a campaign immediately; in-flight items finish but no new items are processed."""
        campaign = self._require_active(campaign_id)
        if campaign["status"] in {"COMPLETED", "STOPPED", "FAILED"}:
            raise ValueError(f"Cannot stop campaign in status {campaign['status']}")
        campaign["status"] = "STOPPED"
        campaign["completed_at"] = datetime.now(timezone.utc).isoformat()
        return {"campaign_id": campaign_id, "status": campaign["status"]}

    def _require_active(self, campaign_id: int) -> dict[str, Any]:
        """Return the campaign state or raise if not found."""
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign not found: {campaign_id}")
        return campaign

    def _send_item_with_retry(
        self,
        campaign: dict[str, Any],
        item: dict[str, Any],
        max_retries: int = 3,
        backoff_factor: float = 2.0,
    ) -> dict[str, Any]:
        """Send a single item with exponential backoff retry on failure."""
        last_error = ""
        for attempt in range(1, max_retries + 1):
            try:
                result = self._send_item(campaign, item)
                if result.get("success"):
                    return result
                last_error = result.get("error", "Unknown send failure")
            except Exception as exc:
                last_error = str(exc)
            if attempt < max_retries:
                wait = backoff_factor ** attempt
                time.sleep(min(wait, 60.0))
        return {"success": False, "error": last_error, "item": item, "retries": max_retries}

    def _send_item(self, campaign: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
        """Route a single item to its channel handler and return the result."""
        channel = campaign.get("channel", "EMAIL").upper()
        if channel == "EMAIL":
            recipient = item.get("recipient", "")
            subject = item.get("subject", "")
            content = item.get("content", "")
            return send_gmail_safe(campaign["sender_account"], recipient, subject, content)
        return {"success": False, "error": f"Unsupported channel: {channel}", "item": item}
