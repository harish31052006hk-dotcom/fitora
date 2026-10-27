# Fitora — Refinement and Deployment Guide

This revision concentrates on the conversation experience, concise AI responses, contextual AI actions, and a saved weekly plan. It deliberately omits `.env`, database files, logs and Python bytecode from the archive.

## What's changed

- The assistant transcript lives in a bounded scrolling pane; long conversations should not keep stretching the page. Responses render as readable paragraphs, headings and proper lists, and the current reader position is respected.
- Ordinary assistant responses are instructed to answer first and stay concise, specific, and non-judgmental. The assistant receives verified diary/profile context when applicable and must distinguish logged facts from estimates.
- The assistant no longer substitutes a loosely related FAQ for a general nutrition question when the AI provider fails.
- A new `/plan/` page saves one weekly plan per signed-in user and current Monday-starting week. Preferences cover goal, food style, budget, preparation time, training days and foods to avoid. The plan uses current profile targets and recent diary records when available.
- If AI plan generation fails, a starter plan is shown and clearly labelled as a template, not as AI-generated.
- Dashboard, diary, progress and weekly-plan pages have context-specific links into AI. The floating AI widget is hidden on the dedicated assistant page to avoid duplicate controls.
- Weekly plan days collapse by default (Monday opens first) to make the page easier to scan.

## Local setup

1. Extract this ZIP into your intended project folder.
2. Copy `.env.example` to `.env` locally and add a fresh API key if needed:

   ```powershell
   Copy-Item .env.example .env
   ```

3. Create and activate the environment, then install requirements:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. Migrate and run:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

5. Visit `http://127.0.0.1:8000/`. Run `python manage.py test` to test the app.

## Production configuration

Configure production values in **Render → Fitora service → Environment**. Local `.env` changes are not sent to Render by Git. The current Groq settings use:

```dotenv
AI_API_URL=https://api.groq.com/openai/v1/chat/completions
AI_MODEL=qwen/qwen3.8-27b
AI_API_TIMEOUT=35
```

Set `AI_API_KEY` to a newly generated key. Revoke any key previously shared in a chat or committed to a repository. Keep `DEBUG=False` in production, use a secure Django `SECRET_KEY`, and leave `MONGODB_URI` blank if the optional logging integration is not needed. `NUTRITION_API_KEY` may remain blank for the current Open Food Facts flow.

## Push and deploy

From the repository root (the directory containing `manage.py`):

```powershell
git status
git add .
git commit -m "Refine Fitora AI and add weekly plans"
git push
```

Before committing, confirm `.env` does not appear in `git status`. Render's build configuration runs migrations so the new `plans` table is created. If automatic deployment is disabled, manually deploy the latest commit in Render.

## Validation status

Python modules compile and the chat JavaScript passes `node --check`. The full Django suite and live AI calls were not run here because Django was unavailable and package downloads could not reach the package index. Please run `python manage.py test` and test the assistant and `/plan/` on the deployed service before considering the revision production-verified.
