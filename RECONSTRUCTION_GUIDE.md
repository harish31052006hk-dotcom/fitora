# Fitora Reconstruction — Setup & Deployment Guide

## What changed

- Reworked the visual system to a responsive royal-blue / warm-ivory palette with frosted-glass panels, cleaner navigation, calmer cards, and a purpose-built assistant workspace.
- Unified floating-chat and full-page assistant behavior. Both support image attachments and show recoverable errors instead of leaving the interface in a permanent loading state.
- Switched the default AI configuration to Groq’s OpenAI-compatible chat-completions endpoint, moved the model ID into configuration, and enabled multimodal prompts for JPEG, PNG, and WebP images.
- Extended the request timeout, capped image sizes, restricted accepted image types, excluded encoded images from MongoDB interaction logs, and limited the amount of recent conversation history sent to the backend.
- Fixed the calorie-intent rule so a question such as “How many calories should I eat?” is not incorrectly treated as a request to read calories already logged in the diary.
- Added tests for the calorie-intent edge case, allowed image types, and image payload construction.

## Important credential security

A Groq key was pasted into the chat. Revoke it in the Groq console and create a replacement. The `.env` in this reconstruction contains a placeholder only; do not paste an exposed key into the distributable archive or Git history.

## Local setup

1. Use Python 3.11+ (or the version supported by your deployed Django environment).
2. Create a virtual environment, activate it, and install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and generate a new Django `SECRET_KEY`.
4. Set these local environment variables in `.env`:

   ```dotenv
   AI_API_KEY=your_new_groq_api_key
   AI_API_URL=https://api.groq.com/openai/v1/chat/completions
   AI_MODEL=qwen/qwen3.8-27b
   AI_API_TIMEOUT=35
   ```

5. Run `python manage.py migrate`, then `python manage.py runserver`. Seed FAQ and nutrition fixtures if your existing setup requires them.

## Render deployment

In the Render dashboard for the Fitora web service, set or verify:

- `AI_API_KEY`: your newly generated Groq key (secret value; do not share screenshots of it).
- `AI_API_URL`: `https://api.groq.com/openai/v1/chat/completions`
- `AI_MODEL`: `qwen/qwen3.8-27b`
- `AI_API_TIMEOUT`: `35`

Commit the reconstructed project without `.env`, push it to the connected GitHub repository, and deploy on Render. After deployment, open `/health/` to check app/database health and open `/assistant/` to test text and image questions. The health indicator can report the presence of configuration; it cannot prove the provider accepts the key, so send a real test prompt as well.

## Validation status

Python files were compiled with `py_compile` and the chat JavaScript was checked with `node --check`. The full Django test suite could not be executed in this environment because Django dependencies were not installed and package downloads were unavailable. Run `python manage.py test` in the project’s configured virtual environment before considering the deployment verified.
