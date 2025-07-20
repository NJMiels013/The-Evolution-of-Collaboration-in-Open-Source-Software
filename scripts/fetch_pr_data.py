
import os
import time
import json
import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv
from requests.exceptions import ChunkedEncodingError, ConnectionError

# --- LOAD CONFIGURATION ---
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise EnvironmentError("Please set your GITHUB_TOKEN environment variable.")

HEADERS = {"Authorization": f"token " + GITHUB_TOKEN}
START_DATE = datetime(2018, 1, 1)
END_DATE = datetime(2023, 12, 31)
PER_PAGE = 100

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
                time.sleep(10 * (attempt + 1))
            elif response.status_code == 200:
                return response.json()
            else:
                print(f"Unexpected error {response.status_code} on {url}")
                break
        except (ChunkedEncodingError, ConnectionError) as e:
            print(f"{type(e).__name__} on {url}. Retry {attempt + 1}/{retries}...")
            time.sleep(10 * (attempt + 1))
    return None


def extract_users(items):
    return list({item.get("user", {}).get("login") for item in items if item.get("user")})

def fetch_all_pull_requests(repo):
    data_dir = f"data/raw/{repo.replace('/', '_')}"
    os.makedirs(data_dir, exist_ok=True)
    jsonl_path = os.path.join(data_dir, "checkpoint_data.jsonl")
    state_path = os.path.join(data_dir, "checkpoint_state.json")

    # Resume from last page
    page = 1
    if os.path.exists(state_path):
        with open(state_path, "r") as f:
            state = json.load(f)
            page = state.get("last_completed_page", 1) + 1

    start_time = time.time()
    skipped_pages = []

    with open(jsonl_path, "a", encoding="utf-8") as jsonl_file, tqdm(desc=f"Fetching PRs for {repo}", initial=page - 1) as pbar:
        while True:
            url = f"https://api.github.com/repos/{repo}/pulls?state=all&sort=created&direction=asc&per_page=100&page={page}"
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

                pr_data = {
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
                }

                jsonl_file.write(json.dumps(pr_data) + "\n")
                jsonl_file.flush()
                time.sleep(0.3)

            with open(state_path, "w") as f:
                json.dump({"last_completed_page": page}, f)

            page += 1
            pbar.update(1)

    print(f"Finished fetching PRs from {repo}")
    print(f"Total runtime: {(time.time() - start_time)/60:.2f} minutes")
    print(f"Skipped pages: {skipped_pages}")
    return jsonl_path, data_dir

def convert_jsonl_to_csv(jsonl_path, csv_path):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f]
    df = pd.json_normalize(lines)
    df.to_csv(csv_path, index=False)
    print(f"Converted to CSV: {csv_path}")

# --- MAIN ---
if __name__ == "__main__":
    repos = ["kubernetes/kubernetes", "pytorch/pytorch", "apache/spark", "scikit-learn/scikit-learn"]
    for repo in repos:
        print(f"\n--- Processing repository: {repo} ---")
        jsonl_path, data_dir = fetch_all_pull_requests(repo)
        csv_path = os.path.join(data_dir, f"{repo.replace('/', '_')}_prs_2018_2023.csv")
        convert_jsonl_to_csv(jsonl_path, csv_path)
        print(f"--- Done with {repo} ---")
