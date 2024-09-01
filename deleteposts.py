import requests
from datetime import datetime, timezone
import pytz
import jwt
import time

# Ghost Admin API configuration
API_URL = "https://sacredhindu.com/ghost/api/admin/"
ADMIN_API_KEY = "66cf3aa22fd6260249df98cb:85c76d4994f52ed095fd3a4c919933a35ee57f29c8830a24f798265702a85d2d"  # Replace with your actual Admin API key

# Date range for deletion (inclusive)
START_DATE = datetime(2023, 9, 8, tzinfo=timezone.utc)
END_DATE = datetime(2023, 10, 29, tzinfo=timezone.utc)

# Helper function to generate JWT token
def generate_token():
    id, secret = ADMIN_API_KEY.split(':')
    iat = int(time.time())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
    payload = {
        'iat': iat,
        'exp': iat + 300,
        'aud': '/admin/'
    }
    return jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)

# Helper function to make authenticated requests
def make_request(endpoint, method="GET", json=None):
    headers = {
        "Authorization": f"Ghost {generate_token()}",
        "Content-Type": "application/json"
    }
    url = API_URL + endpoint
    print(f"Making {method} request to: {url}")
    try:
        response = requests.request(method, url, headers=headers, json=json)
        print(f"Response status code: {response.status_code}")
        if response.content:
            print(f"Response content: {response.text[:500]}...")  # Print first 500 characters of response
        response.raise_for_status()
        return response.json() if response.content else None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        raise

# Function to get all posts within the date range
def get_posts_in_range():
    posts = []
    page = 1
    while True:
        try:
            data = make_request(f"posts/?page={page}&limit=100")
            if not data or 'posts' not in data:
                break
            for post in data['posts']:
                post_date = datetime.fromisoformat(post['created_at'].replace('Z', '+00:00'))
                if START_DATE <= post_date <= END_DATE:
                    posts.append(post)
                elif post_date < START_DATE:
                    return posts  # Posts are ordered by date, so we can stop here
            if len(data['posts']) < 100:
                break
            page += 1
        except Exception as e:
            print(f"Error fetching posts on page {page}: {e}")
            break
    return posts

# Function to delete a post
def delete_post(post_id):
    try:
        response = make_request(f"posts/{post_id}", method="DELETE")
        if response is None:  # Successful deletion with no content
            print(f"Successfully deleted post: {post_id}")
            return True
    except Exception as e:
        print(f"Error deleting post {post_id}: {e}")
    return False

# Function to get all tags
def get_all_tags():
    try:
        return make_request("tags/?limit=all")['tags']
    except Exception as e:
        print(f"Error fetching tags: {e}")
        return []

# Function to delete a tag
def delete_tag(tag_id):
    try:
        response = make_request(f"tags/{tag_id}", method="DELETE")
        if response is None:  # Successful deletion with no content
            print(f"Successfully deleted tag: {tag_id}")
            return True
    except Exception as e:
        print(f"Error deleting tag {tag_id}: {e}")
    return False

# Main execution
if __name__ == "__main__":
    try:
        # Delete posts
        posts = get_posts_in_range()
        print(f"Found {len(posts)} posts to delete.")
        successful_deletions = 0
        for i, post in enumerate(posts, 1):
            if delete_post(post['id']):
                successful_deletions += 1
            print(f"Progress: {i}/{len(posts)} posts processed")
        
        # Delete unused tags
        tags = get_all_tags()
        unused_tags = []
        for tag in tags:
            if 'count' in tag and 'posts' in tag['count']:
                if tag['count']['posts'] == 0:
                    unused_tags.append(tag)
            else:
                print(f"Warning: Tag {tag['id']} does not have expected 'count' property. Skipping.")
        
        print(f"Found {len(unused_tags)} unused tags to delete.")
        successful_tag_deletions = 0
        for i, tag in enumerate(unused_tags, 1):
            if delete_tag(tag['id']):
                successful_tag_deletions += 1
            print(f"Progress: {i}/{len(unused_tags)} tags processed")

        print(f"Successfully deleted {successful_deletions} out of {len(posts)} posts.")
        print(f"Successfully deleted {successful_tag_deletions} out of {len(unused_tags)} unused tags.")
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        import traceback
        traceback.print_exc()