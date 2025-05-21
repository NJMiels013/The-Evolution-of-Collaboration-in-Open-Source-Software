# plot_community_network.py
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Patch

# === CONFIGURATION ===
EDGE_PATH = "data/dev_network_edgelist.csv"
METRICS_PATH = "data/developer_network_metrics.csv"
SAVE_PATH = "data/developer_network_by_community_with_legend.png"

# === LOAD DATA ===
edges_df = pd.read_csv(EDGE_PATH)
metrics_df = pd.read_csv(METRICS_PATH).set_index("developer")

# === BUILD GRAPH ===
G = nx.from_pandas_edgelist(edges_df, source="source", target="target", edge_attr="weight")

# === COLOR BY COMMUNITY ===
color_palette = sns.color_palette("tab10", n_colors=10)
community_map = {}
node_colors = []

for node in G.nodes():
    if node in metrics_df.index:
        comm = int(metrics_df.loc[node]["community"])
        community_map[comm] = color_palette[comm % 10]
        node_colors.append(color_palette[comm % 10])
    else:
        node_colors.append((0.5, 0.5, 0.5))  # Gray for unknown

# === PLOT GRAPH ===
plt.figure(figsize=(12, 10))
pos = nx.spring_layout(G, seed=42, k=0.15)
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=40)
nx.draw_networkx_edges(G, pos, alpha=0.05, width=0.2)
plt.title("Developer Network Colored by Community", fontsize=14)
plt.axis("off")

# === ADD LEGEND ===
legend_handles = [
    Patch(color=color_palette[i % 10], label=f"Community {i}")
    for i in sorted(community_map.keys())
]
plt.legend(handles=legend_handles, title="Communities", loc="upper right", fontsize=9)

plt.tight_layout()
plt.savefig(SAVE_PATH)
plt.show()
