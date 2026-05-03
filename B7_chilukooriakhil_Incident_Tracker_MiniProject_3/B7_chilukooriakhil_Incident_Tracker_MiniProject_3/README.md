# IT Incident Auto-Triage & Tracker

This project implements Mini Project 3 as a Python command-line application that:

- loads raw incidents from JSON
- classifies each incident by type and severity using regex
- creates mock tickets in ServiceNow, Jira, and Azure Boards
- generates HTML and JSON reports under `incident_tracker/output/`

## Project Layout

```text
B7_VamshiKrishna_Incident_Tracker_MiniProject_3/
├── .vscode/launch.json
├── README.md
├── requirements.txt
└── incident_tracker/
    ├── config.py
    ├── main.py
    ├── data/incidents.json
    ├── models/
    ├── output/
    ├── services/
    └── utils/
```

## How To Run In VS Code

1. Open the folder `B7_VamshiKrishna_Incident_Tracker_MiniProject_3` in VS Code.
2. Open the integrated terminal.
3. Run:

```powershell
cd incident_tracker
python main.py
```

To process only one severity:

```powershell
cd incident_tracker
python main.py --severity critical
```

## Mock Mode

`MOCK_API` is enabled by default in `incident_tracker/config.py`, so the project runs without live credentials. In mock mode, each service prints the payload and returns a fake ticket ID.

## Optional Live API Setup

If you want to switch to live API mode later:

1. Install optional dependency:

```powershell
pip install -r requirements.txt
```

2. Set environment variables or update `incident_tracker/config.py`.
3. Set `INCIDENT_TRACKER_MOCK_API=false`.

## Output Files

Successful execution generates:

- `incident_tracker/output/report.html`
- `incident_tracker/output/report.json`

If `--severity` is used, the filtered run is written to:

- `incident_tracker/output/report_<severity>.html`
- `incident_tracker/output/report_<severity>.json`

## Notes

- The sample dataset contains 12 incidents as required.
- The implementation includes the stretch goal `--severity` CLI flag.
- The base `Incident` class also includes JSON schema validation before loading.
