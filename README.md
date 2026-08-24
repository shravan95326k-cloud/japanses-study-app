# Japanese Study Companion

A focused, friendly dashboard for building a consistent Japanese study habit. Log study sessions, plan today's work, track progress, and use the built-in focus timer from one simple Flask app.

## Features

- Live date, time, and time-aware greeting
- Light and dark themes saved in the browser
- Moss, Sakura, and Ocean palettes
- Samurai palette with katana, kanji, and temple-inspired background details
- Optional cat-and-dog study buddies and kanji/hiragana background
- Focus timer with 5, 25, and 50 minute presets
- Study session logging by grammar, vocabulary, kanji, or dokkai
- Daily plan checklist with completion percentage
- Study minutes, session count, score, and streak tracking
- Seven-day and 30-day activity charts with daily category insight
- SQLite persistence with a small JSON dashboard API
- Responsive layout with reduced-motion support

## Tech Stack

- Python 3.10+
- Flask 3.0
- SQLite
- HTML, CSS, and vanilla JavaScript

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/japanese-study-companion.git
cd japanese-study-companion
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

The SQLite database is created automatically on first run. Use the **Reset data** button to clear study sessions and plans.

## Deploy to Google Cloud

This project includes an App Engine Standard deployment manifest in `app.yaml`.

1. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install), sign in, and select a project:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. Enable App Engine for the project. Choose a region close to your users; this cannot be changed later:

```bash
gcloud app create --region=us-central
```

3. Deploy from the folder containing `app.yaml`:

```bash
gcloud app deploy app.yaml
gcloud app browse
```

The included `gunicorn` dependency is used by App Engine to serve Flask in production. The local SQLite file is ignored during deployment because App Engine instances have an ephemeral filesystem. For persistent data, move the database to a managed service such as Cloud SQL before using the app with real study data.

## Project Structure

```text
.
├── app.py              # Flask routes, database setup, and dashboard stats
├── app.yaml             # Google App Engine deployment configuration
├── .gcloudignore        # Files excluded from Google Cloud deployment
├── index.html          # Jinja template and page structure
├── script.js           # Timer, theme, clock, and live dashboard updates
├── style.css           # Responsive visual design and animations
├── requirements.txt    # Python dependencies
└── study_tracker.db    # Local SQLite data file created by the app
```

## API

`GET /api/dashboard` returns the current dashboard statistics as JSON. The app also exposes form endpoints for adding sessions, saving plans, toggling plans, and resetting data.

## License

This project is available for personal learning and experimentation.
