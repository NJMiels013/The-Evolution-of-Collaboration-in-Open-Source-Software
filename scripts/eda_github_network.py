# eda_github_network.py
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Load data
prs_path = "data/prs_jan_mar2019.csv"
bipartite_path = "data/dev_pr_bipartite_edges.csv"
projected_path = "data/dev_network_edgelist.csv"

prs_df = pd.read_csv(prs_path)
bipartite_df = pd.read_csv(bipartite_path)
projected_df = pd.read_csv(projected_path, names=["source", "target", "weight"])

# Basic PR stats
print("\n--- PR Metadata Overview ---")
print(prs_df.describe(include='all'))
print("\nMerged PRs:", prs_df['merged'].sum())

# Build bipartite graph
B = nx.Graph()
for _, row in bipartite_df.iterrows():
    B.add_edge(row['developer'], row['pr_id'])

# Build developer network
G = nx.Graph()
for _, row in projected_df.iterrows():
    G.add_edge(row['source'], row['target'], weight=row['weight'])

# Network stats
print("\n--- Developer–Developer Network Stats ---")
print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())
print("Density:", nx.density(G))
print("Connected Components:", nx.number_connected_components(G))

# Plot degree distribution
degree_sequence = [d for _, d in G.degree()]
plt.figure(figsize=(10, 6))
sns.histplot(degree_sequence, bins=30)
plt.title("Degree Distribution (Developer–Developer Network)")
plt.xlabel("Degree")
plt.ylabel("Frequency")
plt.grid(True)
plt.tight_layout()
plt.savefig("data/dev_network_degree_distribution.png")
plt.show()

# Top 10 most connected developers
degree_df = pd.DataFrame(G.degree, columns=["developer", "degree"])
print("\nTop 10 Most Connected Developers:")
print(degree_df.sort_values("degree", ascending=False).head(10))
