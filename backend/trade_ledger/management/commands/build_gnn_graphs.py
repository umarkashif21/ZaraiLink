# trade_ledger/management/commands/build_gnn_graphs.py
import pandas as pd
import networkx as nx
from datetime import timedelta
from django.core.management.base import BaseCommand
from trade_data.models import Transaction
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Builds 5 GNN graphs from Transaction data'

    def handle(self, *args, **options):
        self.stdout.write("Loading transactions...")
        # Load all transactions into a DataFrame
        transactions = Transaction.objects.values(
            'buyer', 'seller', 'country', 'qty_mt',
            'product_item_id', 'reporting_date'
        )
        df = pd.DataFrame(list(transactions))
        
        if df.empty:
            self.stdout.write(self.style.ERROR("No transactions found!"))
            return

        # Ensure product_item_id is not null
        df = df.dropna(subset=['product_item_id'])
        df['product_item_id'] = df['product_item_id'].astype(int)

        self.stdout.write(f"Loaded {len(df)} transactions.")

        # ================================
        # 1. Company–Product Graph
        # ================================
        self.stdout.write("Building Company–Product graph...")
        G_company_product = nx.Graph()
        for _, row in tqdm(df.iterrows(), total=len(df)):
            company = row['buyer']  # for import; adjust if export needed
            product = f"product_{row['product_item_id']}"
            weight = float(row['qty_mt'])
            if G_company_product.has_edge(company, product):
                G_company_product[company][product]['weight'] += weight
            else:
                G_company_product.add_edge(company, product, weight=weight)
        nx.write_graphml(G_company_product, "company_product_graph.graphml")
        self.stdout.write("✅ Company–Product graph saved.")

        # ================================
        # 2. Product–Product Co-Trade Graph
        # ================================
        self.stdout.write("Building Product–Product co-trade graph...")
        G_product_co = nx.Graph()
        
        # Group by company and 90-day windows
        df_sorted = df.sort_values('reporting_date')
        for company in tqdm(df['buyer'].unique()):
            company_df = df_sorted[df_sorted['buyer'] == company].copy()
            for i in range(len(company_df)):
                for j in range(i + 1, len(company_df)):
                    row_i = company_df.iloc[i]
                    row_j = company_df.iloc[j]
                    if (row_j['reporting_date'] - row_i['reporting_date']) <= timedelta(days=90):
                        p1 = f"product_{int(row_i['product_item_id'])}"
                        p2 = f"product_{int(row_j['product_item_id'])}"
                        if p1 != p2:
                            if G_product_co.has_edge(p1, p2):
                                G_product_co[p1][p2]['weight'] += 1
                            else:
                                G_product_co.add_edge(p1, p2, weight=1)
                    else:
                        break  # dates are sorted, so can break early
        nx.write_graphml(G_product_co, "product_co_trade_graph.graphml")
        self.stdout.write("✅ Product–Product co-trade graph saved.")

        # ================================
        # 3. Company–Company Graph
        # ================================
        self.stdout.write("Building Company–Company graph...")
        G_company_company = nx.Graph()
        for _, row in tqdm(df.iterrows(), total=len(df)):
            buyer = row['buyer']
            seller = row['seller']
            weight = float(row['qty_mt'])
            if G_company_company.has_edge(buyer, seller):
                G_company_company[buyer][seller]['weight'] += weight
            else:
                G_company_company.add_edge(buyer, seller, weight=weight)
        nx.write_graphml(G_company_company, "company_company_graph.graphml")
        self.stdout.write("✅ Company–Company graph saved.")

        # ================================
        # 4. Company–Country Graph
        # ================================
        self.stdout.write("Building Company–Country graph...")
        G_company_country = nx.Graph()
        for _, row in tqdm(df.iterrows(), total=len(df)):
            company = row['buyer']
            country = f"country_{row['country']}"
            weight = float(row['qty_mt'])
            if G_company_country.has_edge(company, country):
                G_company_country[company][country]['weight'] += weight
            else:
                G_company_country.add_edge(company, country, weight=weight)
        nx.write_graphml(G_company_country, "company_country_graph.graphml")
        self.stdout.write("✅ Company–Country graph saved.")

        # ================================
        # 5. Product–Country Graph
        # ================================
        self.stdout.write("Building Product–Country graph...")
        G_product_country = nx.Graph()
        for _, row in tqdm(df.iterrows(), total=len(df)):
            product = f"product_{row['product_item_id']}"
            country = f"country_{row['country']}"
            weight = float(row['qty_mt'])
            if G_product_country.has_edge(product, country):
                G_product_country[product][country]['weight'] += weight
            else:
                G_product_country.add_edge(product, country, weight=weight)
        nx.write_graphml(G_product_country, "product_country_graph.graphml")
        self.stdout.write("✅ Product–Country graph saved.")

        self.stdout.write(self.style.SUCCESS("All 5 GNN graphs built successfully!"))