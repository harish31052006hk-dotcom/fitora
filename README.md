# Fitora

Fitora is a Django-based nutrition and habit-tracking web app with a context-aware AI coach. Its core workflows are food logging, recorded progress, personal targets, and weekly planning. The interface uses a restrained royal-blue and warm-cream palette with responsive glass surfaces.

## Product features

- User accounts and protected wellness pages.
- Food diary with meal categories, calorie and macro totals, saved meals, and recipes.
- Weight logging and recorded progress summaries.
- AI assistant for text questions and food/fitness images using the configured provider.
- Contextual AI actions from the dashboard, diary, progress page, and weekly plan.
- Saved seven-day meal and movement plans based on profile targets, selected preferences, and recent recorded diary entries.
- FAQ, troubleshooting, and support tickets.
- PostgreSQL in production, local SQLite fallback, optional MongoDB Atlas logging.

### Product behaviour

- An unlogged day does not mean no food was eaten.
- Planned meals are suggestions; the app does not automatically log them as consumed.
- Meal calories, protein, and other nutrition figures are estimates, not medical advice.
- The weekly plan labels AI-generated content separately from a starter-template fallback.
- API keys and Django secrets belong in environment variables, not source control.

## Local setup (PowerShell)

1. Extract the project and open the directory containing `manage.py`.
2. Create a local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

3. Create and activate a virtual environment, then install dependencies:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. Configure `.env`. You can leave `DATABASE_URL` blank to use local SQLite. Add a newly generated AI provider key only to your local `.env`.
5. Apply migrations, seed existing reference data, and run the server:

   ```powershell
   python manage.py migrate
   python manage.py seed_nutrition_data
   python manage.py seed_faqs
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000/`.

Run tests with:

```powershell
python manage.py test
```

## Environment variables

- `SECRET_KEY`: local Django secret; use Render's generated/managed secret in production.
- `DEBUG`: `True` for local development, `False` in production.
- `ALLOWED_HOSTS`: comma-separated allowed hostnames.
- `DATABASE_URL`: blank for local SQLite; set to PostgreSQL in production.
- `AI_API_KEY`: newly generated Groq API key. Never commit it or paste it into source files.
- `AI_API_URL`: `https://api.groq.com/openai/v1/chat/completions` for the current Groq configuration.
- `AI_MODEL`: model ID enabled for your Groq account.
- `AI_API_TIMEOUT`: timeout in seconds.
- `MONGODB_URI`: optional, used only for optional chat/feedback logging.
- `NUTRITION_API_KEY`: optional for the current Open Food Facts integration.

Local `.env` values do not update Render. Set production values separately in **Render → Fitora service → Environment**. The deliverable ZIP intentionally excludes `.env`, database files, Python bytecode, and local logs.

## Deploy on Render

The repository's `render.yaml` configures the web service and PostgreSQL. Its build command installs dependencies, collects static files, runs migrations, and seeds reference data. After pushing a code change, ensure Render deploys the latest commit from the intended branch. Store production secrets in Render Environment settings, never in GitHub.

## Current iteration

- Bounded AI conversation viewport with internal scrolling and improved Markdown display.
- Concise, direct-first assistant response instructions and reduced unrelated FAQ fallback.
- Contextual AI entry points in the dashboard, diary, progress, and plan pages.
- User-scoped, saved weekly plan with editable preferences, per-day collapsible details, prep ideas, and shopping list.
- Reduced duplicate UI, including hiding the floating assistant control on its full-page chat screen.

## Validation note

Python syntax compilation and `node --check static/js/chat.js` passed during packaging. The Django test suite and live provider requests could not be run in this workspace because Django was not installed and package downloads were unavailable. Run the tests locally or in CI before treating the package as production-verified.
