from __future__ import annotations

import json
import logging
from itertools import count
from typing import Any, Dict

from config import MOCK_API, REQUEST_TIMEOUT, SERVICENOW_CONFIG
from utils.decorators import log_call, retry


class ServiceNowService:
    _mock_counter = count(1)

    def __init__(self) -> None:
        self.base_url = (
            f"https://{SERVICENOW_CONFIG['instance']}.service-now.com/api/now/table/incident"
        )

    @staticmethod
    def _urgency_from_severity(severity: str | None) -> int:
        return {"critical": 1, "high": 1, "medium": 2, "low": 3}.get(severity or "low", 3)

    def _build_payload(self, incident) -> Dict[str, Any]:
        return {
            "short_description": incident.title,
            "description": incident.description,
            "urgency": self._urgency_from_severity(incident.severity),
            "category": incident.incident_type,
            "assignment_group": incident.assigned_team,
        }

    @retry(times=3)
    @log_call
    def create_incident(self, incident) -> str:
        payload = self._build_payload(incident)

        if MOCK_API:
            logging.info("ServiceNow mock payload:\n%s", json.dumps(payload, indent=2))
            ticket_id = f"MOCK-SNOW-{next(self._mock_counter):03d}"
            incident.ticket_ids["snow"] = ticket_id
            return ticket_id

        import requests

        response = requests.post(
            self.base_url,
            auth=(SERVICENOW_CONFIG["username"], SERVICENOW_CONFIG["password"]),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        ticket_id = response.json()["result"]["sys_id"]
        incident.ticket_ids["snow"] = ticket_id
        return ticket_id

    @retry(times=3)
    @log_call
    def update_status(self, ticket_id: str, status: str) -> bool:
        payload = {"state": status}

        if MOCK_API:
            logging.info(
                "ServiceNow mock status update for %s:\n%s", ticket_id, json.dumps(payload, indent=2)
            )
            return True

        import requests

        response = requests.patch(
            f"{self.base_url}/{ticket_id}",
            auth=(SERVICENOW_CONFIG["username"], SERVICENOW_CONFIG["password"]),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return True
