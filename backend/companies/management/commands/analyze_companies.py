from django.core.management.base import BaseCommand
from companies.models import Company
from utils.ai_service import AIService
import time

class Command(BaseCommand):
    help = 'Analyze sentiment of company descriptions'

    def handle(self, *args, **options):
        companies = Company.objects.all()
        total = companies.count()
        self.stdout.write(f"Analyzing sentiment for {total} companies...")
        
        count = 0
        for company in companies:
            if not company.description:
                continue
                
            sentiment = AIService.analyze_sentiment(company.description[:1000])
            company.market_sentiment = sentiment
            company.save(update_fields=['market_sentiment'])
            
            count += 1
            if count % 10 == 0:
                self.stdout.write(f"Analyzed {count}/{total}")
            
            time.sleep(0.1)
            
        self.stdout.write(self.style.SUCCESS(f"Successfully analyzed {count} companies."))
