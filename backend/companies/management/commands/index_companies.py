from django.core.management.base import BaseCommand
from companies.models import Company
from utils.ai_service import AIService
from utils.redis_client import RedisClient
import logging
import time

logger = logging.getLogger('zarailink')

class Command(BaseCommand):
    help = 'Index all companies into Redis Vector Store for Smart Search'

    def handle(self, *args, **options):
        self.stdout.write("Initializing Redis Index...")
        RedisClient.create_index()
        
        companies = Company.objects.filter(verification_status='verified')
        total = companies.count()
        self.stdout.write(f"Found {total} verified companies to index.")
        
        count = 0
        for company in companies:
            text = f"{company.name}. "
            if company.sector:
                text += f"Sector: {company.sector.name}. "
            if company.description:
                text += f"{company.description[:500]}" 
            
            embedding = AIService.get_embedding(text)
            if embedding:
                metadata = {
                    "name": company.name,
                    "description": company.description[:100] if company.description else ""
                }
                RedisClient.index_data("company", company.id, embedding, metadata)
                count += 1
                if count % 10 == 0:
                    self.stdout.write(f"Indexed {count}/{total}")
                
                time.sleep(0.1)
            else:
                self.stdout.write(self.style.WARNING(f"Failed to generate embedding for {company.name}"))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully indexed {count} companies."))
