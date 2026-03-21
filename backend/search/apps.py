from django.apps import AppConfig


class SearchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'search'

    def ready(self):
        import threading
        t = threading.Thread(target=self._prewarm, daemon=True)
        t.start()

    def _prewarm(self):
        import logging
        logger = logging.getLogger(__name__)
        try:
            from search.services.retrieval import get_embedding_model, HybridRetriever
            get_embedding_model()
            logger.info("Search: embedding model pre-warmed")
            HybridRetriever.get_index()
            logger.info("Search: FAISS/BM25 index pre-warmed")
            from search.services.ranking_ltr import RankingEnsemble
            RankingEnsemble()
            logger.info("Search: LTR model pre-warmed")
        except Exception as e:
            logger.warning(f"Search pre-warm (retrieval/ranking) failed (non-fatal): {e}")
        try:
            from search.services.ner_extractor import get_ner_extractor
            get_ner_extractor()
            logger.info("Search: GLiNER NER model pre-warmed")
        except Exception as e:
            logger.warning(f"Search pre-warm (GLiNER) failed (non-fatal): {e}")
        try:
            from search.services.setfit_classifier import get_setfit_classifier
            get_setfit_classifier()
            logger.info("Search: SetFit classifier pre-warmed")
        except Exception as e:
            logger.warning(f"Search pre-warm (SetFit) failed (non-fatal): {e}")
