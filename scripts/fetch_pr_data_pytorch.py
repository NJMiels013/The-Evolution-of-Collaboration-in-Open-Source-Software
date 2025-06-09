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

HEADERS = {"Authorization": f"token " + GITHUB_TOKEN}
REPO = "pytorch/pytorch"
START_DATE = datetime(2018, 1, 1)
END_DATE = datetime(2023, 12, 31)
PER_PAGE = 100
DATA_DIR = "data/raw"
CHECKPOINT_FILE = os.path.join(DATA_DIR, "checkpoint.json")
os.makedirs(DATA_DIR, exist_ok=True)

# --- HELPERS ---
def fetch_json(url, retries=3):
    for attempt in range(retries):
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
            sleep_time = max(reset_time - int(time.time()), 60)
            print(f"Rate limit hit. Sleeping for {sleep_time / 60:.2f} minutes...")
            time.sleep(sleep_time)
        elif response.status_code in (500, 502, 503):
            print(f"Server error {response.status_code} on {url}. Retry {attempt + 1}/{retries}...")
            time.sleep(10 * (attempt + 1))  # backoff
        elif response.status_code == 200:
            return response.json()
        else:
            print(f"Unexpected error {response.status_code} on {url}")
            break
    return None  # signal that it failed

def extract_users(items):
    return list({item.get("user", {}).get("login") for item in items if item.get("user")})

def save_checkpoint(data, page):
    checkpoint_data = {
        "page": page,
        "data": data
    }
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint_data, f)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            cp = json.load(f)
        print(f"Resuming from page {cp['page']}")
        return cp["data"], cp["page"]
    return [], 1

# --- MAIN FETCH FUNCTION ---
def fetch_all_pull_requests():
    prs, page = load_checkpoint()
    start_time = time.time()
    skipped_pages = []

    with tqdm(desc="Fetching PRs") as pbar:
        while True:
            url = f"https://api.github.com/repos/{REPO}/pulls?state=all&sort=created&direction=asc&per_page={PER_PAGE}&page={page}"
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
            save_checkpoint(prs, page)

    print(f"Total PRs fetched: {len(prs)}")
    print(f"Skipped pages: {skipped_pages}")
    print(f"Total runtime: {(time.time() - start_time)/60:.2f} minutes")
    return prs

# --- SAVE RESULTS ---
def save_results(prs):
    json_path = os.path.join(DATA_DIR, "pytorch_prs_2018_2023.json")
    csv_path = os.path.join(DATA_DIR, "pytorch_prs_2018_2023.csv")

    with open(json_path, "w") as f:
        json.dump(prs, f, indent=2)

    df = pd.json_normalize(prs)
    df.to_csv(csv_path, index=False)

    print(f"Saved {len(prs)} PRs to:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")

# --- RUN ---
if __name__ == "__main__":
    pr_data = fetch_all_pull_requests()
    save_results(pr_data)
