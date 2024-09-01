import requests
import os
from datetime import datetime
import jwt
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix
from annoy import AnnoyIndex

# Ghost API settings
GHOST_URL = "https://website.com/"
CONTENT_API_KEY = "content-key"
ADMIN_API_KEY = "admin-key"
API_VERSION = "v3"

# Similarity threshold
SIMILARITY_THRESHOLD = 0.8  # Adjust as needed

# Batch size for fetching posts
BATCH_SIZE = 100

def generate_admin_token():
    key_id, secret = ADMIN_API_KEY.split(':')
    iat = int(datetime.now().timestamp())

    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': key_id}
    payload = {
        'iat': iat,
        'exp': iat + 5 * 60,
        'aud': f'/v3/admin/'
    }

    return jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)

def get_posts_batch(page=1):
    url = f"{GHOST_URL}/ghost/api/{API_VERSION}/content/posts/"
    params = {
        'key': CONTENT_API_KEY,
        'limit': BATCH_SIZE,
        'page': page,
        'fields': 'id,title,html,published_at'
    }
    response = requests.get(url, params=params)
    return response.json()['posts']

def create_backup(post):
    backup_dir = "post_backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    filename = f"{backup_dir}/{post['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Title: {post['title']}\n\n")
        f.write(f"Published at: {post['published_at']}\n\n")
        f.write(post['html'])

def delete_post(post_id):
    url = f"{GHOST_URL}/ghost/api/{API_VERSION}/admin/posts/{post_id}"
    headers = {'Authorization': f'Ghost {generate_admin_token()}'}
    response = requests.delete(url, headers=headers)
    return response.status_code == 204

def find_similar_posts(posts):
    print(f"Analyzing {len(posts)} posts for similarity...")
    vectorizer = TfidfVectorizer().fit_transform([post['html'] for post in posts])
    vectors = csr_matrix(vectorizer)

    print("Building search index...")
    annoy_index = AnnoyIndex(vectors.shape[1], 'angular')
    for i in range(vectors.shape[0]):
        annoy_index.add_item(i, vectors[i].toarray()[0])
    annoy_index.build(10)  # 10 trees for better accuracy

    similar_posts = []
    total_comparisons = 0
    for i in range(len(posts)):
        nearest = annoy_index.get_nns_by_item(i, 10)  # Get top 10 nearest neighbors
        for j in nearest:
            if i != j:
                total_comparisons += 1
                similarity = 1 - annoy_index.get_distance(i, j)  # Convert distance to similarity
                if similarity > SIMILARITY_THRESHOLD:
                    similar_posts.append((posts[i], posts[j], similarity))

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1} posts... Found {len(similar_posts)} similar pairs so far.")

    print(f"Similarity analysis complete. Checked {total_comparisons} potential pairs.")
    return similar_posts

def main():
    all_posts = []
    page = 1

    # Fetch all posts
    while True:
        posts_batch = get_posts_batch(page)
        if not posts_batch:
            break
        all_posts.extend(posts_batch)
        print(f"Fetched batch {page}. Total posts: {len(all_posts)}")
        page += 1

    print(f"Fetching complete. Total posts fetched: {len(all_posts)}")

    # Find similar posts across ALL posts
    similar_posts = find_similar_posts(all_posts)

    print(f"\nFound {len(similar_posts)} pairs of similar posts.")
    print("Processing similar posts...")

    posts_deleted = 0
    for index, (post1, post2, similarity) in enumerate(similar_posts, 1):
        print(f"\nProcessing similar pair {index} of {len(similar_posts)}:")
        print(f"1. Title: {post1['title']}")
        print(f"   Published at: {post1['published_at']}")
        print(f"2. Title: {post2['title']}")
        print(f"   Published at: {post2['published_at']}")
        print(f"Similarity score: {similarity:.2f}")

        # Decide which post to keep (e.g., the older one)
        post_to_delete = post2 if post1['published_at'] < post2['published_at'] else post1
        post_to_keep = post1 if post1['published_at'] < post2['published_at'] else post2

        print(f"Creating backup of: {post_to_delete['title']}")
        create_backup(post_to_delete)

        print(f"Attempting to delete: {post_to_delete['title']}")
        if delete_post(post_to_delete['id']):
            print(f"Post deleted successfully. It was similar to: {post_to_keep['title']}")
            posts_deleted += 1
        else:
            print("Failed to delete post")

        print(f"Progress: {index}/{len(similar_posts)} pairs processed. {posts_deleted} posts deleted.")
        print("---")

    print(f"\nProcess complete. Checked {len(all_posts)} posts.")
    print(f"Found {len(similar_posts)} similar pairs.")
    print(f"Deleted {posts_deleted} posts.")

if __name__ == "__main__":
    main()