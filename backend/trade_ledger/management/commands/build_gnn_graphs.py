import pandas as pd
import networkx as nx
from datetime import timedelta
from django.core.management.base import BaseCommand
from trade_data.models import Transaction
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Builds GNN graphs for import-focused trade intelligence, including buyer-seller for link prediction.'

    def handle(self, *args, **options):
        self.stdout.write("Loading import transactions...")

        transactions = Transaction.objects.values(
            'buyer', 'seller', 'country', 'qty_mt',
            'product_item_id', 'reporting_date'
        )

        df = pd.DataFrame(list(transactions))

        if df.empty:
            self.stdout.write(self.style.ERROR("No transactions found!"))
            return

        df = df.dropna(subset=['product_item_id'])
        df['product_item_id'] = df['product_item_id'].astype(int)

        df['reporting_date'] = pd.to_datetime(df['reporting_date'])

        self.stdout.write(f"Loaded {len(df)} transactions.")

        self.stdout.write("Building Company-Product graph...")
        G_company_product = nx.Graph()

        for _, row in tqdm(df.iterrows(), total=len(df)):
            company = str(row['buyer']).strip()
            product = f"product_{row['product_item_id']}"
            weight = float(row['qty_mt']) if row['qty_mt'] else 0.0

            G_company_product.add_node(company, type="company")
            G_company_product.add_node(product, type="product")

            if G_company_product.has_edge(company, product):
                G_company_product[company][product]['weight'] += weight
            else:
                G_company_product.add_edge(company, product, weight=weight)

        nx.write_graphml(G_company_product, "company_product_graph.graphml")
        self.stdout.write("[OK] Company-Product graph saved.")

        self.stdout.write("Building Product-Product co-trade graph...")
        G_product_co = nx.Graph()
        df_sorted = df.sort_values('reporting_date')

        for company in tqdm(df['buyer'].unique()):
            company_df = df_sorted[df_sorted['buyer'] == company]
            rows = company_df.to_dict("records")

            for i in range(len(rows)):
                for j in range(i + 1, len(rows)):
                    t_i = rows[i]
                    t_j = rows[j]

                    if (t_j['reporting_date'] - t_i['reporting_date']) > timedelta(days=90):
                        break

                    p1 = f"product_{t_i['product_item_id']}"
                    p2 = f"product_{t_j['product_item_id']}"

                    if p1 == p2:
                        continue

                    G_product_co.add_node(p1, type="product")
                    G_product_co.add_node(p2, type="product")

                    if G_product_co.has_edge(p1, p2):
                        G_product_co[p1][p2]['weight'] += 1
                    else:
                        G_product_co.add_edge(p1, p2, weight=1)

        nx.write_graphml(G_product_co, "product_co_trade_graph.graphml")
        self.stdout.write("[OK] Product-Product co-trade graph saved.")

        self.stdout.write("Building Seller-Product graph...")
        G_seller_product = nx.Graph()

        for _, row in tqdm(df.iterrows(), total=len(df)):
            seller = str(row['seller']).strip()
            product = f"product_{row['product_item_id']}"
            weight = float(row['qty_mt']) if row['qty_mt'] else 0.0

            G_seller_product.add_node(seller, type="seller")
            G_seller_product.add_node(product, type="product")

            if G_seller_product.has_edge(seller, product):
                G_seller_product[seller][product]['weight'] += weight
            else:
                G_seller_product.add_edge(seller, product, weight=weight)

        nx.write_graphml(G_seller_product, "seller_product_graph.graphml")
        self.stdout.write("[OK] Seller-Product graph saved.")

        self.stdout.write("Building Buyer-Seller graph for link prediction...")
        G_buyer_seller = nx.Graph()

        for _, row in tqdm(df.iterrows(), total=len(df)):
            buyer = str(row['buyer']).strip()
            seller = str(row['seller']).strip()
            weight = float(row['qty_mt']) if row['qty_mt'] else 1.0

            G_buyer_seller.add_node(buyer, type="buyer")
            G_buyer_seller.add_node(seller, type="seller")

            if G_buyer_seller.has_edge(buyer, seller):
                G_buyer_seller[buyer][seller]['weight'] += weight
            else:
                G_buyer_seller.add_edge(buyer, seller, weight=weight)

        nx.write_graphml(G_buyer_seller, "buyer_seller_graph.graphml")
        self.stdout.write("[OK] Buyer-Seller graph saved for link prediction.")

        self.stdout.write(self.style.SUCCESS(
            "All 4 graphs built successfully! You can now use 'buyer_seller_graph.graphml' for link prediction."
        ))
