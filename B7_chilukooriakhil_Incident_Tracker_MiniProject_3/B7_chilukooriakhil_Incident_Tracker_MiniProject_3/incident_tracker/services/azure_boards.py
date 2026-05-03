from __future__ import annotations

import base64
import json
import logging
from itertools import count
from typing import Any, Dict, List

from config import AZURE_BOARDS_CONFIG, MOCK_API, REQUEST_TIMEOUT
from utils.decorators import log_call, retry


class AzureBoardsService:
    _mock_counter = count(1)

    def __init__(self) -> None:
        self.base_url = (
            "https://dev.azure.com/"
            f"{AZURE_BOARDS_CONFIG['organization']}/{AZURE_BOARDS_CONFIG['project']}"
            "/_apis/wit/workitems/$Bug?api-version=7.1"
        )

    @staticmethod
    def _priority_from_severity(severity: str | None) -> int:
        return {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(severity or "low", 4)

    def _build_payload(self, incident) -> List[Dict[str, Any]]:
        return [
            {"op": "add", "path": "/fields/System.Title", "value": incident.title},
            {
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": self._priority_from_severity(incident.severity),
            },
            {"op": "add", "path": "/fields/System.AssignedTo", "value": incident.assigned_team},
            {"op": "add", "path": "/fields/System.Description", "value": incident.description},
        ]

    def _headers(self) -> Dict[str, str]:
        raw_token = f":{AZURE_BOARDS_CONFIG['pat']}".encode("utf-8")
        encoded = base64.b64encode(raw_token).decode("ascii")
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json-patch+json",
            "Accept": "application/json",
        }

    @retry(times=3)
    @log_call
    def create_work_item(self, incident) -> str:
        payload = self._build_payload(incident)

        if MOCK_API:
            logging.info("Azure Boards mock payload:\n%s", json.dumps(payload, indent=2))
            work_item_id = f"MOCK-AZURE-{next(self._mock_counter):03d}"
            incident.ticket_ids["azure"] = work_item_id
            return work_item_id

        import requests

        response = requests.post(
            self.base_url,
            headers=self._headers(),
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        work_item_id = str(response.json()["id"])
        incident.ticket_ids["azure"] = work_item_id
        return work_item_id
