import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .service import FitoraAssistantService
from .mongo_client import log_chat_interaction, log_user_feedback

def assistant_page_view(request):
    """
    Dedicated full-page AI Assistant consultation view.
    """
    return render(request, 'assistant/assistant.html', {
        'title': 'Ask Fitora AI Assistant'
    })

def chat_api_view(request):
    """
    POST API endpoint for conversational AI interaction.
    Secured with server-side validation, rate limit protection, and MongoDB logging.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id', '').strip()
    page = data.get('page', '').strip()

    if not message:
        return JsonResponse({'error': 'Message content cannot be empty'}, status=400)

    if len(message) > 1000:
        return JsonResponse({'error': 'Message exceeds maximum length of 1000 characters'}, status=400)

    # Process message via Fitora Assistant Service
    service = FitoraAssistantService()
    result = service.process_message(
        user_message=message,
        user=request.user,
        conversation_id=conversation_id,
        page=page
    )

    # Log interaction to MongoDB Atlas
    user_identifier = request.user.username if request.user.is_authenticated else 'Anonymous'
    mongo_result = log_chat_interaction(
        conversation_id=result['conversation_id'],
        user_identifier=user_identifier,
        user_message=message,
        assistant_response=result['response'],
        page=page,
        status='success'
    )

    result['mongo_logged'] = mongo_result.get('saved', False)
    return JsonResponse(result)

def feedback_api_view(request):
    """
    POST API endpoint for recording user feedback on AI responses into MongoDB.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    conversation_id = data.get('conversation_id', '').strip()
    rating = data.get('rating', '').strip() # e.g. 'helpful', 'unhelpful'
    comment = data.get('comment', '').strip()

    if not conversation_id or not rating:
        return JsonResponse({'error': 'conversation_id and rating are required'}, status=400)

    user_identifier = request.user.username if request.user.is_authenticated else 'Anonymous'
    mongo_result = log_user_feedback(
        conversation_id=conversation_id,
        rating=rating,
        comment=comment,
        user_identifier=user_identifier
    )

    return JsonResponse({
        'success': True,
        'saved_to_mongo': mongo_result.get('saved', False),
        'reason': mongo_result.get('reason', '')
    })
