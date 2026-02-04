# NatWest BlueOptima Data Extraction (Python)

Standalone script to authenticate and extract developer data from BlueOptima APIs.

## Prerequisites

- Python 3.8+
- [Optional] Virtual environment

## Setup

1. (Optional) Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   ./venv/bin/pip install -r requirements.txt
   ```

3. Install Playwright browser:
   ```bash
   ./venv/bin/playwright install chromium
   ```

## Running Data Extraction

To run the extraction:

```bash
export PYTHONPATH=$PYTHONPATH:.
LOGIN_USERNAME="your-email@example.com" ./venv/bin/python3 run_login.py
```

- JSON responses will be saved in the `data/` directory with timestamps.
- Use `DEMO=true` (default) to keep the browser open. Set `DEMO=false` for non-interactive execution.
