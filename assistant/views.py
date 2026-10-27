import json
import base64
import binascii
import logging
from django.shortcuts import render
from django.http import JsonResponse

from .service import FitoraAssistantService
from .mongo_client import log_chat_interaction, log_user_feedback

logger = logging.getLogger('fitora.assistant')

def assistant_page_view(request):
    """
    Dedicated full-page AI Assistant consultation view.
    """
    return render(request, 'assistant/assistant.html', {
        'title': 'Ask Fitora AI Assistant'
    })

def chat_api_view(request):
    """POST API for text and image-assisted conversations."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    # Keep image requests bounded; large images can stall a free web instance.
    try:
        content_length = int(request.META.get('CONTENT_LENGTH') or 0)
    except (TypeError, ValueError):
        content_length = 0
    if content_length > 6_000_000:
        return JsonResponse({'error': 'The request is too large. Please use an image under 4 MB.'}, status=413)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({'error': 'The request body must be a JSON object.'}, status=400)

    message_value = data.get('message', '')
    message = message_value.strip() if isinstance(message_value, str) else ''
    conversation_value = data.get('conversation_id', '')
    conversation_id = conversation_value.strip()[:100] if isinstance(conversation_value, str) else ''
    page_value = data.get('page', '')
    page = page_value.strip()[:250] if isinstance(page_value, str) else ''
    image_data = data.get('image_data')
    if image_data is not None and not isinstance(image_data, str):
        return JsonResponse({'error': 'Invalid image attachment.'}, status=400)
    raw_history = data.get('history', [])
    history = []
    if isinstance(raw_history, list):
        for item in raw_history[-8:]:
            if not isinstance(item, dict) or item.get('role') not in ('user', 'assistant'):
                continue
            content = item.get('content', '')
            if isinstance(content, str) and content.strip():
                history.append({'role': item['role'], 'content': content.strip()[:1200]})

    if image_data:
        mime_type, encoded = FitoraAssistantService._split_image_data(image_data)
        if not mime_type or not encoded:
            return JsonResponse({'error': 'Unsupported image. Attach a JPEG, PNG, or WebP image.'}, status=400)
        try:
            raw_image = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            return JsonResponse({'error': 'The attached image could not be read. Please choose it again.'}, status=400)
        if len(raw_image) > 4 * 1024 * 1024:
            return JsonResponse({'error': 'Please use an image smaller than 4 MB.'}, status=413)

    if not message and not image_data:
        return JsonResponse({'error': 'Enter a message or attach an image.'}, status=400)
    if len(message) > 1000:
        return JsonResponse({'error': 'Message exceeds maximum length of 1000 characters.'}, status=400)

    try:
        service = FitoraAssistantService()
        result = service.process_message(
            user_message=message,
            user=request.user,
            conversation_id=conversation_id,
            page=page,
            image_data=image_data,
            history=history,
        )
        # Never store the base64 image or transmit it to the logging database.
        log_message = message if message else '[image attachment]'
        if image_data:
            log_message = f"{log_message} [image attached]"[:1000]
        user_identifier = request.user.username if request.user.is_authenticated else 'Anonymous'
        mongo_result = log_chat_interaction(
            conversation_id=result['conversation_id'],
            user_identifier=user_identifier,
            user_message=log_message,
            assistant_response=result['response'],
            page=page,
            status='success'
        )
        result['mongo_logged'] = mongo_result.get('saved', False)
        return JsonResponse(result)
    except Exception as exc:
        logger.exception("Chat API request failed (%s).", exc.__class__.__name__)
        return JsonResponse({
            'error': 'Fitora AI could not complete that request. Please retry in a moment or use the Help page.',
            'source': 'error',
        }, status=503)

def feedback_api_view(request):
    """
    POST API endpoint for recording user feedback on AI responses into MongoDB.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({'error': 'The request body must be a JSON object.'}, status=400)

    conversation_value = data.get('conversation_id', '')
    rating_value = data.get('rating', '')
    comment_value = data.get('comment', '')
    conversation_id = conversation_value.strip()[:100] if isinstance(conversation_value, str) else ''
    rating = rating_value.strip() if isinstance(rating_value, str) else ''
    comment = comment_value.strip()[:1000] if isinstance(comment_value, str) else ''

    if not conversation_id or rating not in ('helpful', 'unhelpful'):
        return JsonResponse({'error': 'A conversation ID and a valid feedback rating are required.'}, status=400)

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
