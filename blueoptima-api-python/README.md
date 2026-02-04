# BlueOptima API Python

A clean, direct API client for BlueOptima using Personal Access Tokens (PAT).

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env and add your BLUEOPTIMA_PAT
   ```

## Usage

Run the main example script:
```bash
python3 main.py
```

## Features
- Direct PAT authentication
- Automatic 10-minute JWT token lifecycle management
- Simplified API wrapper for BlueOptima endpoints
