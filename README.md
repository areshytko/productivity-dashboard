# Personal Productivity Dashboard

`Streamlit` dashboard that fetches the [Pomodoro](https://en.wikipedia.org/wiki/Pomodoro_Technique) data from
Google Sheets and builds red-yellow-green KPIs, suggested actions and historical stats.

## Runbook

Prerequisites:
- Python 3.9

Steps:

1. Create virtual env:
```
python -m venv .venv
source .venv/bin/activate
```
2. Install third-party dependencies:
```
pip install -r requirements.txt
```

3. Configure google sheets ids and ranges:

Edit `dashboard/config.py` file.

4. Run the application:
```
streamlit run app.py ./configs/default.yaml
```

## Google Sheets tables expected schema

#### Activities Catalog Sheet
*See the schema in [load.py](dashboard/load.py)*
- Activity
- Parent
- Tags
- Active
- Comment

#### Pomodoros Sheet
*See the schema in [load.py](dashboard/load.py)*
- Week
- Date
- Activity
- Comment
- Pomodoros
- Planned
- Weekly Done KPI

## Changing App credentials

If you want to change App credentials in `credentials.json`, please
follow instructions in [Google Sheets API Python Quickstart](https://developers.google.com/sheets/api/quickstart/python).

Basically, you need to:
- create a Project
- enable Google Sheets API in it
- create Desktop Application Credentials
