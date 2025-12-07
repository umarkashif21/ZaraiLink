# trade_ledger/management/commands/generate_gnn_embeddings.py
import numpy as np
from django.core.management.base import BaseCommand
from django.db import transaction
from node2vec import Node2Vec
import networkx as nx
from sklearn.cluster import HDBSCAN
from trade_data.models import CompanyEmbedding, ProductEmbedding

class Command(BaseCommand):
    help = 'Generates GNN embeddings and clusters from pre-built graphs'

    def handle(self, *args, **options):
        # ================================
        # 1. COMPANY EMBEDDINGS
        # ================================
        self.stdout.write("Loading Company–Product and Company–Company graphs...")
        G_cp = nx.read_graphml("company_product_graph.graphml")
        G_cc = nx.read_graphml("company_company_graph.graphml")

        G_company = nx.compose(G_cp, G_cc)
        self.stdout.write(f"Combined company graph: {G_company.number_of_nodes()} nodes")

        # Node2Vec
        node2vec = Node2Vec(G_company, dimensions=64, walk_length=30, num_walks=200, workers=4)
        model = node2vec.fit(window=10, min_count=1, batch_words=4)

        companies = [n for n in G_company.nodes() if not n.startswith("product_") and not n.startswith("country_")]
        embeddings = {}
        pagerank = nx.pagerank(G_cc, weight='weight') if G_cc.number_of_edges() > 0 else {}
        degree = dict(G_cc.degree())

        for company in companies:
            if company in model.wv:
                embeddings[company] = model.wv[company].tolist()  # ✅ 64-dim list
            else:
                embeddings[company] = np.random.rand(64).tolist()

        # Clustering
        self.stdout.write("Clustering companies...")
        embedding_matrix = np.array([embeddings[c] for c in companies])
        clusterer = HDBSCAN(min_cluster_size=5, metric='euclidean')
        cluster_labels = clusterer.fit_predict(embedding_matrix)

        TAGS = ["Bulk Trader", "High Growth", "Price Aggressive", "Emerging", "Regional Aggregator", "Commodity Specialist"]
        company_tags = {}
        for i, company in enumerate(companies):
            label = cluster_labels[i]
            company_tags[company] = TAGS[label % len(TAGS)] if label != -1 else "Other"

        # Save to DB — PASS LIST DIRECTLY (NO json.dumps!)
        self.stdout.write("Saving company embeddings...")
        with transaction.atomic():
            CompanyEmbedding.objects.all().delete()
            for company in companies:
                CompanyEmbedding.objects.create(
                    company_name=company,
                    embedding=embeddings[company],  # ✅ LIST, not JSON string
                    cluster_tag=company_tags[company],
                    pagerank=pagerank.get(company, 0.0),
                    degree=degree.get(company, 0)
                )

        # ================================
        # 2. PRODUCT EMBEDDINGS
        # ================================
        self.stdout.write("Loading Product–Product co-trade graph...")
        G_pp = nx.read_graphml("product_co_trade_graph.graphml")
        products = [n for n in G_pp.nodes() if n.startswith("product_")]

        if G_pp.number_of_edges() == 0:
            self.stdout.write(self.style.WARNING("No product co-trade edges — skipping product embeddings"))
            return

        node2vec_pp = Node2Vec(G_pp, dimensions=64, walk_length=20, num_walks=100, workers=4)
        model_pp = node2vec_pp.fit(window=10, min_count=1, batch_words=4)

        product_embeddings = {}
        for prod in products:
            if prod in model_pp.wv:
                product_embeddings[prod] = model_pp.wv[prod].tolist()
            else:
                product_embeddings[prod] = np.random.rand(64).tolist()

        # Clustering
        self.stdout.write("Clustering products...")
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

        # Save to DB — PASS LIST DIRECTLY
        self.stdout.write("Saving product embeddings...")
        with transaction.atomic():
            ProductEmbedding.objects.all().delete()
            for prod_node in products:
                prod_id = int(prod_node.split("_")[1])
                ProductEmbedding.objects.create(
                    product_item_id=prod_id,
                    embedding=product_embeddings[prod_node],  # ✅ LIST, not JSON string
                    cluster_tag=product_tags[prod_node]
                )

        self.stdout.write(self.style.SUCCESS("✅ GNN embeddings and clusters generated!"))