# FITORA Implementation Plan

## Architecture & Technology Stack
- **Framework:** Python 3.14 + Django 6.1
- **Databases:**
  - Relational: PostgreSQL (with local SQLite fallback when `DATABASE_URL` is omitted)
  - NoSQL: MongoDB Atlas (via `pymongo` with resilient fallback if offline)
- **Frontend:** Bootstrap 5, Bootstrap Icons, Chart.js, Custom CSS (#142B3B Navy, #14B8A6 Teal, #A3E635 Lime Green, #F7F9FC Light BG)
- **AI Engine:** Secure server-side LLM integration (Gemini / OpenAI compatible API with FAQ context-injection + local heuristic FAQ & error code matcher fallback)
- **Nutrition API:** Open Food Facts & verified nutrition database with timeout, rate limit handling, and custom food fallback
- **Production Server:** Gunicorn + WhiteNoise + Render YAML deployment spec

## Implementation Stages
1. **Project Setup & Base Architecture:** Django project scaffolding, environment config, static assets, base responsive templates, brand styling, custom hero image.
2. **Authentication & User Management:** Registration, login, logout, password validation, user profiles & personalized calorie/macro goals.
3. **Food Diary & Nutrition Engine:** Breakfast/Lunch/Dinner/Snacks tracking, date navigation, serving size math, custom food entries, Decimal precision.
4. **Third-Party Nutrition API & Search:** Open Food Facts / Nutrition API integration with timeout, error handling, and offline fallback.
5. **My Meals & Recipes:** Recipe builder, ingredient calculation, per-serving macronutrient math, one-click logging to diary.
6. **Progress Tracking & Analytics:** Chart.js dashboards for calorie balance, weekly trends, macronutrient split, and historical weight logs.
7. **FAQ Knowledge Base & Error Code Guide:** PostgreSQL FAQ model, 12 pre-seeded entries, search & category filter, documentation for 8 error codes (HTTP 400, 401, 403, 404, 429, 500, 503, and APP-001).
8. **Custom Error Pages & Health Check:** Branded 404 & 500 error handlers, `/health/` monitoring endpoint with JSON status.
9. **Fitora AI Assistant & Support Tickets:** Global floating AI widget, database FAQ injection, user calorie context, error code diagnostics, support ticket creation, MongoDB conversation & feedback logging.
10. **Automated Testing & Verification:** Comprehensive test suite spanning auth, nutrition math, recipe math, tickets, FAQs, AI fallback, error pages, and health checks.
11. **Production Deployment & Documentation:** `render.yaml`, `requirements.txt`, `.env.example`, `.gitignore`, and detailed `README.md` with PowerShell setup instructions and assessment checklist.
