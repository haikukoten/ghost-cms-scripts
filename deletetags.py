import requests
import jwt
import datetime

# Configuration
api_url = "https://sacredhindu.com/ghost/api/admin/"
admin_api_key = "66cf3aa22fd6260249df98cb:85c76d4994f52ed095fd3a4c919933a35ee57f29c8830a24f798265702a85d2d"

# Function to generate the JWT token
def create_jwt_token():
    id, secret = admin_api_key.split(':')
    iat = int(datetime.datetime.now().timestamp())
    exp = iat + 5 * 60  # Token valid for 5 minutes
    payload = {
        'iat': iat,
        'exp': exp,
        'aud': '/v5/admin/'
    }
    token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers={'kid': id})
    return token

# Function to get all tags with pagination support
def get_all_tags():
    all_tags = []
    page = 1
    while True:
        url = f"{api_url}/tags/?limit=50&page={page}"  # Adjust limit as needed
        headers = {
            "Authorization": f"Ghost {create_jwt_token()}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tags = response.json()['tags']
            if not tags:
                break  # No more tags to fetch
            all_tags.extend(tags)
            page += 1
        else:
            raise Exception(f"Error fetching tags: {response.status_code}, {response.text}")
    return all_tags

# Function to get all posts with pagination support
def get_all_posts():
    all_posts = []
    page = 1
    while True:
        url = f"{api_url}/posts/?limit=50&page={page}"  # Adjust limit as needed
        headers = {
            "Authorization": f"Ghost {create_jwt_token()}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            posts = response.json()['posts']
            if not posts:
                break  # No more posts to fetch
            all_posts.extend(posts)
            page += 1
        else:
            raise Exception(f"Error fetching posts: {response.status_code}, {response.text}")
    return all_posts

# Function to delete a tag by ID
def delete_tag(tag_id):
    url = f"{api_url}/tags/{tag_id}/"
    headers = {
        "Authorization": f"Ghost {create_jwt_token()}"
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"Deleted tag ID {tag_id}")
    else:
        print(f"Failed to delete tag ID {tag_id}: {response.status_code}, {response.text}")

# Main function to delete unused tags
def delete_unused_tags():
    tags = get_all_tags()
    posts = get_all_posts()
    
    used_tag_ids = set()
    for post in posts:
        for tag in post.get('tags', []):
            used_tag_ids.add(tag['id'])
    
    unused_tags = [tag for tag in tags if tag['id'] not in used_tag_ids]
    
    for tag in unused_tags:
        delete_tag(tag['id'])

# Run the script
if __name__ == "__main__":
    delete_unused_tags()
