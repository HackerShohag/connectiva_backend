# Connectiva Backend

The Connectiva backend is a Flask-based application architected for serverless deployment on Vercel. It processes and predicts telecommunication infrastructure gaps, rural digital divide severity, and computes regional roadmaps based on historical data.

## Project Structure

```
backend/
├── app.py                      # Main entrypoint and API route definitions
├── data/                       # Contains master CSVs, static weights, and the compiled model (.pkl)
├── scripts/                    # Scripts for local development and ML training
│   ├── data_verifier.py        # Validates uploaded data sets
│   ├── model_trainer.py        # Handles subprocess logic for training jobs
│   └── train_model.py          # Generates the connectiva_model.pkl file
├── src/
│   ├── core/                   # Core business logic
│   │   ├── constants.py        # Static configurations and mapping dicts
│   │   ├── data_loader.py      # Loads the ML model state and static CSV files
│   │   ├── helpers.py          # Stateless utility functions
│   │   ├── indicators.py       # Computes roadmap trends and budget estimates
│   │   └── scraper.py          # Synchronous news scraping logic
│   └── utils/
│       └── file_parser.py      # Analyzes uploaded dataset files (CSV, XLSX, PDF, etc.)
├── requirements.txt            # Python dependencies
└── vercel.json                 # Vercel deployment configuration
```

## API Documentation

Below is the list of available endpoints intended for the frontend integration.

### Core Data & Analytics

- **`GET /api/summary`**  
  Returns the latest national connectivity score, the change from the previous year, and the total indicators tracked.
- **`GET /api/score`**  
  Returns a historical list of the overall connectivity score year-over-year.
- **`GET /api/indicators`**  
  Returns detailed metadata for the top 20 indicators, including their normalized latest values and historical trends.
- **`GET /api/analyze`**  
  Provides a comprehensive division-level breakdown, including BTRC mobile penetration statistics, dominant operators, NTTN fiber metrics, and individual district scores.
- **`POST /api/district-roadmap`**  
  **Payload:** `{ "district": "Dhaka", "target": 80, "timeframe": 5, "multipliers": {}, "active_year": 2025, "current_connectivity": null }`  
  Calculates the investment budget, network generation status, and generates indicator trends required to reach the specified `target` connectivity score within the `timeframe`. Includes live scraped regional news.

### Data Upload & Verification

- **`POST /api/analyze-upload`**  
  **Payload:** `multipart/form-data` with a `file` field.  
  Parses uploaded files (CSV, XLSX, PDF, JSON, DOCX) to extract dimensions and identify telecommunication variables matched against Connectiva schemas.
- **`POST /api/verify-data`**  
  **Payload:** `multipart/form-data` with a `file` field.  
  Runs the uploaded data through the `DataVerifier` pipeline to validate structural integrity, year bounds, and expected growth trends against historical data.

### Machine Learning & Model State (Local Use)

These endpoints are used to retrain the ML model locally. Because Vercel has a read-only filesystem, any training output must be committed to Git before cloud deployment.

- **`POST /api/train/start`**  
  **Payload (Optional):** `multipart/form-data` with a `file` field.  
  Triggers a background subprocess via `scripts/train_model.py` to calculate new scaling distributions and compile a new `data/connectiva_model.pkl` file. Returns a `job_id`.
- **`GET /api/train/status/<job_id>`**  
  Returns the progress (`0-100`) and completion status (`queued`, `running`, `completed`) of a local training job.
- **`POST /api/train/cancel/<job_id>`**  
  Cancels a currently active local training job.
- **`POST /api/train/reload`**  
  Hot-reloads the newly trained `.pkl` model state into the running Flask application memory without requiring a server restart.

### System Diagnostics

- **`GET /api/news-cache-status`**  
  Returns the number of cached regional news items and the timestamp of the last cache update.
- **`GET /api/data-freshness`**  
  Returns metadata on the master data source, including the latest data year and row counts.

## Vercel Deployment Notes

1. Background threading is intentionally disabled; operations like scraping are performed synchronously to prevent Vercel from killing the process mid-execution.
2. The filesystem on Vercel is read-only. Temporary files (like file uploads and the news cache) are written strictly to the ephemeral `/tmp/` directory.
3. The `.pkl` ML model file must be generated locally and committed to the repository for the production serverless functions to read it correctly.
