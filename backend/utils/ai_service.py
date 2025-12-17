import os
import openai
from django.conf import settings
import logging
import json

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
    def smart_search(cls, query, company_data, max_results=20):
        """
        Use GPT to intelligently search companies based on natural language query.
        
        Args:
            query: User's search query (e.g., "sugar mills in karachi")
            company_data: List of dicts with company info [{id, name, province, sector, description}, ...]
            max_results: Maximum number of results to return
            
        Returns:
            List of company IDs that match the query, ordered by relevance
        """
        client = cls.get_client()
        if not client:
            logger.warning("OpenAI API Key not set. Cannot perform smart search.")
            return None
        
        
        company_summary = "\n".join([
            f"ID:{c['id']} | {c['name']} | {c.get('province', 'N/A')} | {c.get('sector', 'N/A')}"
            for c in company_data[:100]
        ])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a company search assistant. Given a user query and a list of companies, 
return the IDs of companies that best match the query. Consider:
- Company name matches
- Location/province matches  
- Sector/industry relevance
- Semantic meaning of the query

CRITICAL: Return ONLY pure JSON - a single array of company IDs ordered by relevance.
NO markdown, NO code blocks, NO explanation, NO extra text. JUST the JSON array.
Example correct response: [1, 5, 12, 8]
If no companies match: []"""
                    },
                    {
                        "role": "user", 
                        "content": f"Query: {query}\n\nCompanies:\n{company_summary}"
                    }
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            
            if result.startswith('```'):
                
                lines = result.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]  
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]  
                result = '\n'.join(lines).strip()
            
            
            try:
                ids = json.loads(result)
                if isinstance(ids, list):
                    return ids[:max_results]
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse GPT response: {result}")
                
        except Exception as e:
            logger.error(f"Error in smart search: {e}")
        
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

