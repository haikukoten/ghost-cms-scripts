import requests
import csv
from urllib.parse import urljoin

# Ghost API configuration
API_URL = "https://yourwebsite.com/ghost/api/v3/content/"
API_KEY = "content-api"
ADMIN_URL = "https://yourwebsite.com/ghost/"  # Add your Ghost admin URL here

# Function to get all posts
def get_all_posts():
    all_posts = []
    page = 1
    while True:
        url = urljoin(API_URL, f"posts/?key={API_KEY}&fields=id,title&page={page}")
        response = requests.get(url)
        data = response.json()
        posts = data['posts']
        if not posts:
            break
        all_posts.extend(posts)
        page += 1
    return all_posts

# Function to create edit link
def create_edit_link(post_id):
    return f"{ADMIN_URL}#/editor/post/{post_id}"

# Function to export titles and edit links to CSV
def export_titles_and_links_to_csv(posts, filename="post_titles_and_links.csv"):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Title", "Edit Link"])  # Header
        for post in posts:
            edit_link = create_edit_link(post['id'])
            writer.writerow([post['title'], edit_link])

# Main execution
if __name__ == "__main__":
    posts = get_all_posts()
    export_titles_and_links_to_csv(posts)
    print(f"Exported {len(posts)} post titles and edit links to post_titles_and_links.csv")