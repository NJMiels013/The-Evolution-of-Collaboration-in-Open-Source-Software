import os
import time
import json
import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv

# --- LOAD CONFIGURATION ---
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError("Please set your GITHUB_TOKEN environment variable.")

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
REPO = "pytorch/pytorch"
START_DATE = datetime(2018, 1, 1)
END_DATE = datetime(2023, 12, 31)
PER_PAGE = 100
DATA_DIR = "data/raw"
os.makedirs(DATA_DIR, exist_ok=True)

# --- HELPERS ---
def fetch_json(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return []

def extract_users(items):
    return list({item.get("user", {}).get("login") for item in items if item.get("user")})

# --- MAIN FETCH FUNCTION ---
def fetch_all_pull_requests():
    prs = []
    page = 1
    start_time = time.time()

    with tqdm(desc="Fetching PRs") as pbar:
        while True:
            url = f"https://api.github.com/repos/{REPO}/pulls?state=all&sort=created&direction=asc&per_page={PER_PAGE}&page={page}"
            response = requests.get(url, headers=HEADERS)
            if response.status_code != 200:
                print(f"Error fetching page {page}: {response.status_code}")
                break

            batch = response.json()
            if not batch:
                break

            for pr in batch:
                created = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                if created < START_DATE or created > END_DATE:
                    continue  # Skip PRs outside the time window

                pr_number = pr["number"]
                pr_url = pr["url"]

                # Sub-requests for extra data
                commits = fetch_json(pr["commits_url"])
                comments = fetch_json(pr["comments_url"])
                reviews = fetch_json(pr["review_comments_url"])

                prs.append({
                    "pr_number": pr_number,
                    "title": pr.get("title"),
                    "state": pr.get("state"),
                    "created_at": pr.get("created_at"),
                    "closed_at": pr.get("closed_at"),
                    "merged_at": pr.get("merged_at"),
                    "author": pr.get("user", {}).get("login"),
                    "merged_by": pr.get("merged_by", {}).get("login") if pr.get("merged_by") else None,
                    "assignees": [a["login"] for a in pr.get("assignees", [])],
                    "reviewers": [r["login"] for r in pr.get("requested_reviewers", [])],
                    "commit_authors": extract_users(commits),
                    "comment_authors": extract_users(comments),
                    "review_comment_authors": extract_users(reviews)
                })

                time.sleep(0.3)

            page += 1
            pbar.update(1)

    print(f"Total PRs fetched: {len(prs)}")
    print(f"Total runtime: {(time.time() - start_time)/60:.2f} minutes")
    return prs

# --- SAVE RESULTS ---
def save_results(prs):
    json_path = os.path.join(DATA_DIR, "pytorch_prs_2018_2023.json")
    csv_path = os.path.join(DATA_DIR, "pytorch_prs_2018_2023.csv")

    # Save JSON
    with open(json_path, "w") as f:
        json.dump(prs, f, indent=2)

    # Flatten for CSV
    df = pd.json_normalize(prs)
    df.to_csv(csv_path, index=False)

    print(f"Saved {len(prs)} PRs to:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")

# --- RUN ---
if __name__ == "__main__":
    pr_data = fetch_all_pull_requests()
    save_results(pr_data)
