# NatWest BlueOptima Data Extraction (Node.js)

Standalone TypeScript script to authenticate and extract developer data from BlueOptima APIs.

## Prerequisites

- Node.js (Latest LTS recommended)
- npm or yarn

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Install Playwright browser:
   ```bash
   npx playwright install chromium
   ```

## Running Data Extraction

To run the extraction:

```bash
LOGIN_USERNAME="your-email@example.com" npm start
```

- JSON responses will be saved in the `data/` directory with timestamps.
- Use `DEMO=true` (default) to keep the browser open. Set `DEMO=false` for non-interactive execution.
