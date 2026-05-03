from __future__ import annotations

from functools import reduce


def get_critical_incidents(incidents):
    return list(filter(lambda incident: incident.severity == "critical", incidents))


def build_jira_payloads(incidents):
    return list(map(lambda incident: incident.to_dict(), incidents))


def count_by_team(incidents):
    return reduce(
        lambda accumulator, incident: {
            **accumulator,
            incident.assigned_team: accumulator.get(incident.assigned_team, 0) + 1,
        },
        incidents,
        {},
    )
