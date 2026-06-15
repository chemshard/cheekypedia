# Cheekypedia

A tiny Flask app that searches Wikipedia and returns only the first intro paragraph for the best matching article.

## Run it

```bash
cd cheekypedia
python -m venv .venv
.venv\Scripts\activate      # Windows PowerShell/CMD
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python app.py
```

Then open: http://127.0.0.1:5000

## Notes

- The backend uses Wikipedia OpenSearch to resolve the user's search into a likely article title.
- It then uses the Wikimedia REST summary endpoint to fetch the intro extract.
- The app keeps only the first paragraph before returning it to the frontend.
- Replace the User-Agent contact string in `app.py` before deploying publicly.
