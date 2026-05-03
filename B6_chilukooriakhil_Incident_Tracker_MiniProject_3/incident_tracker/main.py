
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List

from config import INCIDENT_DATA_FILE, LOG_LEVEL, OUTPUT_DIR
from models import (
    AppIncident,
    GeneralIncident,
    Incident,
    IncidentIterator,
    NetworkIncident,
    ReportGenerator,
    SecurityIncident,
    batch_incidents,
)
from services.azure_boards import AzureBoardsService
from services.jira import JiraService
from services.servicenow import ServiceNowService
from utils.classifier import detect_type
from utils.helpers import build_jira_payloads, count_by_team, get_critical_incidents


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-classify IT incidents and create tickets across mock enterprise platforms."
    )
    parser.add_argument(
        "--severity",
        choices=["critical", "high", "medium", "low"],
        help="Only push incidents matching the selected severity.",
    )
    parser.add_argument(
        "--data-file",
        default=str(INCIDENT_DATA_FILE),
        help="Path to the input JSON file.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="Number of incidents processed together in each batch.",
    )
    parser.add_argument(
        "--skip-json-export",
        action="store_true",
        help="Skip writing output/report.json.",
    )
    return parser.parse_args()


def load_records(data_file: Path) -> List[Dict[str, str]]:
    with data_file.open("r", encoding="utf-8") as handle:
        records = json.load(handle)
    Incident.validate_dataset(records)
    return records


def build_incident(record: Dict[str, str]) -> Incident:
    incident_text = f"{record['title']} {record['description']}"
    detected_type = detect_type(incident_text)
    incident_class = {
        "network": NetworkIncident,
        "security": SecurityIncident,
        "app": AppIncident,
        "general": GeneralIncident,
    }[detected_type]

    incident = incident_class(
        id=record["id"],
        title=record["title"],
        description=record["description"],
        reported_by=record["reported_by"],
        timestamp=record["timestamp"],
        assigned_team=record["assigned_team"],
    )
    incident.classify()
    return incident


def trigger_domain_actions(incident: Incident) -> None:
    if isinstance(incident, NetworkIncident) and incident.severity == "critical":
        logging.info(incident.escalate())
    elif isinstance(incident, SecurityIncident) and incident.severity in {"critical", "high"}:
        logging.info(incident.notify_soc())
    elif isinstance(incident, AppIncident):
        logging.debug("Stack trace preview for %s: %s", incident.id, incident.get_stack_trace())


def create_tickets(incidents: List[Incident], severity_filter: str | None, batch_size: int) -> None:
    servicenow = ServiceNowService()
    jira = JiraService()
    azure = AzureBoardsService()

    for batch_number, batch in enumerate(batch_incidents(incidents, batch_size=batch_size), start=1):
        logging.info("Processing batch %s containing %s incidents", batch_number, len(batch))
        for incident in IncidentIterator(batch, severity_filter=severity_filter):
            trigger_domain_actions(incident)
            servicenow.create_incident(incident)
            jira.create_issue(incident)
            azure.create_work_item(incident)


def print_summary(incidents: List[Incident], report_path: Path, json_path: Path | None) -> None:
    critical_incidents = get_critical_incidents(incidents)
    team_counts = count_by_team(incidents)
    payload_previews = build_jira_payloads(incidents)

    print("\nRun Summary")
    print("-" * 60)
    print(f"Processed incidents : {len(incidents)}")
    print(f"Critical incidents  : {len(critical_incidents)}")
    print(f"Payload previews    : {len(payload_previews)}")
    print(f"HTML report         : {report_path}")
    if json_path is not None:
        print(f"JSON export         : {json_path}")
    print("Counts by team      :")
    for team, count in sorted(team_counts.items()):
        print(f"  - {team}: {count}")


def main() -> int:
    configure_logging()
    args = parse_args()

    data_file = Path(args.data_file).resolve()
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be greater than zero.")

    logging.info("Loading incidents from %s", data_file)
    records = load_records(data_file)
    all_incidents = [build_incident(record) for record in records]

    # A generator expression avoids creating an intermediate list before sorting the filtered items.
    selected_incidents = sorted(
        incident
        for incident in all_incidents
        if args.severity is None or incident.severity == args.severity
    )

    if not selected_incidents:
        print("No incidents matched the supplied severity filter.")
        return 0

    create_tickets(selected_incidents, args.severity, args.batch_size)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_generator = ReportGenerator(selected_incidents, OUTPUT_DIR)
    report_filename = "report.html" if args.severity is None else f"report_{args.severity}.html"
    json_filename = "report.json" if args.severity is None else f"report_{args.severity}.json"
    report_path = report_generator.generate_html(report_filename)
    json_path = None if args.skip_json_export else report_generator.export_json(json_filename)

    print_summary(selected_incidents, report_path, json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
