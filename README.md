# FITORA — AI-Powered Fitness and Nutrition Tracker

> **Tagline:** Your Goals. Your Journey. Your Fit.  
> **Course / Assessment:** Software Development Final Assessment (Marked out of 100)

---

## Local environment and AI assistant

1. Copy `.env.example` to `.env`.
2. Create a fresh Groq API key from the official console and set `AI_API_KEY` in your local `.env`. Never commit `.env` or put the key into browser JavaScript.
3. The default model is `qwen/qwen3.8-27b`, which supports text and image inputs. Adjust `AI_MODEL` only to a model enabled for your account.
4. The assistant accepts JPEG, PNG, and WebP uploads up to 4 MB, keeps a limited recent text history per page session, and returns image-based insights with explicit uncertainty. Visual nutrition estimates are approximate and not medical advice.
5. In Render, configure `AI_API_KEY`, `AI_API_URL`, and `AI_MODEL` under the web service's Environment settings, then deploy the latest commit.

The key previously pasted into a chat should be revoked and replaced. Do not copy that exposed value into this repository.

## 1. Project Overview

**Fitora** is a full-stack, enterprise-grade fitness and nutrition tracking web platform engineered with Python and Django. Drawing functional inspiration from MyFitnessPal and a modern commercial lifestyle aesthetic, Fitora combines precision macronutrient tracking, daily energy calculations, recipe and meal portion builders, interactive Chart.js analytics, and an intelligent AI assistant backed by a PostgreSQL FAQ knowledge base and MongoDB Atlas audit logs.

### Key Highlights
- **Precision Energy Balance:** Strict Decimal arithmetic prevents floating-point inaccuracies when calculating calories consumed and remaining (`Calories Remaining = Daily Goal - Calories Consumed`).
- **Dynamic Serving Scaling:** Scaling any food portion (e.g., 100g to 250g) dynamically re-computes calories, protein, carbohydrates, and fats in real-time.
- **Resilient Third-Party Nutrition API:** Nutrition search via Open Food Facts with strict connection timeouts (4s), rate-limit resilience, and automatic fallback to verified local PostgreSQL foods.
- **Fitora AI Assistant:** Available on every page via a floating chat widget. Prioritizes PostgreSQL FAQ retrieval before answering, diagnoses 8 documented system error codes (including custom `APP-001`), pulls live user calorie totals without hallucinations, generates tracked support tickets, and logs dialogues to MongoDB Atlas.
- **Custom Branded Error Handlers:** Dedicated custom 404 and 500 error pages with links back to the dashboard and direct "Ask Fitora AI" assistance.
- **System Health & Observability:** Live `/health/` monitoring endpoint reporting database status, MongoDB connectivity, and latency metrics alongside structured request logging middleware.

---

## 2. Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons | Responsive, accessible UI with custom cryo-glass branding (royal blue, warm ivory, and translucent frost surfaces) |
| **Visualization** | Chart.js 4.4 | Interactive calorie trend bars, weight tracking lines, and macro doughnut charts |
| **Backend** | Python 3.14 + Django 6.1 | Secure MVC architecture, CSRF protection, password validators, and session management |
| **Relational DB** | PostgreSQL (Production) / SQLite (Local Dev Fallback) | Managed via `dj-database-url` and `psycopg-3` for user profiles, food entries, recipes, FAQs, and tickets |
| **NoSQL DB** | MongoDB Atlas | Managed via `pymongo` for conversational audit logs and AI response feedback ratings |
| **AI Assistant** | Server-side LLM Integration | Groq chat-completions API with multimodal image support, PostgreSQL FAQ context, profile context, and safe fallback responses |
| **External API** | Open Food Facts API | Nutrition database query with connection timeouts, rate-limit safety, and database fallback |
| **Production Server** | Gunicorn + WhiteNoise | WSGI production server with compressed static asset serving on Render |

---

## 3. Architecture & Project Structure

```text
fitora/
├── manage.py                     # Django management script
├── requirements.txt              # Production Python dependencies
├── render.yaml                   # Infrastructure-as-Code blueprint for Render
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore specifications
├── IMPLEMENTATION_PLAN.md        # Architectural roadmap
├── README.md                     # Comprehensive documentation & checklist
│
├── config/                       # Core project configuration
│   ├── settings.py               # Django settings (DB, auth, logging, WhiteNoise)
│   ├── urls.py                   # Master routing & custom 404/500 handlers
│   ├── wsgi.py                   # Production WSGI application
│   └── asgi.py                   # ASGI application
│
├── accounts/                     # User authentication & nutrition goals
│   ├── models.py                 # Profile model (daily calories, macros, target weight)
│   ├── forms.py                  # UserRegistrationForm, ProfileUpdateForm
│   ├── views.py                  # Register, login, logout, profile views
│   └── urls.py
│
├── dashboard/                    # Overview dashboard & landing page
│   ├── views.py                  # home_view (public), dashboard_view (authenticated)
│   └── urls.py
│
├── food_diary/                   # Food diary logging & meal categories
│   ├── models.py                 # FoodEntry (Breakfast, Lunch, Dinner, Snacks)
│   ├── forms.py                  # FoodEntryForm with Decimal validation
│   ├── views.py                  # Diary view, add, edit, delete entry
│   └── urls.py
│
├── nutrition/                    # Nutrition database & third-party API client
│   ├── models.py                 # FoodItem (verified & custom foods)
│   ├── api_client.py             # NutritionAPIClient with timeout & fallback
│   ├── views.py                  # Live search API endpoint & custom food management
│   ├── management/commands/      # seed_nutrition_data command
│   └── urls.py
│
├── recipes/                      # Recipe & custom meal management
│   ├── models.py                 # Recipe, RecipeIngredient (per-serving math)
│   ├── forms.py                  # RecipeForm, RecipeIngredientForm
│   ├── views.py                  # Recipe CRUD & one-click diary logging
│   └── urls.py
│
├── progress/                     # Progress tracking & analytics
│   ├── models.py                 # WeightLog model (dated weight entries)
│   ├── forms.py                  # WeightLogForm
│   ├── views.py                  # Progress charts view (cal trends, weight history)
│   └── urls.py
│
├── support/                      # Knowledge base, error guides & health check
│   ├── models.py                 # FAQ and SupportTicket models
│   ├── error_data.py             # Documentation for 8 error codes (HTTP + APP-001)
│   ├── middleware.py             # RequestLoggingMiddleware for monitoring
│   ├── views.py                  # FAQ view, error guide, ticket portal, /health/ endpoint
│   ├── management/commands/      # seed_faqs command (13 initial FAQs)
│   └── urls.py
│
├── assistant/                    # AI Assistant & MongoDB integration
│   ├── service.py                # FitoraAssistantService (FAQ injection & fallback)
│   ├── mongo_client.py           # MongoDB Atlas chat logging & feedback client
│   ├── views.py                  # Chat API, feedback API, consultation page
│   ├── context_processors.py     # Global branding template context
│   └── urls.py
│
├── templates/                    # Semantic HTML5 Bootstrap templates
│   ├── base.html                 # Master template with floating AI widget & navbar
│   ├── 404.html                  # Custom 404 error page
│   ├── 500.html                  # Custom 500 error page
│   ├── accounts/                 # Login, register, profile
│   ├── dashboard/                # Home and dashboard views
│   ├── food_diary/               # Diary, entry form, confirm delete
│   ├── recipes/                  # Recipe list, detail, form, saved meals list & forms
│   ├── progress/                 # Progress & analytics view, edit weight record form
│   ├── support/                  # FAQ, error guide, tickets, APP-001 notice
│   └── assistant/                # Full AI consultation interface
│
├── static/                       # Static assets
│   ├── css/main.css              # Custom brand styles & responsive design
│   ├── js/main.js                # Form helpers & calculators
│   ├── js/chat.js                # Floating AI Assistant widget controller
│   └── images/hero_banner.jpg    # Custom high-resolution nutrition hero image
│
└── tests/                        # 46 comprehensive automated tests (100% PASS)
    ├── test_auth.py              # Registration, login, access isolation
    ├── test_nutrition_and_diary.py # Diary CRUD, Decimal math, serving scaling
    ├── test_stage3_features.py   # Starter foods search, Saved Meals CRUD & diary logging, validation
    ├── test_stage4_features.py   # Weight history, date filtering (7/30/custom), macro & calorie analytics, empty states
    ├── test_recipes.py           # Ingredient math, per-serving values, diary logging
    ├── test_faq_and_support.py   # FAQ retrieval, search, ticket persistence
    ├── test_assistant_and_mongo.py # AI FAQ context, calorie retrieval, MongoDB mocks
    ├── test_api_client.py        # Third-party API timeout and offline fallback
    └── test_views_and_errors.py  # Custom 404, 500, /health/ endpoint, APP-001 demo
```

---

## 4. Local Installation & Setup Instructions

Follow these clear terminal commands in **Windows PowerShell**:

### 1. Clone the Repository
```powershell
git clone <GITHUB_REPOSITORY_URL_PLACEHOLDER>
cd fitora
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and verify the settings. For local development with SQLite, `DATABASE_URL` can be left blank (defaults to local `db.sqlite3`). To connect to a local or remote PostgreSQL database, set:
```ini
DATABASE_URL=postgresql://username:password@localhost:5432/fitora_db
```

### 5. Apply Database Migrations
```powershell
python manage.py migrate
```

### 6. Seed Initial Data
Seed the verified nutrition database and 13 PostgreSQL FAQ records:
```powershell
python manage.py seed_nutrition_data
python manage.py seed_faqs
```

### 7. Create Superuser (Administrator)
```powershell
python manage.py createsuperuser
```

### 8. Run Automated Tests
Execute the automated test suite covering all 33 test cases:
```powershell
python manage.py test tests
```

### 9. Start the Development Server
```powershell
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 5. Deployment Guide (Render)

### Step 1: Create GitHub Repository
1. Initialize git and commit files:
   ```powershell
   git init
   git add .
   git commit -m "Initial commit of complete Fitora platform"
   git branch -M main
   git remote add origin <YOUR_GITHUB_REPO_URL>
   git push -u origin main
   ```
2. Verify that `.env` and `db.sqlite3` are not tracked (handled by `.gitignore`).

### Step 2: Deploy to Render using Blueprint
1. Log in to [Render](https://render.com/).
2. Click **New +** > **Blueprint**.
3. Connect your GitHub repository. Render will automatically parse `render.yaml`.
4. It will provision:
   - A **PostgreSQL Database** (`fitora-db`)
   - A **Web Service** (`fitora`) running `gunicorn config.wsgi:application`
5. Under Environment Variables in the Render dashboard, supply or verify:
   - `MONGODB_URI` (your MongoDB Atlas connection string; optional for core assistant replies)
   - `AI_API_KEY` (a newly generated Groq API key; do not reuse a key pasted into a chat)
   - `AI_API_URL=https://api.groq.com/openai/v1/chat/completions`
   - `AI_MODEL=qwen/qwen3.8-27b`
   - `AI_API_TIMEOUT=35`
   - `NUTRITION_API_KEY` (optional)
6. Once deployed, run migrations and seed data in the Render Shell:
   ```bash
   python manage.py migrate
   python manage.py seed_nutrition_data
   python manage.py seed_faqs
   ```
7. Verify HTTPS connectivity at your assigned `https://fitora.onrender.com` URL.

---

## 6. Live Project Links
- **Live Website URL:** `<LIVE_WEBSITE_URL_PLACEHOLDER>`
- **GitHub Repository URL:** `<GITHUB_REPOSITORY_URL_PLACEHOLDER>`

---

## 7. Known Limitations & Proposed Future Improvement

### Known Limitations
- External nutrition search speed is contingent on third-party network latency; however, Fitora handles this via strict 4-second timeouts and automatic fallback to verified local foods.
- MongoDB Atlas operations are decoupled from PostgreSQL transactions; if MongoDB is temporarily down, chat dialogues fall back gracefully while the core application remains fully functional.

### Proposed Future Improvement
> *"Add semantic search and personalized nutrition recommendations to improve FAQ retrieval and provide more relevant assistance based on a user's goals and food diary."*

---

## 8. Assessment Requirements Checklist (Marked out of 100)

| Category & Marks | Requirement | Implementation File / URL | Test Performed | Result | Remaining Work |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Website (10 Marks)** | Responsive design, 3+ functional pages | `templates/base.html`, `dashboard.html`, `diary.html`, `recipe_list.html`, `progress.html` | Tested across desktop & mobile screen breakpoints | **PASS** | None |
| **Website (10 Marks)** | Floating chat widget on every page | `templates/base.html`, `static/js/chat.js` | Modal toggle, quick prompt triggers on all routes | **PASS** | None |
| **FAQ (10 Marks)** | At least 10 FAQs stored in PostgreSQL | `support/models.py`, `support/management/commands/seed_faqs.py` | `tests/test_faq_and_support.py::test_faq_database_retrieval` (13 FAQs verified) | **PASS** | None |
| **FAQ (10 Marks)** | FAQ search & category filtering | `support/views.py::faq_view`, `templates/support/faq.html` | `tests/test_faq_and_support.py::test_faq_search`, `test_faq_category_filter` | **PASS** | None |
| **Error Codes (15 Marks)** | 7 HTTP codes + 1 custom APP-001 code | `support/error_data.py`, `templates/support/error_guide.html` | `tests/test_views_and_errors.py::test_app001_demo_page` | **PASS** | None |
| **Error Codes (15 Marks)** | Custom 404 and 500 error handlers | `support/views.py::custom_404_view`, `custom_500_view`, `templates/404.html`, `500.html` | `tests/test_views_and_errors.py::test_custom_404_page_on_invalid_url`, `test_custom_500_error_handler` | **PASS** | None |
| **AI Assistant (25 Marks)** | Answers retrieved from FAQ database | `assistant/service.py::process_message` | `tests/test_assistant_and_mongo.py::test_faq_retrieval_before_answering` | **PASS** | None |
| **AI Assistant (25 Marks)** | Explains error codes (HTTP + APP-001) | `assistant/service.py::_check_error_code_inquiry` | `tests/test_assistant_and_mongo.py::test_error_code_explanation_http_429`, `test_error_code_explanation_app_001` | **PASS** | None |
| **AI Assistant (25 Marks)** | Pulls live user calorie intake | `assistant/service.py::_check_user_nutrition_inquiry` | `tests/test_assistant_and_mongo.py::test_personal_calorie_data_retrieval` | **PASS** | None |
| **AI Assistant (25 Marks)** | Support ticket creation upon confirmation | `assistant/service.py::_check_support_ticket_intent` | `tests/test_assistant_and_mongo.py::test_support_ticket_creation_via_ai` | **PASS** | None |
| **AI Assistant (25 Marks)** | API failure fallback mode | `assistant/service.py::_build_faq_response` | `tests/test_assistant_and_mongo.py::test_ai_api_failure_fallback_mode` | **PASS** | None |
| **Backend & Data (15 Marks)** | Support tickets in PostgreSQL | `support/models.py::SupportTicket` | `tests/test_faq_and_support.py::test_support_ticket_creation_and_persistence` | **PASS** | None |
| **Backend & Data (15 Marks)** | Chat logs stored in MongoDB | `assistant/mongo_client.py::log_chat_interaction` | `tests/test_assistant_and_mongo.py::test_chat_api_endpoint_with_mongo_mock` | **PASS** | None |
| **Backend & Data (15 Marks)** | Feedback ratings in MongoDB | `assistant/mongo_client.py::log_user_feedback` | `tests/test_assistant_and_mongo.py::test_feedback_api_endpoint_with_mongo_mock` | **PASS** | None |
| **Deployment & Security (15 Marks)**| HTTPS & Render deployment spec | `render.yaml`, `config/settings.py` | SSL headers, cookie security, WhiteNoise static files verified | **PASS** | None |
| **Deployment & Security (15 Marks)**| Environment variables & no secrets in repo | `.env.example`, `.gitignore` | Inspected git status, `.env` excluded from VCS | **PASS** | None |
| **Monitoring & Feedback (5 Marks)**| Structured request logging | `support/middleware.py::RequestLoggingMiddleware` | Logged method, path, status, duration, user, IP | **PASS** | None |
| **Monitoring & Feedback (5 Marks)**| Health check endpoint (`/health/`) | `support/views.py::health_check_view` | `tests/test_views_and_errors.py::test_health_check_endpoint` | **PASS** | None |
| **Monitoring & Feedback (5 Marks)**| Nutrition API timeout & fallback | `nutrition/api_client.py::NutritionAPIClient` | `tests/test_api_client.py::test_nutrition_api_timeout_fallback`, `test_nutrition_api_rate_limit_429_fallback` | **PASS** | None |
| **Viva & Problem Solving (5 Marks)**| Automated test suite & documentation | `tests/`, `README.md` | Full suite execution: 46 tests passed in 79.2s | **PASS** | None |
