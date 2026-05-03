from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from models.incident import Incident
from utils.helpers import count_by_team, get_critical_incidents


class ReportGenerator:
    def __init__(self, incidents: Iterable[Incident], output_dir: Path) -> None:
        self.incidents: List[Incident] = list(incidents)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html(self, filename: str = "report.html") -> Path:
        team_counts = count_by_team(self.incidents)
        critical_count = len(get_critical_incidents(self.incidents))

        # Generator expression keeps memory usage small by avoiding a second list of rows.
        rows_html = "\n".join(self._render_row(incident) for incident in self.incidents)
        team_html = "".join(
            f"<li><strong>{html.escape(team)}</strong>: {count}</li>"
            for team, count in sorted(team_counts.items())
        )

        document = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IT Incident Auto-Triage Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f7fb;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #62708a;
      --line: #d7dfec;
      --accent: #0057b8;
      --critical: #b42318;
      --high: #dd6b20;
      --medium: #b7791f;
      --low: #2b6cb0;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top right, rgba(0, 87, 184, 0.12), transparent 24rem),
        linear-gradient(180deg, #f7faff 0%, var(--bg) 100%);
    }}
    .container {{
      width: min(1200px, calc(100% - 2rem));
      margin: 2rem auto;
    }}
    .hero {{
      background: linear-gradient(135deg, #0b2447 0%, #0057b8 100%);
      color: white;
      border-radius: 20px;
      padding: 2rem;
      box-shadow: 0 18px 40px rgba(11, 36, 71, 0.2);
    }}
    .hero h1 {{
      margin: 0 0 0.5rem;
      font-size: clamp(1.8rem, 3vw, 2.7rem);
    }}
    .hero p {{
      margin: 0.4rem 0;
      color: rgba(255, 255, 255, 0.9);
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin: 1.5rem 0;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 1rem 1.1rem;
      box-shadow: 0 10px 24px rgba(23, 32, 51, 0.06);
    }}
    .card h2 {{
      margin: 0;
      font-size: 0.95rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .card p {{
      margin: 0.6rem 0 0;
      font-size: 1.8rem;
      font-weight: 700;
    }}
    .section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 1.2rem;
      box-shadow: 0 10px 24px rgba(23, 32, 51, 0.06);
      margin-bottom: 1.5rem;
    }}
    .section h2 {{
      margin-top: 0;
    }}
    ul {{
      margin: 0;
      padding-left: 1.2rem;
    }}
    .table-wrap {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
    }}
    th, td {{
      padding: 0.9rem 0.75rem;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #edf3ff;
      font-size: 0.9rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
    }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      color: white;
      font-size: 0.82rem;
      font-weight: 700;
      text-transform: capitalize;
    }}
    .critical {{
      background: var(--critical);
    }}
    .high {{
      background: var(--high);
    }}
    .medium {{
      background: var(--medium);
    }}
    .low {{
      background: var(--low);
    }}
    .muted {{
      color: var(--muted);
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <section class="hero">
      <h1>IT Incident Auto-Triage & Tracker</h1>
      <p>Generated on {datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")}</p>
      <p>Mock integration summary for ServiceNow, Jira, and Azure Boards.</p>
    </section>

    <section class="cards">
      <div class="card">
        <h2>Total Incidents</h2>
        <p>{len(self.incidents)}</p>
      </div>
      <div class="card">
        <h2>Critical Incidents</h2>
        <p>{critical_count}</p>
      </div>
      <div class="card">
        <h2>Teams Covered</h2>
        <p>{len(team_counts)}</p>
      </div>
    </section>

    <section class="section">
      <h2>Incidents By Team</h2>
      <ul>{team_html}</ul>
    </section>

    <section class="section">
      <h2>Processed Incidents</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Type</th>
              <th>Severity</th>
              <th>Assigned Team</th>
              <th>Reported By</th>
              <th>Timestamp</th>
              <th>ServiceNow</th>
              <th>Jira</th>
              <th>Azure Boards</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </div>
    </section>
  </div>
</body>
</html>
"""

        target = self.output_dir / filename
        target.write_text(document, encoding="utf-8")
        return target

    def export_json(self, filename: str = "report.json") -> Path:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_incidents": len(self.incidents),
            "critical_incidents": len(get_critical_incidents(self.incidents)),
            "counts_by_team": count_by_team(self.incidents),
            "incidents": [incident.to_dict() for incident in self.incidents],
        }

        target = self.output_dir / filename
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return target

    def _render_row(self, incident: Incident) -> str:
        safe = html.escape
        severity = incident.severity or "low"
        return f"""<tr>
  <td>{safe(incident.id)}</td>
  <td>
    <strong>{safe(incident.title)}</strong>
    <div class="muted">{safe(incident.description)}</div>
  </td>
  <td>{safe(incident.incident_type.title())}</td>
  <td><span class="badge {safe(severity)}">{safe(severity)}</span></td>
  <td>{safe(incident.assigned_team)}</td>
  <td>{safe(incident.reported_by)}</td>
  <td>{safe(incident.timestamp.isoformat())}</td>
  <td>{safe(str(incident.ticket_ids.get("snow", "-")))}</td>
  <td>{safe(str(incident.ticket_ids.get("jira", "-")))}</td>
  <td>{safe(str(incident.ticket_ids.get("azure", "-")))}</td>
</tr>"""
