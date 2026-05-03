from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Iterable, Iterator, List, Optional

from utils.classifier import (
    APP_PATTERN,
    ERROR_CODE_PATTERN,
    EXCEPTION_PATTERN,
    HOST_PATTERN,
    HTTP_STATUS_PATTERN,
    IP_PATTERN,
    NETWORK_PATTERN,
    PROTOCOL_PATTERN,
    SECURITY_PATTERN,
    SERVICE_NAME_PATTERN,
    THREAT_PATTERN,
    detect_severity,
)


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class Incident:
    required_fields = {"id", "title", "description", "reported_by", "timestamp", "assigned_team"}
    incident_type = "general"

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        reported_by: str,
        timestamp: str,
        assigned_team: str,
    ) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.reported_by = reported_by
        self.timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        self.assigned_team = assigned_team
        self._severity: Optional[str] = None
        self.ticket_ids: Dict[str, Any] = {}

    @property
    def severity(self) -> Optional[str]:
        return self._severity

    @property
    def combined_text(self) -> str:
        return f"{self.title} {self.description}"

    def classify(self) -> str:
        raise NotImplementedError("Subclasses must implement classify()")

    def extra_details(self) -> Dict[str, Any]:
        return {}

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "reported_by": self.reported_by,
            "timestamp": self.timestamp.isoformat(),
            "assigned_team": self.assigned_team,
            "type": self.incident_type,
            "severity": self.severity,
            "ticket_ids": self.ticket_ids,
        }
        payload.update(self.extra_details())
        return payload

    def __str__(self) -> str:
        return f"{self.id} [{self.severity or 'unclassified'}] {self.title}"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id!r}, severity={self.severity!r}, "
            f"assigned_team={self.assigned_team!r})"
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Incident):
            return NotImplemented

        self_rank = SEVERITY_ORDER.get(self.severity or "low", 3)
        other_rank = SEVERITY_ORDER.get(other.severity or "low", 3)
        return (self_rank, self.timestamp, self.id) < (other_rank, other.timestamp, other.id)

    @staticmethod
    def validate_record(record: Dict[str, Any]) -> None:
        missing = Incident.required_fields.difference(record.keys())
        if missing:
            raise ValueError(f"Incident record is missing required fields: {sorted(missing)}")

        for field in Incident.required_fields:
            if not isinstance(record[field], str) or not record[field].strip():
                raise ValueError(f"Incident field {field!r} must be a non-empty string.")

        datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))

    @staticmethod
    def validate_dataset(records: List[Dict[str, Any]]) -> None:
        if not isinstance(records, list):
            raise ValueError("The incident JSON file must contain a top-level list of incident records.")

        for record in records:
            Incident.validate_record(record)


class NetworkIncident(Incident):
    incident_type = "network"

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        reported_by: str,
        timestamp: str,
        assigned_team: str,
        affected_host: Optional[str] = None,
        protocol: Optional[str] = None,
    ) -> None:
        super().__init__(id, title, description, reported_by, timestamp, assigned_team)
        self.affected_host = affected_host
        self.protocol = protocol

    def classify(self) -> str:
        match = IP_PATTERN.search(self.combined_text) or HOST_PATTERN.search(self.combined_text)
        protocol_match = PROTOCOL_PATTERN.search(self.combined_text) or NETWORK_PATTERN.search(self.combined_text)

        if match:
            self.affected_host = match.group(0)
        if protocol_match:
            self.protocol = protocol_match.group(0).upper()

        self._severity = detect_severity(self.combined_text)
        return self.incident_type

    def escalate(self) -> str:
        return f"Paging on-call network team for {self.id} ({self.title})"

    def extra_details(self) -> Dict[str, Any]:
        return {"affected_host": self.affected_host, "protocol": self.protocol}


class AppIncident(Incident):
    incident_type = "app"

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        reported_by: str,
        timestamp: str,
        assigned_team: str,
        app_name: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(id, title, description, reported_by, timestamp, assigned_team)
        self.app_name = app_name
        self.error_code = error_code

    def classify(self) -> str:
        app_match = SERVICE_NAME_PATTERN.search(self.combined_text)
        error_match = (
            HTTP_STATUS_PATTERN.search(self.combined_text)
            or EXCEPTION_PATTERN.search(self.combined_text)
            or ERROR_CODE_PATTERN.search(self.combined_text)
            or APP_PATTERN.search(self.combined_text)
        )

        if app_match:
            self.app_name = app_match.group(1)
        if error_match:
            self.error_code = error_match.group(0)

        self._severity = detect_severity(self.combined_text)
        return self.incident_type

    def get_stack_trace(self) -> str:
        cleaned = re.sub(r"\s+", " ", self.description).strip()
        return cleaned[:140]

    def extra_details(self) -> Dict[str, Any]:
        return {"app_name": self.app_name, "error_code": self.error_code}


class SecurityIncident(Incident):
    incident_type = "security"

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        reported_by: str,
        timestamp: str,
        assigned_team: str,
        threat_type: Optional[str] = None,
        source_ip: Optional[str] = None,
    ) -> None:
        super().__init__(id, title, description, reported_by, timestamp, assigned_team)
        self.threat_type = threat_type
        self.source_ip = source_ip

    def classify(self) -> str:
        threat_match = THREAT_PATTERN.search(self.combined_text) or SECURITY_PATTERN.search(self.combined_text)
        source_match = IP_PATTERN.search(self.combined_text)

        if threat_match:
            self.threat_type = threat_match.group(0).lower()
        if source_match:
            self.source_ip = source_match.group(0)

        self._severity = detect_severity(self.combined_text)
        return self.incident_type

    def notify_soc(self) -> str:
        return f"Sending SOC alert for {self.id} ({self.threat_type or 'security event'})"

    def extra_details(self) -> Dict[str, Any]:
        return {"threat_type": self.threat_type, "source_ip": self.source_ip}


class GeneralIncident(Incident):
    incident_type = "general"

    def classify(self) -> str:
        self._severity = detect_severity(self.combined_text)
        return self.incident_type


class IncidentIterator(Iterator[Incident]):
    def __init__(self, incidents: Iterable[Incident], severity_filter: Optional[str] = None) -> None:
        self._incidents = list(incidents)
        self._severity_filter = severity_filter
        self._index = 0

    def __iter__(self) -> "IncidentIterator":
        return self

    def __next__(self) -> Incident:
        while self._index < len(self._incidents):
            incident = self._incidents[self._index]
            self._index += 1
            if self._severity_filter and incident.severity != self._severity_filter:
                continue
            return incident
        raise StopIteration


def batch_incidents(incidents: List[Incident], batch_size: int = 3):
    """Yield incidents in batches of batch_size."""
    for index in range(0, len(incidents), batch_size):
        yield incidents[index : index + batch_size]
