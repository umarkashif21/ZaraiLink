"""
Management command to generate embeddings for companies in the trade directory.
This creates CompanyEmbedding records for companies that don't have them,
enabling the Similar Companies feature.
"""
from django.core.management.base import BaseCommand
from companies.models import Company
from trade_data.models import CompanyEmbedding
from utils.ai_service import AIService
import logging

logger = logging.getLogger('zarailink')


class Command(BaseCommand):
    help = 'Generate embeddings for trade directory companies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of companies to process'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        
        
        existing_names = set(CompanyEmbedding.objects.values_list('company_name', flat=True))
        companies = Company.objects.filter(verification_status='verified')
        
        if limit:
            companies = companies[:limit]
        
        companies_to_process = [c for c in companies if c.name not in existing_names]
        
        self.stdout.write(f"Found {len(companies_to_process)} companies needing embeddings")
        
        created_count = 0
        for company in companies_to_process:
            
            text_parts = [company.name]
            if company.description:
                text_parts.append(company.description)
            if company.sector:
                text_parts.append(f"Sector: {company.sector.name}")
            if company.company_role:
                text_parts.append(f"Role: {company.company_role.name}")
            
            text = " | ".join(text_parts)
            
            
            embedding = AIService.get_embedding(text)
            
            if embedding:
                CompanyEmbedding.objects.create(
                    company_name=company.name,
                    embedding=embedding,
                    cluster_tag="Directory Company",  
                    pagerank=0.0,
                    degree=0
                )
                created_count += 1
                self.stdout.write(f"✓ Created embedding for: {company.name}")
            else:
                self.stdout.write(self.style.WARNING(f"✗ Failed to get embedding for: {company.name}"))
        
        self.stdout.write(self.style.SUCCESS(f"\nDone! Created {created_count} embeddings."))
