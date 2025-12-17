import numpy as np
from django.core.management.base import BaseCommand
from django.db import transaction
from node2vec import Node2Vec
import networkx as nx
from sklearn.cluster import HDBSCAN
from trade_data.models import CompanyEmbedding, ProductEmbedding

class Command(BaseCommand):
    help = 'Generates GNN embeddings and clusters from pre-built graphs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fast',
            action='store_true',
            help='Use faster parameters (less accurate but 5x faster)',
        )

    def handle(self, *args, **options):
        fast_mode = options.get('fast', False)
        
        
        if fast_mode:
            self.stdout.write(self.style.WARNING("Running in FAST mode (reduced accuracy, 5x faster)"))
            DIMENSIONS = 32
            WALK_LENGTH = 10
            NUM_WALKS = 30
            WORKERS = 1
        else:
            
            DIMENSIONS = 64   
            WALK_LENGTH = 30  
            NUM_WALKS = 200   
            WORKERS = 4
        
        
        
        
        G_cp = nx.read_graphml("company_product_graph.graphml")
        G_cc = nx.read_graphml("buyer_seller_graph.graphml")

        G_company = nx.compose(G_cp, G_cc)
        self.stdout.write(f"       Combined company graph: {G_company.number_of_nodes()} nodes, {G_company.number_of_edges()} edges")

        
        self.stdout.write(self.style.HTTP_INFO(f"[2/8] Generating random walks (walks={NUM_WALKS}, length={WALK_LENGTH})..."))
        node2vec = Node2Vec(G_company, dimensions=DIMENSIONS, walk_length=WALK_LENGTH, num_walks=NUM_WALKS, workers=WORKERS, quiet=True)
        
        
        self.stdout.write(self.style.HTTP_INFO("[3/8] Training Word2Vec on walks..."))
        model = node2vec.fit(window=10, min_count=1, batch_words=4, workers=WORKERS)
        self.stdout.write(self.style.SUCCESS("       Word2Vec training complete!"))

        self.stdout.write(self.style.HTTP_INFO("[4/8] Extracting company embeddings..."))
        companies = [n for n in G_company.nodes() if not n.startswith("product_") and not n.startswith("country_")]
        embeddings = {}
        pagerank = nx.pagerank(G_cc, weight='weight') if G_cc.number_of_edges() > 0 else {}
        degree = dict(G_cc.degree())

        for company in companies:
            if company in model.wv:
                embeddings[company] = model.wv[company].tolist()
            else:
                embeddings[company] = np.random.rand(DIMENSIONS).tolist()
        self.stdout.write(f"       Extracted embeddings for {len(companies)} companies")

        
        self.stdout.write(self.style.HTTP_INFO("[5/8] Clustering companies (HDBSCAN)..."))
        embedding_matrix = np.array([embeddings[c] for c in companies])
        clusterer = HDBSCAN(min_cluster_size=5, metric='euclidean')
        cluster_labels = clusterer.fit_predict(embedding_matrix)

        TAGS = ["Bulk Trader", "High Growth", "Price Aggressive", "Emerging", "Regional Aggregator", "Commodity Specialist"]
        company_tags = {}
        for i, company in enumerate(companies):
            label = cluster_labels[i]
            company_tags[company] = TAGS[label % len(TAGS)] if label != -1 else "Other"
        self.stdout.write(f"       Assigned {len(set(cluster_labels))} clusters")

        
        self.stdout.write(self.style.HTTP_INFO("[6/8] Saving company embeddings to database..."))
        with transaction.atomic():
            CompanyEmbedding.objects.all().delete()
            for company in companies:
                CompanyEmbedding.objects.create(
                    company_name=company,
                    embedding=embeddings[company],  
                    cluster_tag=company_tags[company],
                    pagerank=pagerank.get(company, 0.0),
                    degree=degree.get(company, 0)
                )
        self.stdout.write(self.style.SUCCESS(f"       Saved {len(companies)} company embeddings"))

        
        
        
        self.stdout.write(self.style.HTTP_INFO("[7/8] Loading Product–Product co-trade graph..."))
        G_pp = nx.read_graphml("product_co_trade_graph.graphml")
        products = [n for n in G_pp.nodes() if n.startswith("product_")]
        self.stdout.write(f"       Product graph: {G_pp.number_of_nodes()} nodes, {G_pp.number_of_edges()} edges")

        if G_pp.number_of_edges() == 0:
            self.stdout.write(self.style.WARNING("       No product co-trade edges - skipping product embeddings"))
            self.stdout.write(self.style.SUCCESS("\n[OK] GNN embeddings generated (companies only)!"))
            return

        self.stdout.write("       Training product Node2Vec...")
        PROD_WALKS = 30 if fast_mode else 50
        node2vec_pp = Node2Vec(G_pp, dimensions=DIMENSIONS, walk_length=15, num_walks=PROD_WALKS, workers=WORKERS, quiet=True)
        model_pp = node2vec_pp.fit(window=10, min_count=1, batch_words=4, workers=WORKERS)
        self.stdout.write(self.style.SUCCESS("       Product Word2Vec training complete!"))

        product_embeddings = {}
        for prod in products:
            if prod in model_pp.wv:
                product_embeddings[prod] = model_pp.wv[prod].tolist()
            else:
                product_embeddings[prod] = np.random.rand(DIMENSIONS).tolist()

        
        self.stdout.write(self.style.HTTP_INFO("[8/8] Clustering and saving products..."))
        if len(products) >= 5:
            product_matrix = np.array([product_embeddings[p] for p in products])
            product_clusters = HDBSCAN(min_cluster_size=3).fit_predict(product_matrix)
            PRODUCT_TAGS = ["Sugar & Derivatives", "Soy Products", "Edible Oils", "Pharma Raw Materials", "Confectionery"]
            product_tags = {}
            for i, prod in enumerate(products):
                label = product_clusters[i]
                product_tags[prod] = PRODUCT_TAGS[label % len(PRODUCT_TAGS)] if label != -1 else "Other"
        else:
            product_tags = {prod: "Other" for prod in products}

        
        from trade_data.models import ProductItem
        existing_product_ids = set(ProductItem.objects.values_list('id', flat=True))
        
        saved_count = 0
        skipped_count = 0
        with transaction.atomic():
            ProductEmbedding.objects.all().delete()
            for prod_node in products:
                prod_id = int(prod_node.split("_")[1])
                
                if prod_id not in existing_product_ids:
                    skipped_count += 1
                    continue
                ProductEmbedding.objects.create(
                    product_item_id=prod_id,
                    embedding=product_embeddings[prod_node],  
                    cluster_tag=product_tags[prod_node]
                )
                saved_count += 1
        
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"       Skipped {skipped_count} products (not in database)"))
        self.stdout.write(self.style.SUCCESS(f"       Saved {saved_count} product embeddings"))

        self.stdout.write(self.style.SUCCESS("\n[OK] GNN embeddings and clusters generated!"))
