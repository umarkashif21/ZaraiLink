"""
Django management command: rebuild_search_index

Rebuilds the BM25 + FAISS-HNSW search index using nomic-embed-text-v1.
Run this after adding new ProductSubCategory or ProductItem records.

Usage:
    python manage.py rebuild_search_index
    python manage.py rebuild_search_index --force
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Rebuild BM25 + FAISS search index (nomic-embed-text-v1)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help='Force rebuild even if index file already exists',
        )

    def handle(self, *args, **options):
        from search.services.retrieval import build_index, HybridRetriever

        force = options['force']
        self.stdout.write(f'Building search index (force={force})...')

        try:
            idx = build_index(force_rebuild=force)
            # Invalidate singleton so next query loads fresh index
            HybridRetriever._index = None

            self.stdout.write(
                self.style.SUCCESS(
                    f'Index built: {idx["n_docs"]} subcategories, '
                    f'model={idx["model_name"]}, '
                    f'dim={idx["embedding_dim"]}'
                )
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Index build failed: {e}'))
            raise
