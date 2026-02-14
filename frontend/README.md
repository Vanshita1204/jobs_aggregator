Frontend pages for the Jobs Aggregator API

This folder contains a tiny, framework-free frontend (HTML + vanilla JS) to exercise the API endpoints in `app`.

How to run
- Option A: Serve static files with Python (recommended for quick testing):
  1. From project root run the React dev server (recommended):
    ```bash
    cd frontend/react-app
    npm install
    npm run dev
    ```
    The dev server runs on http://localhost:3000 by default.
  2. Alternatively you can still serve the static `frontend/` pages with Python's http.server as a quick fallback:
    ```bash
    cd frontend
    python -m http.server 3000
    ```
  3. Open the dev URL in your browser.

- Option B: Use any static file server or copy files into an existing frontend.

Notes
- The frontend stores the Bearer token in localStorage after login and sends it in the `Authorization` header for protected requests.
- Edit `frontend/js/api.js` if your API is hosted at a different base URL (default: `/api/v1`).
