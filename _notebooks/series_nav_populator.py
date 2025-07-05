import os
import yaml
import re

import argparse

def get_posts_dir(base_dir, folder_name):
    return os.path.join(base_dir, '_posts', folder_name)

# Set up argument parser
parser = argparse.ArgumentParser(description='Process folder name for posts directory.')
parser.add_argument('folder_name', type=str, help='The folder name within _posts')

# Parse arguments
args = parser.parse_args()

POSTS_DIR = get_posts_dir('..', args.folder_name)

# Helper to read YAML front matter from a markdown file
def read_front_matter(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        raise ValueError(f'No YAML front matter found in {filepath}')
    front_matter = yaml.safe_load(match.group(1))
    body = match.group(2)
    return front_matter, body

# Helper to write YAML front matter and body back to file
def write_front_matter(filepath, front_matter, body):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('---\n')
        yaml.dump(front_matter, f, sort_keys=False, allow_unicode=True)
        f.write('---\n')
        f.write(body.lstrip('\n'))

# Gather all posts and their metadata
posts = []
for fname in os.listdir(POSTS_DIR):
    if fname.endswith('.md'):
        path = os.path.join(POSTS_DIR, fname)
        fm, _ = read_front_matter(path)
        if 'series' in fm and 'id' in fm['series']:
            posts.append({
                'id': fm['series']['id'],
                'title': fm.get('title', ''),
                'filename': fname,
                'path': path,
                'front_matter': fm
            })

# Sort posts by series.id
posts.sort(key=lambda x: x['id'])

# Add previous/next page titles
for i, post in enumerate(posts):
    prev_title = posts[i-1]['title'] if i > 0 else None
    next_title = posts[i+1]['title'] if i < len(posts)-1 else None
    # Update front matter
    if 'series' not in post['front_matter']:
        post['front_matter']['series'] = {}
    if prev_title:
        post['front_matter']['series']['previous_page_title'] = prev_title
    else:
        post['front_matter']['series'].pop('previous_page_title', None)
    if next_title:
        post['front_matter']['series']['next_page_title'] = next_title
    else:
        post['front_matter']['series'].pop('next_page_title', None)

# Write back updated files
for post in posts:
    fm, body = read_front_matter(post['path'])
    # Use the updated front matter
    write_front_matter(post['path'], post['front_matter'], body)

print('Series navigation fields populated.') 