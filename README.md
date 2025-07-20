# The Evolution of Collaboration in Open Source Software

This repository contains the data, code, and documentation for the Bachelor End Project (BEP) titled:

**The Evolution of Collaboration in Open Source Software: A Network Analysis of GitHub Developer Communities Before, During, and After COVID-19**

Authored by **Niels Hultermans** as part of the Joint Bachelor of Science in Data Science at Tilburg University and Eindhoven University of Technology 

## Project Summary

This study investigates how the COVID-19 pandemic affected collaboration among developers in major open-source software (OSS) projects hosted on GitHub. Using pull request (PR) data, we analyze collaboration patterns across three distinct periods:

- **Pre-COVID:** before 30 January 2020  
- **During COVID:** 30 January 2020 – 5 May 2023  
- **Post-COVID:** after 5 May 2023

We apply social network analysis to model and compare developer interactions over time.

## Analyzed Repositories

This study covers four well-known OSS repositories, each representing a different governance style:

| Repository     | Governance Model     | Coordination Style      |
|----------------|-----------------------|--------------------------|
| Kubernetes     | Hierarchical (CNCF)   | Role-based              |
| PyTorch        | Centralized (Meta AI) | Industry-driven         |
| scikit-learn   | Community-based       | Consensus-oriented      |
| Apache Spark   | Meritocratic (ASF)    | Role-evolved            |

## Research Questions

1. Did overall collaboration cohesion change during the pandemic?
2. Did individual contributor roles shift across periods?
3. Did the composition of the contributor base change over time?
4. Do governance styles influence structural change in collaboration networks?

## Methodology

1. **Data Collection:** PR data collected using GitHub REST API (2018–2023)
2. **Bot Filtering:** Static + behavioral heuristics
3. **Network Construction:** Bipartite projection to undirected developer–developer networks
4. **Metrics Computed:**
   - Global: density, clustering coefficient, modularity
   - Node-level: degree, strength, betweenness centrality
5. **Comparative Analysis:** Across projects and time periods

## Key Findings

- Collaboration cohesion (density and clustering) declined during COVID-19 and partially recovered post-pandemic.
- Core contributors in PyTorch and Kubernetes retained their roles more than in decentralized projects.
- Governance style plays a major role in network resilience and contributor retention.

## Repository Structure

```
.
├── data/                   # Cleaned and processed PR data (JSON/CSV)
├── figures/                # Generated visualizations and graphs
├── scripts/                # Python scripts and Jupyter notebooks for data collection and processing
└── README.md               # Project overview
```

## Reproducibility

All code for data retrieval, processing, network construction, and metric computation is located in the `scripts/ folder.

## Citation

If you use this work, please cite it as:

> Niels Hultermans (2025). *The Evolution of Collaboration in Open Source Software: A Network Analysis of GitHub Developer Communities Before, During, and After COVID-19*. Bachelor End Project, Tilburg University and Eindhoven University of Technology.

## Acknowledgments

Supervisors: Claudia Zucca, Gergő Bocsárdi  
Second Supervisor: Ugochukwu Orji

Special thanks to the GitHub developer communities of Kubernetes, PyTorch, scikit-learn, and Apache Spark.
