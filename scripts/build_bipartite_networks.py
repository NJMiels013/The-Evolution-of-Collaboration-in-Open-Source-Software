import pandas as pd
import ast
import networkx as nx
from datetime import datetime
from tqdm import tqdm
import matplotlib.pyplot as plt
import os
print(os.getcwd())

# Load cleaned PR data
df = pd.read_csv("data/pytorch_prs_clean.csv")
df["created_at"] = pd.to_datetime(df["created_at"])

# Define time slices
periods = {
    "pre_covid": ("2018-01-01", "2020-01-29"),
    "during_covid": ("2020-01-30", "2023-05-04"),
    "post_covid": ("2023-05-05", "2023-12-31")
}

# Helper: Get all contributors from a row
def extract_developers(row):
    devs = set()
    if pd.notnull(row["author_clean"]):
        devs.add(row["author_clean"])
    for field in ["commit_authors_clean", "comment_authors_clean", "review_comment_authors_clean"]:
        try:
            devs.update(ast.literal_eval(row[field]))
        except:
            continue
    return list(devs)

# Define plot function BEFORE the loop
def plot_graph(G, title, path):
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42, k=0.15)
    degrees = dict(G.degree())
    nx.draw_networkx_nodes(G, pos, node_size=[v * 3 for v in degrees.values()], node_color="skyblue", alpha=0.7)
    nx.draw_networkx_edges(G, pos, width=0.5, alpha=0.5)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    print(f"Plot saved to: {path}")

# Process each time slice
for period, (start, end) in periods.items():
    print(f"\n Building networks for: {period}")

    df_period = df[(df["created_at"] >= start) & (df["created_at"] <= end)].copy()
    print(f"PRs in this period: {len(df_period)}")

    B = nx.Graph()

    for _, row in tqdm(df_period.iterrows(), total=len(df_period), desc=f"Processing PRs ({period})"):
        pr_id = f"PR_{row['pr_number']}"
        devs = extract_developers(row)
        for dev in devs:
            B.add_node(dev, bipartite=0)
            B.add_node(pr_id, bipartite=1)
            B.add_edge(dev, pr_id)

    nx.write_graphml(B, f"data/networks/bipartite_{period}.graphml")

    dev_nodes = {n for n, d in B.nodes(data=True) if d["bipartite"] == 0}
    G = nx.bipartite.weighted_projected_graph(B, dev_nodes)
    nx.write_graphml(G, f"data/networks/developer_projected_{period}.graphml")

    plot_path = f"data/networks/plot_{period}.png"
    plot_graph(G, f"Developer Network ({period.replace('_', ' ').title()})", plot_path)

    print(f"Saved bipartite and projected graphs for {period}")

