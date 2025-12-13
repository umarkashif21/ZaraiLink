import os
import openai
from django.conf import settings
import logging

logger = logging.getLogger('zarailink')

class AIService:
    _client = None

    @classmethod
    def get_client(cls):
        if not cls._client and settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            cls._client = openai.Client(api_key=settings.OPENAI_API_KEY)
        return cls._client

    @classmethod
    def get_embedding(cls, text):
        client = cls.get_client()
        if not client:
            logger.warning("OpenAI API Key not set. Skipping embedding.")
            return None
        
        try:
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    @classmethod
    def analyze_sentiment(cls, text):
        client = cls.get_client()
        if not client:
            return "Neutral"

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Analyze the sentiment of the following text. Return only one word: Positive, Negative, or Neutral."},
                    {"role": "user", "content": text}
                ],
                max_tokens=10
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return "Neutral"
