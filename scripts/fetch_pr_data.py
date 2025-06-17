import os
import time
import json
import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
from requests.exceptions import ChunkedEncodingError

# --- LOAD CONFIGURATION ---
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError("Please set your GITHUB_TOKEN environment variable.")

HEADERS = {"Authorization": f"token " + GITHUB_TOKEN}
START_DATE = datetime(2018, 1, 1)
END_DATE = datetime(2023, 12, 31)
PER_PAGE = 100

# --- HELPERS ---


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 403:
                reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                sleep_time = max(reset_time - int(time.time()), 60)
                print(f"Rate limit hit. Sleeping for {sleep_time / 60:.2f} minutes...")
                time.sleep(sleep_time)
            elif response.status_code in (500, 502, 503):
                print(f"Server error {response.status_code} on {url}. Retry {attempt + 1}/{retries}...")
                time.sleep(10 * (attempt + 1))  # exponential backoff
            elif response.status_code == 200:
                return response.json()
            else:
                print(f"Unexpected error {response.status_code} on {url}")
                break
        except ChunkedEncodingError as e:
            print(f"ChunkedEncodingError on {url}. Retry {attempt + 1}/{retries}...")
            time.sleep(10 * (attempt + 1))  # backoff before retry
    return None


def extract_users(items):
    return list({item.get("user", {}).get("login") for item in items if item.get("user")})

def fetch_all_pull_requests(repo):
    data_dir = f"data/raw/{repo.replace('/', '_')}"
    os.makedirs(data_dir, exist_ok=True)
    prs = []
    page = 1
    skipped_pages = []
    start_time = time.time()

    with tqdm(desc=f"Fetching PRs for {repo}") as pbar:
        while True:
            url = f"https://api.github.com/repos/{repo}/pulls?state=all&sort=created&direction=asc&per_page={PER_PAGE}&page={page}"
            page_data = fetch_json(url)
            if page_data is None:
                print(f"Failed to fetch page {page} after retries. Skipping.")
                skipped_pages.append(page)
                page += 1
                pbar.update(1)
                continue
            if not page_data:
                break

            for pr in page_data:
                created = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                if created < START_DATE or created > END_DATE:
                    continue

                pr_number = pr["number"]

                commits = fetch_json(pr["commits_url"]) or []
                comments = fetch_json(pr["comments_url"]) or []
                reviews = fetch_json(pr["review_comments_url"]) or []

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

    print(f"Total PRs fetched from {repo}: {len(prs)}")
    print(f"Skipped pages: {skipped_pages}")
    print(f"Total runtime: {(time.time() - start_time)/60:.2f} minutes")
    return prs, data_dir

def save_results(prs, data_dir, repo):
    json_path = os.path.join(data_dir, f"{repo.replace('/', '_')}_prs_2018_2023.json")
    csv_path = os.path.join(data_dir, f"{repo.replace('/', '_')}_prs_2018_2023.csv")

    with open(json_path, "w") as f:
        json.dump(prs, f, indent=2)

    df = pd.json_normalize(prs)
    df.to_csv(csv_path, index=False)

    print(f"Saved {len(prs)} PRs to:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")

# --- MAIN ---
if __name__ == "__main__":
    repos = [
        "kubernetes/kubernetes"
    ]

    for repo in repos:
        print(f"\n--- Processing repository: {repo} ---")
        pr_data, output_dir = fetch_all_pull_requests(repo)
        save_results(pr_data, output_dir, repo)
        print(f"--- Finished processing {repo} ---\n")
