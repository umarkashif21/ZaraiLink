import os
import pickle
import numpy as np
from django.core.management.base import BaseCommand
from django.conf import settings
from trade_data.models import ProductSubCategory
from sentence_transformers import SentenceTransformer

class Command(BaseCommand):
    help = 'Builds the semantic search index for Product Subcategories'

    def handle(self, *args, **options):
        self.stdout.write("Building search index...")
        
        # 1. Fetch data
        subcategories = list(ProductSubCategory.objects.all())
        if not subcategories:
            self.stdout.write(self.style.WARNING("No subcategories found in database. Run 'load_data.py' or 'ingest_trade' first."))
            return

        texts = [s.name for s in subcategories]
        ids = [s.id for s in subcategories]
        hs_codes = [s.hs_code for s in subcategories]
        
        self.stdout.write(f"Encoding {len(texts)} subcategories... (This may take a moment)")
        
        # 2. Generate Embeddings
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts)
        
        # 3. Save to disk
        index_path = os.path.join(settings.BASE_DIR, 'search_index.pkl')
        with open(index_path, 'wb') as f:
            pickle.dump({
                'ids': ids, 
                'names': texts,
                'hs_codes': hs_codes,
                'embeddings': embeddings
            }, f)
            
        self.stdout.write(self.style.SUCCESS(f"Index built successfully at {index_path}"))
