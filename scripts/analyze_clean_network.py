# analyze_clean_network.py
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from networkx.algorithms.community import greedy_modularity_communities

# --- Load and Clean Data ---
projected_path = "data/dev_network_edgelist.csv"
projected_df = pd.read_csv(projected_path, names=["source", "target", "weight"])
projected_df["weight"] = pd.to_numeric(projected_df["weight"], errors="coerce")


# --- Identify Bots ---
bot_keywords = ["bot", "ci", "travis", "actions"]
def is_bot(username):
    return any(kw in username.lower() for kw in bot_keywords)

# Filter out edges where either node is a bot
filtered_df = projected_df[~projected_df['source'].apply(is_bot) & ~projected_df['target'].apply(is_bot)]

# --- Build Clean Graph ---
G = nx.Graph()
for _, row in filtered_df.iterrows():
    G.add_edge(row['source'], row['target'], weight=row['weight'])

# --- Compute Centrality Metrics ---
degree_centrality = nx.degree_centrality(G)
betweenness = nx.betweenness_centrality(G, weight='weight')
eigenvector = nx.eigenvector_centrality(G, max_iter=1000)
clustering = nx.clustering(G, weight='weight')

# --- Detect Communities ---
communities = list(greedy_modularity_communities(G))
node_community_map = {}
for i, comm in enumerate(communities):
    for node in comm:
        node_community_map[node] = i

# --- Create DataFrame of Results ---
metrics_df = pd.DataFrame({
    "developer": list(G.nodes),
    "degree_centrality": [degree_centrality[n] for n in G.nodes],
    "betweenness": [betweenness[n] for n in G.nodes],
    "eigenvector": [eigenvector[n] for n in G.nodes],
    "clustering": [clustering[n] for n in G.nodes],
    "community": [node_community_map[n] for n in G.nodes]
})

# --- Save and Report ---
metrics_df.to_csv("data/developer_network_metrics.csv", index=False)

print("Top 10 developers by eigenvector centrality:")
print(metrics_df.sort_values("eigenvector", ascending=False).head(10))

# --- Plot Eigenvector Centrality Distribution ---
plt.figure(figsize=(10, 6))
sns.histplot(metrics_df['eigenvector'], bins=30, kde=True)
plt.title("Eigenvector Centrality Distribution")
plt.xlabel("Eigenvector Centrality")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("data/eigenvector_centrality_distribution.png")
plt.show()
