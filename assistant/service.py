import re
import uuid
import logging
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

from support.models import FAQ, SupportTicket
from support.error_data import ERROR_CODES
from food_diary.models import FoodEntry
from accounts.models import Profile

logger = logging.getLogger('fitora.assistant')

class FitoraAssistantService:
    """
    Intelligent Assistant service for Fitora.
    Integrates PostgreSQL FAQ retrieval, real-time user calorie metrics,
    error code explanations, support ticket generation, and external LLM with robust fallback.
    """

    def __init__(self):
        self.api_key = getattr(settings, 'AI_API_KEY', '').strip()
        self.api_url = getattr(settings, 'AI_API_URL', '').strip()
        self.model = getattr(settings, 'AI_MODEL', 'qwen/qwen3.8-27b').strip()
        self.timeout = max(10, int(getattr(settings, 'AI_API_TIMEOUT', 35)))

    def process_message(self, user_message, user=None, conversation_id=None, page='', image_data=None, history=None):
        """
        Main processing pipeline for user queries.
        Returns a dictionary with:
        {
            'response': str,
            'source': 'faq_database' | 'error_guide' | 'user_nutrition' | 'ticket_system' | 'llm_api' | 'fallback_faq',
            'ticket_offered': bool,
            'ticket_created': bool,
            'ticket_id': str or None,
            'conversation_id': str
        }
        """
        conv_id = conversation_id or str(uuid.uuid4())
        clean_msg = (user_message or '').strip()
        image_data = image_data or None

        if not clean_msg and image_data:
            clean_msg = 'Please analyze the attached image and provide relevant nutrition or fitness insights. Explain what can and cannot be reliably inferred from the image.'

        if not clean_msg:
            return {
                'response': "Hello! I am your Fitora AI assistant. How can I assist you with your fitness, nutrition, or technical questions today?",
                'source': 'system',
                'ticket_offered': False,
                'ticket_created': False,
                'ticket_id': None,
                'conversation_id': conv_id
            }

        # Use deterministic, database-backed actions for explicit text-only intents.
        # Image requests should always reach the multimodal model for visual analysis.
        if not image_data:
            ticket_result = self._check_support_ticket_intent(clean_msg, user)
            if ticket_result:
                ticket_result['conversation_id'] = conv_id
                return ticket_result

            error_result = self._check_error_code_inquiry(clean_msg)
            if error_result:
                error_result['conversation_id'] = conv_id
                return error_result

            nutrition_result = self._check_user_nutrition_inquiry(clean_msg, user)
            if nutrition_result:
                nutrition_result['conversation_id'] = conv_id
                return nutrition_result

        # 4. Retrieve Relevant FAQs from PostgreSQL
        relevant_faqs = self._retrieve_relevant_faqs(clean_msg)

        # 5. If LLM API Key is configured, attempt LLM call with PostgreSQL FAQ context
        if self.api_key and self.api_url:
            llm_result = self._call_llm_api(clean_msg, relevant_faqs, user, image_data=image_data, history=history)
            if llm_result:
                llm_result['conversation_id'] = conv_id
                return llm_result
            # Image understanding cannot be replaced by a text-only FAQ fallback.
            logger.warning("LLM API call was unsuccessful. Falling back to internal FAQ knowledge base.")
            if image_data:
                return {
                    'response': "I couldn't analyze that image right now because the AI service did not return a usable response. Please retry shortly, or ask your question without an image.",
                    'source': 'ai_unavailable', 'ticket_offered': False,
                    'ticket_created': False, 'ticket_id': None, 'conversation_id': conv_id,
                }
        elif image_data:
            return {
                'response': "Image analysis is temporarily unavailable because the AI service is not configured. Please try again later or continue with a text question.",
                'source': 'ai_unavailable', 'ticket_offered': False,
                'ticket_created': False, 'ticket_id': None, 'conversation_id': conv_id,
            }

        # 6. Fallback / Direct FAQ Knowledge Base Response
        fallback_resp = self._build_faq_response(clean_msg, relevant_faqs)
        fallback_resp['conversation_id'] = conv_id
        return fallback_resp

    def _check_support_ticket_intent(self, message, user):
        """
        Detects if user is asking to create a support ticket.
        If confirmed, creates ticket in PostgreSQL and returns actual ticket ID.
        """
        lower = message.lower()
        ticket_triggers = [
            'create a ticket', 'open a ticket', 'submit ticket', 'create ticket',
            'contact support team', 'yes create a ticket', 'file a ticket', 'open ticket',
            'support ticket', 'open a support ticket', 'create a support ticket', 'submit a ticket'
        ]
        has_ticket_intent = any(trigger in lower for trigger in ticket_triggers) or (
            ('ticket' in lower) and any(verb in lower for verb in ['open', 'create', 'file', 'submit', 'raise'])
        )
        if has_ticket_intent:
            # Extract description or use message
            ticket_id = SupportTicket.generate_ticket_id()
            subject = f"Support Request from Fitora AI: {message[:60]}"
            description = f"User initiated support ticket via Fitora AI Assistant.\nFull query: {message}"
            contact_email = user.email if (user and user.is_authenticated) else 'guest@fitora.local'

            ticket = SupportTicket.objects.create(
                ticket_id=ticket_id,
                user=user if (user and user.is_authenticated) else None,
                contact_email=contact_email,
                subject=subject,
                description=description,
                category='Technical',
                status=SupportTicket.STATUS_OPEN
            )

            response_text = (
                f"I have opened a support ticket for you!\n\n"
                f"**Ticket Reference ID:** `{ticket.ticket_id}`\n"
                f"**Status:** Open\n"
                f"**Subject:** {ticket.subject}\n\n"
                f"Our support team has been notified and will assist you shortly. "
                f"You can view and track your ticket anytime in the Support Tickets portal."
            )
            return {
                'response': response_text,
                'source': 'ticket_system',
                'ticket_offered': False,
                'ticket_created': True,
                'ticket_id': ticket.ticket_id,
            }
        return None

    def _check_error_code_inquiry(self, message):
        """
        Detects error code references and returns structured troubleshooting info.
        """
        upper = message.upper()
        # Look for APP-001 or standard 3-digit HTTP codes
        matched_code = None
        if 'APP-001' in upper or 'APP001' in upper:
            matched_code = 'APP-001'
        else:
            for code in ['400', '401', '403', '404', '429', '500', '503']:
                # Match isolated code numbers or 'HTTP 404', 'Error 500'
                if re.search(r'\b' + code + r'\b', upper):
                    matched_code = code
                    break

        if matched_code and matched_code in ERROR_CODES:
            info = ERROR_CODES[matched_code]
            causes = "\n- ".join(info['common_causes'])
            steps = "\n- ".join(info['troubleshooting'])
            resp = (
                f"### {info['code']} — {info['title']}\n\n"
                f"**Meaning:** {info['meaning']}\n\n"
                f"**Common Causes:**\n- {causes}\n\n"
                f"**Recommended Troubleshooting Steps:**\n- {steps}\n\n"
                f"**Resolution:** {info['resolution_party']}\n\n"
                f"_If you need further assistance, you can ask me to **create a support ticket** at any time._"
            )
            return {
                'response': resp,
                'source': 'error_guide',
                'ticket_offered': True,
                'ticket_created': False,
                'ticket_id': None,
            }
        return None

    def _check_user_nutrition_inquiry(self, message, user):
        """
        If user asks about their recorded calorie intake or remaining calories,
        retrieves actual authenticated user's data from PostgreSQL.
        Never invents personal nutrition data.
        """
        lower = message.lower()
        # Only queries about recorded intake should be answered from the food diary.
        # General goal-setting questions such as 'How many calories should I eat?' must reach the LLM.
        calorie_keywords = [
            'my calories', 'calories remaining', 'calories today', 'intake today',
            'calories left', 'what did i eat', 'my calorie intake', 'my food diary',
            'how many calories have i', 'how many calories did i',
            'how much have i eaten', 'what have i eaten today',
            'what have i logged', 'calorie intake today', 'my nutrition today'
        ]
        if any(kw in lower for kw in calorie_keywords):
            if not user or not user.is_authenticated:
                return {
                    'response': "To view your personalized daily calorie intake and remaining calories, please **Sign In** to your Fitora account. Once logged in, I can pull your exact live food diary data!",
                    'source': 'user_nutrition',
                    'ticket_offered': False,
                    'ticket_created': False,
                    'ticket_id': None,
                }

            today = timezone.now().date()
            profile, _ = Profile.objects.get_or_create(user=user)
            entries = FoodEntry.objects.filter(user=user, date=today)

            consumed = sum((e.calories for e in entries), Decimal('0.00'))
            protein = sum((e.protein for e in entries), Decimal('0.00'))
            carbs = sum((e.carbohydrates for e in entries), Decimal('0.00'))
            fat = sum((e.fat for e in entries), Decimal('0.00'))
            goal = Decimal(str(profile.daily_calorie_goal))
            remaining = goal - consumed

            if entries.exists():
                recent_items = ", ".join([f"{e.food_name} ({e.calories} kcal)" for e in entries[:5]])
                resp = (
                    f"Here is your verified nutrition summary for today ({today.strftime('%B %d, %Y')}):\n\n"
                    f"- **Daily Goal:** {goal} kcal\n"
                    f"- **Calories Consumed:** {consumed} kcal\n"
                    f"- **Calories Remaining:** {remaining} kcal\n"
                    f"- **Macros:** Protein: {protein}g / {profile.daily_protein_goal}g | Carbs: {carbs}g / {profile.daily_carbs_goal}g | Fat: {fat}g / {profile.daily_fat_goal}g\n"
                    f"- **Logged Meals:** {recent_items}\n\n"
                    f"*(Calculation: Calories Remaining = Goal [{goal}] - Consumed [{consumed}] = {remaining} kcal. Non-medical tracking estimate.)*"
                )
            else:
                resp = (
                    f"You haven't logged any foods yet today ({today.strftime('%B %d, %Y')}).\n\n"
                    f"- **Daily Calorie Goal:** {goal} kcal\n"
                    f"- **Calories Consumed:** 0.00 kcal\n"
                    f"- **Calories Remaining:** {goal} kcal\n\n"
                    f"Head over to your **Food Diary** to log your breakfast, lunch, dinner, or snacks!"
                )

            return {
                'response': resp,
                'source': 'user_nutrition',
                'ticket_offered': False,
                'ticket_created': False,
                'ticket_id': None,
            }
        return None

    def _retrieve_relevant_faqs(self, message):
        """
        Retrieves matching FAQs from PostgreSQL database before generating an answer.
        """
        words = [w.lower() for w in re.findall(r'\b\w{3,}\b', message)]
        if not words:
            return list(FAQ.objects.filter(is_active=True)[:3])

        active_faqs = FAQ.objects.filter(is_active=True)
        scored_faqs = []

        for faq in active_faqs:
            q_lower = faq.question.lower()
            a_lower = faq.answer.lower()
            score = sum(3 for w in words if w in q_lower) + sum(1 for w in words if w in a_lower)
            if score > 0:
                scored_faqs.append((score, faq))

        scored_faqs.sort(key=lambda x: x[0], reverse=True)
        return [f[1] for f in scored_faqs[:3]]

    def _call_llm_api(self, message, relevant_faqs, user, image_data=None, history=None):
        """Call the configured chat-completions provider, supporting text and images."""
        faq_context = ""
        if relevant_faqs:
            faq_context = "Fitora official FAQ context (use only when relevant):\n" + "\n".join(
                [f"Q: {f.question}\nA: {f.answer}" for f in relevant_faqs]
            )

        profile_context = ""
        if user and getattr(user, 'is_authenticated', False):
            try:
                profile = Profile.objects.filter(user=user).first()
                if profile:
                    profile_context = (
                        "\nUser profile facts from Fitora (use as context, not as medical advice):\n"
                        f"Daily calorie target: {profile.daily_calorie_goal} kcal\n"
                        f"Current weight: {profile.current_weight if profile.current_weight is not None else 'not set'} kg\n"
                        f"Target weight: {profile.target_weight if profile.target_weight is not None else 'not set'} kg\n"
                        f"Daily protein/carbohydrate/fat goals: {profile.daily_protein_goal}g / {profile.daily_carbs_goal}g / {profile.daily_fat_goal}g\n"
                    )
            except Exception:
                logger.debug("Unable to load optional Fitora profile context for AI request.")

        system_prompt = (
            "You are Fitora AI, a practical fitness, nutrition and food-tracking assistant. "
            "Be accurate, direct, supportive and specific. Answer the actual question rather than forcing it into the FAQ. "
            "When estimating daily calories, explain that body weight alone is insufficient for a precise estimate; ask for age, height, sex and activity level when needed. "
            "Distinguish estimates from values actually recorded in Fitora. Never invent food diary data. "
            "For food photos, describe visible foods and give clearly labelled approximate portion/calorie estimates only when reasonable; ask for portion size or ingredients when uncertain. "
            "Do not diagnose conditions, prescribe treatment, encourage unsafe restriction, or present image-based nutrition estimates as exact. "
            "For a bug or unresolved app issue, explain next steps and offer a support ticket. Never claim an action was completed unless the system did it.\n\n"
            f"{faq_context}{profile_context}"
        )

        try:
            # Google's Gemini API uses its own request/response structure.
            if 'generativelanguage.googleapis.com' in self.api_url:
                contents = [{"role": "user" if item.get('role') == 'user' else 'model', "parts": [{"text": item.get('content', '')}]}
                            for item in (history or [])[-8:] if item.get('role') in ('user', 'assistant') and item.get('content')]
                parts = [{"text": message}]
                if image_data:
                    mime_type, encoded = self._split_image_data(image_data)
                    if not mime_type:
                        logger.warning("AI image rejected because its data URI was invalid.")
                        return None
                    parts.append({"inline_data": {"mime_type": mime_type, "data": encoded}})
                contents.append({"role": "user", "parts": parts})
                url = self.api_url + ("&" if "?" in self.api_url else "?") + f"key={self.api_key}"
                payload = {"system_instruction": {"parts": [{"text": system_prompt}]}, "contents": contents, "generationConfig": {"temperature": 0.3, "maxOutputTokens": 900}}
                response = requests.post(url, json=payload, timeout=(5, self.timeout))
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get('candidates', [])
                    if candidates:
                        text = ''.join(part.get('text', '') for part in candidates[0].get('content', {}).get('parts', []))
                        if text.strip():
                            return self._llm_result(text)
                logger.warning("AI provider returned HTTP %s.", response.status_code)
                return None

            headers = {
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': 'application/json',
            }
            if image_data:
                mime_type, _encoded = self._split_image_data(image_data)
                if not mime_type:
                    logger.warning("AI image rejected because its data URI was invalid.")
                    return None
                user_content = [
                    {"type": "text", "text": message},
                    {"type": "image_url", "image_url": {"url": image_data}},
                ]
            else:
                user_content = message

            history_messages = [
                {"role": item.get('role'), "content": item.get('content', '')}
                for item in (history or [])[-8:]
                if item.get('role') in ('user', 'assistant') and isinstance(item.get('content'), str) and item.get('content').strip()
            ]
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *history_messages,
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.35,
                "max_completion_tokens": 900,
                "stream": False,
            }
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=(5, self.timeout))
            if response.status_code == 200:
                data = response.json()
                choices = data.get('choices') or []
                text = choices[0].get('message', {}).get('content', '') if choices else ''
                if isinstance(text, list):
                    text = ''.join(part.get('text', '') for part in text if isinstance(part, dict))
                if isinstance(text, str) and text.strip():
                    return self._llm_result(text.strip())
                logger.warning("AI provider returned an empty completion.")
                return None

            # Log status only. Never log response bodies, tokens, or user prompts.
            logger.warning("AI provider returned HTTP %s.", response.status_code)
            return None
        except requests.exceptions.Timeout:
            logger.warning("AI provider request timed out after %s seconds.", self.timeout)
            return None
        except requests.exceptions.RequestException as exc:
            logger.warning("AI provider transport error (%s).", exc.__class__.__name__)
            return None
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning("AI provider response could not be parsed (%s).", exc.__class__.__name__)
            return None
        except Exception as exc:
            logger.exception("Unexpected AI provider integration error (%s).", exc.__class__.__name__)
            return None

    @staticmethod
    def _split_image_data(image_data):
        """Return (MIME type, base64 payload) for a validated image data URI."""
        match = re.fullmatch(r'data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=\r\n]+)', image_data or '')
        if not match:
            return None, None
        return match.group(1), re.sub(r'\s+', '', match.group(2))

    @staticmethod
    def _llm_result(text):
        return {
            'response': text,
            'source': 'llm_api',
            'ticket_offered': 'support ticket' in text.lower(),
            'ticket_created': False,
            'ticket_id': None,
        }

    def _build_faq_response(self, message, relevant_faqs):
        """
        Builds a high quality response from PostgreSQL FAQ records when LLM API is unavailable.
        """
        if relevant_faqs:
            best_match = relevant_faqs[0]
            resp = (
                f"**From Fitora Knowledge Base:**\n\n"
                f"**{best_match.question}**\n\n"
                f"{best_match.answer}\n\n"
            )
            if len(relevant_faqs) > 1:
                resp += "**Related Topics:**\n"
                for related in relevant_faqs[1:]:
                    resp += f"- *{related.question}*: {related.answer[:120]}...\n"

            resp += "\n_Would you like to open a **support ticket** for further assistance? Reply with 'Create a ticket' anytime._"
            return {
                'response': resp,
                'source': 'faq_database',
                'ticket_offered': True,
                'ticket_created': False,
                'ticket_id': None,
            }

        # No matching FAQ
        resp = (
            "I could not locate an exact match for your inquiry in our current FAQ knowledge base.\n\n"
            "I can help you with:\n"
            "- Adding food entries, editing servings, and tracking calories & macros\n"
            "- Understanding HTTP errors (400, 401, 403, 404, 429, 500, 503) or APP-001\n"
            "- Creating recipes and logging meals\n"
            "- Managing your weight and tracking progress\n\n"
            "Would you like me to **create a support ticket** so our team can review this? Just reply **'Create a ticket'**."
        )
        return {
            'response': resp,
            'source': 'fallback_faq',
            'ticket_offered': True,
            'ticket_created': False,
            'ticket_id': None,
        }
