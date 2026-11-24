# Al-Powered-Intelligent-Sales-Forecasting-Platform

AI-powered sales forecasting, lead management, and company intelligence.

## Project structure

- `app/`: FastAPI backend package
  - `routers/`: lead and company-analysis endpoints
  - `services/`: AI analysis service
- `frontend/`: Streamlit dashboard
- `static/`: project diagrams

## Run locally

Install dependencies with `pip install -r requirements.txt`, then configure
`DATABASE_URL` in `.env`.

Start the API:

```powershell
uvicorn app.main:app --reload
```

Start the dashboard in another terminal:

```powershell
streamlit run frontend/app.py
```

The previous root entrypoints remain supported: `uvicorn main:app --reload`
and `streamlit run app.py`.
