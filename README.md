# Backtrack

A version-history API for web pages. This repo has been reorganized into a Python package layout so the application code lives under `app/` and runtime data/config live outside the source tree.

## Repository layout

```text
Backtrack/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── watcher.py
│   ├── store.py
│   ├── diff.py
│   └── ...
├── config/
│   └── pages.json
├── data/
│   └── screenshots/
├── scripts/
│   └── demo_seed.py
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
├── demo_seed.py
├── main.py
└── ...
```

## Run it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
.venv/bin/uvicorn app.main:app --reload
```

## Demo

```bash
.venv/bin/python scripts/demo_seed.py
.venv/bin/uvicorn app.main:app --reload
```

## Notes

- `config/pages.json` contains the watched pages.
- `data/` stores generated SQLite data and screenshots.
- The lightweight wrapper files at the repo root remain for compatibility, but the real application source now lives under `app/`.
