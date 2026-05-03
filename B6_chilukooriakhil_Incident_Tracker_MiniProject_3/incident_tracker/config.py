from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
INCIDENT_DATA_FILE = DATA_DIR / "incidents.json"
REQUEST_TIMEOUT = int(os.getenv("INCIDENT_TRACKER_REQUEST_TIMEOUT", "15"))
LOG_LEVEL = os.getenv("INCIDENT_TRACKER_LOG_LEVEL", "INFO").upper()


def _env_flag(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


MOCK_API = _env_flag("INCIDENT_TRACKER_MOCK_API", True)


SERVICENOW_CONFIG = {
    "instance": os.getenv("SERVICENOW_INSTANCE", "demo-instance"),
    "username": os.getenv("SERVICENOW_USERNAME", "demo.user"),
    "password": os.getenv("SERVICENOW_PASSWORD", "demo-password"),
}

JIRA_CONFIG = {
    "domain": os.getenv("JIRA_DOMAIN", "example-domain"),
    "email": os.getenv("JIRA_EMAIL", "demo@example.com"),
    "api_token": os.getenv("JIRA_API_TOKEN", "demo-token"),
    "project_key": os.getenv("JIRA_PROJECT_KEY", "PROJ"),
}

AZURE_BOARDS_CONFIG = {
    "organization": os.getenv("AZURE_ORG", "demo-org"),
    "project": os.getenv("AZURE_PROJECT", "demo-project"),
    "pat": os.getenv("AZURE_PAT", "demo-pat"),
}
