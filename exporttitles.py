import requests
import csv
from urllib.parse import urljoin

# Ghost API configuration
API_URL = "https://healthvery.com/ghost/api/v3/content/"
API_KEY = "8b7a2fde3cc37a0d8c2789e637"

# Function to get all posts
def get_all_posts():
    all_posts = []
    page = 1
    while True:
        url = urljoin(API_URL, f"posts/?key={API_KEY}&fields=title&page={page}")
        response = requests.get(url)
        data = response.json()
        posts = data['posts']
        if not posts:
            break
        all_posts.extend(posts)
        page += 1
    return all_posts

# Function to export titles to CSV
def export_titles_to_csv(posts, filename="post_titles.csv"):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Title"])  # Header
        for post in posts:
            writer.writerow([post['title']])

# Main execution
if __name__ == "__main__":
    posts = get_all_posts()
    export_titles_to_csv(posts)
    print(f"Exported {len(posts)} post titles to post_titles.csv")