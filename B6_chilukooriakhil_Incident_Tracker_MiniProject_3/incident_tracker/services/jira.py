from __future__ import annotations

import base64
import json
import logging
from itertools import count
from typing import Any, Dict

from config import JIRA_CONFIG, MOCK_API, REQUEST_TIMEOUT
from utils.decorators import log_call, retry


class JiraService:
    _mock_counter = count(1)

    def __init__(self) -> None:
        self.base_url = f"https://{JIRA_CONFIG['domain']}.atlassian.net/rest/api/3/issue"

    @staticmethod
    def _priority_from_severity(severity: str | None) -> str:
        return {
            "critical": "Highest",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
        }.get(severity or "low", "Low")

    def _build_payload(self, incident) -> Dict[str, Any]:
        labels = [
            incident.incident_type,
            incident.severity or "low",
            incident.assigned_team.lower().replace(" ", "-"),
        ]
        return {
            "fields": {
                "project": {"key": JIRA_CONFIG["project_key"]},
                "summary": incident.title,
                "description": incident.description,
                "issuetype": {"name": "Bug"},
                "priority": {"name": self._priority_from_severity(incident.severity)},
                "labels": labels,
            }
        }

    def _headers(self) -> Dict[str, str]:
        token = f"{JIRA_CONFIG['email']}:{JIRA_CONFIG['api_token']}".encode("utf-8")
        bearer = base64.b64encode(token).decode("ascii")
        return {
            "Authorization": f"Bearer {bearer}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @retry(times=3)
    @log_call
    def create_issue(self, incident) -> str:
        payload = self._build_payload(incident)

        if MOCK_API:
            logging.info("Jira mock payload:\n%s", json.dumps(payload, indent=2))
            ticket_key = f"MOCK-JIRA-{next(self._mock_counter):03d}"
            incident.ticket_ids["jira"] = ticket_key
            return ticket_key

        import requests

        response = requests.post(
            self.base_url,
            headers=self._headers(),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        ticket_key = response.json()["key"]
        incident.ticket_ids["jira"] = ticket_key
        return ticket_key

    @retry(times=3)
    @log_call
    def update_priority(self, ticket_key: str, priority: str) -> bool:
        payload = {"fields": {"priority": {"name": priority}}}

        if MOCK_API:
            logging.info("Jira mock update for %s:\n%s", ticket_key, json.dumps(payload, indent=2))
            return True

        import requests

        response = requests.put(
            f"{self.base_url}/{ticket_key}",
            headers=self._headers(),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return True
