# Fitora Product Direction — Current Iteration

## Product principle

Fitora should help the user make the next useful decision, not add more dashboard cards. Keep navigation short, answers useful, and all advice grounded in the available data.

## Included in this iteration

1. **Conversation behaviour:** bounded transcript pane, internal scrolling, readable paragraph/list formatting, and no duplicated floating assistant control on the full-page chat.
2. **Response quality:** direct-first, concise instructions; current profile and recorded diary context; FAQ matching limited to Fitora help questions; honest handling when the AI provider is unavailable.
3. **Weekly plan:** saved user-scoped seven-day meal and movement plan, based on targets, preferences and recent logged foods. Includes prep tips and a shopping list. AI output is distinguished from a template fallback.
4. **AI in workflows:** focused actions from dashboard, food diary, progress and weekly plan instead of repeated generic AI panels.
5. **Simplification:** reduced navigation/footer noise and collapsible weekly-plan days.

## Future improvements worth prioritising

- Add explicit “Add to diary” actions only after the user chooses a planned meal and portion; never record a plan as food consumed automatically.
- Add confirmation before AI-driven changes to goals, saved foods or diary entries.
- Add plan history and restore/regenerate controls.
- Evaluate answer quality using a fixed suite of calorie, photo, trend and troubleshooting questions.
- Add true token streaming only when backend and frontend both support cancellation, error handling and safe stream parsing. Do not simulate streaming with a typewriter effect.

## Validation

Python syntax compilation and `node --check static/js/chat.js` passed during packaging. Django integration tests require the declared dependencies and must be run locally or in CI; they were not run in this environment because Django was unavailable.
