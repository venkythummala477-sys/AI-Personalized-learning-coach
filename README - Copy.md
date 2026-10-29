
# AI Personalized Learning Coach

A personalized learning application built with Python, Streamlit, Gemini AI, and SQLite.

## Features
- Generate day-wise study plans
- Generate five-question multiple-choice quizzes
- Evaluate quiz answers with Python
- Identify weak topics
- Generate revision suggestions
- Store learning plans and quiz history in SQLite

## Installation

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Install packages:

```powershell
python -m pip install -r requirements.txt
```

Configure your Gemini API key in `.env`.

Run the app:

```powershell
streamlit run app.py
```

Test Gemini:

```powershell
python test_gemini.py
```

Do not upload `.env` or your API key to GitHub.
