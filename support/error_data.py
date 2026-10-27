"""
Error codes knowledge base for Fitora.
Includes the 7 required HTTP error codes and the custom APP-001 application-specific error code.
"""

ERROR_CODES = {
    '400': {
        'code': 'HTTP 400',
        'title': 'Bad Request',
        'meaning': 'The server cannot process the request due to malformed syntax, invalid input parameters, or missing required fields.',
        'common_causes': [
            'Entering invalid characters or negative numbers in serving amounts or calorie fields.',
            'Submitting an incomplete or corrupted form.',
            'Expired or invalid CSRF verification token.'
        ],
        'troubleshooting': [
            'Check that all required fields (e.g. food name, positive serving quantity) are correctly formatted.',
            'Refresh the page and re-enter the form values.',
            'Clear browser cookies and reload if the session has expired.'
        ],
        'resolvable_by_user': True,
        'resolution_party': 'User can resolve directly by correcting form inputs.'
    },
    '401': {
        'code': 'HTTP 401',
        'title': 'Unauthorized',
        'meaning': 'Authentication is required and has failed or has not been provided to access private nutrition data.',
        'common_causes': [
            'Attempting to view the Dashboard, Food Diary, Recipes, or Progress without signing in.',
            'Session expiration after a period of inactivity.'
        ],
        'troubleshooting': [
            'Click "Sign In" in the navigation bar and enter your valid username and password.',
            'If you do not have an account, click "Sign Up" to register.'
        ],
        'resolvable_by_user': True,
        'resolution_party': 'User can resolve directly by logging into their account.'
    },
    '403': {
        'code': 'HTTP 403',
        'title': 'Forbidden',
        'meaning': 'The server understood the request, but refuses to authorize it. You do not have permission to access or edit this resource.',
        'common_causes': [
            'Attempting to edit or delete another user\'s food entry, recipe, or support ticket by manually altering URL IDs.',
            'Missing CSRF verification cookie on form submission.'
        ],
        'troubleshooting': [
            'Verify that you are accessing your own diary entries and recipes.',
            'Do not alter URL IDs in the browser address bar.',
            'Ensure cookies and JavaScript are enabled for CSRF protection.'
        ],
        'resolvable_by_user': True,
        'resolution_party': 'User can resolve by returning to their own authorized dashboard.'
    },
    '404': {
        'code': 'HTTP 404',
        'title': 'Not Found',
        'meaning': 'The requested page or endpoint could not be found on the Fitora server.',
        'common_causes': [
            'Typing an incorrect or misspelled URL.',
            'Following an outdated link or accessing a deleted recipe or food entry.'
        ],
        'troubleshooting': [
            'Check the web address for typing errors.',
            'Click the "Dashboard" or "Food Diary" link to return to a valid page.',
            'Use the floating "Ask Fitora AI" widget to find the feature you need.'
        ],
        'resolvable_by_user': True,
        'resolution_party': 'User can resolve directly by navigating to an existing page.'
    },
    '429': {
        'code': 'HTTP 429',
        'title': 'Too Many Requests',
        'meaning': 'The client has sent too many requests in a given amount of time (rate limited).',
        'common_causes': [
            'Rapidly sending consecutive food search queries or AI assistant messages.',
            'Third-party external nutrition API rate-limit thresholds reached.'
        ],
        'troubleshooting': [
            'Wait 10 to 30 seconds before sending another query.',
            'Fitora will automatically activate cached database foods if external search limits are reached.'
        ],
        'resolvable_by_user': True,
        'resolution_party': 'User can resolve by waiting briefly before retrying.'
    },
    '500': {
        'code': 'HTTP 500',
        'title': 'Internal Server Error',
        'meaning': 'The server encountered an unexpected condition that prevented it from fulfilling the request.',
        'common_causes': [
            'Unhandled backend exception or database query syntax fault.',
            'Temporary server misconfiguration or unhandled server crash.'
        ],
        'troubleshooting': [
            'Refresh the page after a few moments.',
            'If the error persists, open a support ticket or ask Fitora AI to file an issue for the engineering team.'
        ],
        'resolvable_by_user': False,
        'resolution_party': 'Needs technical support / engineering team investigation.'
    },
    '503': {
        'code': 'HTTP 503',
        'title': 'Service Unavailable',
        'meaning': 'The server is currently unable to handle the request due to maintenance, heavy overload, or downstream database downtime.',
        'common_causes': [
            'Temporary PostgreSQL maintenance or planned platform updates.',
            'Severe resource exhaustion on hosting environment.'
        ],
        'troubleshooting': [
            'Check the `/health/` status page for system diagnostics.',
            'Wait a few minutes and retry your request.'
        ],
        'resolvable_by_user': False,
        'resolution_party': 'Needs platform recovery or hosting provider resolution.'
    },
    'APP-001': {
        'code': 'APP-001',
        'title': 'Fitora Application-Specific Error',
        'meaning': 'An internal application logic event occurred, such as nutrition calculation overflow or third-party nutrition search timeout falling back to local storage.',
        'common_causes': [
            'Attempting to calculate recipe or food nutrition with an excessive numerical input (e.g., serving quantity > 10,000).',
            'External nutrition API connection timed out, triggering local database fallback mode.',
            'Missing or corrupted user profile goal parameters.'
        ],
        'troubleshooting': [
            'Ensure serving sizes and nutrition numbers are within sensible ranges (1 - 5000g).',
            'If searching for foods, select from verified local items or add a custom food item manually.',
            'If profile goals are missing, visit your Profile page and click Save Goals.'
        ],
        'resolvable_by_user': True,
        'resolution_party': 'User can resolve by adjusting numbers or using database fallback; support ticket optional.'
    }
}
