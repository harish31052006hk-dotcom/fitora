import logging
from datetime import datetime, timezone
from django.conf import settings

logger = logging.getLogger('fitora.mongo')

_mongo_client = None

def get_mongo_database():
    """
    Returns the MongoDB database instance if configured and reachable.
    Fails gracefully with None if MONGODB_URI is absent or connection times out.
    """
    global _mongo_client
    mongo_uri = getattr(settings, 'MONGODB_URI', '')
    if not mongo_uri or not mongo_uri.strip():
        return None

    try:
        if _mongo_client is None:
            import pymongo
            _mongo_client = pymongo.MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=2500,
                connectTimeoutMS=2500,
                socketTimeoutMS=2500
            )
        # Verify connection
        _mongo_client.admin.command('ping')
        db_name = getattr(settings, 'MONGODB_DB_NAME', 'fitora_logs')
        return _mongo_client[db_name]
    except Exception as e:
        logger.warning(f"MongoDB Atlas connection unavailable: {str(e)}")
        return None

def check_mongo_health():
    """Returns True if MongoDB is configured and responsive, False otherwise."""
    db = get_mongo_database()
    return db is not None

def log_chat_interaction(conversation_id, user_identifier, user_message, assistant_response, page='', status='success'):
    """
    Persists a chat interaction document to MongoDB Atlas.
    Fields: conversation_id, user, user_message, assistant_response, timestamp, page, status.
    Gracefully handles database errors without crashing application.
    """
    db = get_mongo_database()
    if db is None:
        logger.info(f"MongoDB not connected. Chat log for conv={conversation_id} skipped.")
        return {'saved': False, 'reason': 'MongoDB not configured or connection timed out'}

    try:
        collection = db['chat_logs']
        doc = {
            'conversation_id': str(conversation_id),
            'user': user_identifier or 'Anonymous',
            'user_message': user_message[:2000],
            'assistant_response': assistant_response[:4000],
            'page': page[:250],
            'status': status,
            'timestamp': datetime.now(timezone.utc),
        }
        res = collection.insert_one(doc)
        logger.info(f"Chat log saved to MongoDB with id={res.inserted_id}")
        return {'saved': True, 'id': str(res.inserted_id)}
    except Exception as e:
        logger.error(f"Failed to write chat log to MongoDB: {str(e)}")
        return {'saved': False, 'reason': str(e)}

def log_user_feedback(conversation_id, rating, comment='', user_identifier=''):
    """
    Persists user feedback on an AI response to MongoDB Atlas.
    Fields: conversation_id, rating, comment, timestamp, user.
    """
    db = get_mongo_database()
    if db is None:
        logger.info(f"MongoDB not connected. Feedback for conv={conversation_id} skipped.")
        return {'saved': False, 'reason': 'MongoDB not configured or connection timed out'}

    try:
        collection = db['feedback']
        doc = {
            'conversation_id': str(conversation_id),
            'user': user_identifier or 'Anonymous',
            'rating': rating, # e.g. 'helpful', 'unhelpful', or 1-5
            'comment': (comment or '')[:1000],
            'timestamp': datetime.now(timezone.utc),
        }
        res = collection.insert_one(doc)
        logger.info(f"Feedback saved to MongoDB with id={res.inserted_id}")
        return {'saved': True, 'id': str(res.inserted_id)}
    except Exception as e:
        logger.error(f"Failed to write feedback to MongoDB: {str(e)}")
        return {'saved': False, 'reason': str(e)}
