import re
import bibtexparser
from urllib.parse import urlparse, unquote
import os

# --- BibTeX Handling ---
def parse_bibtex(bib_path):
    with open(bib_path, 'r') as bibfile:
        bib_database = bibtexparser.load(bibfile)
    url_to_key = {}
    title_to_key = {}
    for entry in bib_database.entries:
        if 'url' in entry:
            url_to_key[entry['url']] = entry['ID']
        if 'title' in entry:
            title_to_key[entry['title'].lower()] = entry['ID']
    return url_to_key, title_to_key, bib_database

def bib_entry_to_string(entry):
    bib = f"@{entry['ENTRYTYPE']}{{{entry['ID']},\n"
    for k, v in entry.items():
        if k not in ['ENTRYTYPE', 'ID']:
            bib += f"  {k} = {{{v}}},\n"
    bib = bib.rstrip(',\n') + "\n}\n\n"
    return bib

# --- Math Notation Fixing ---
def fix_math_notation(md):
    # Block math: $$...$$ => \[ ... \]
    md = re.sub(r'\$\$(.+?)\$\$', r'\\[\1\\]', md, flags=re.DOTALL)
    # Inline math: $...$ => \( ... \)
    md = re.sub(r'(?<!\\)\$(.+?)\$', r'\\( \1 \\)', md)
    return md

# --- Title Suggestion from URL ---
def suggest_title_from_url(url):
    parsed = urlparse(url)
    path = parsed.path
    last = unquote(path.strip('/').split('/')[-1])
    last = re.sub(r'--[A-Za-z0-9]+$', '', last)
    title = re.sub(r'[-_]', ' ', last).title()
    domain = parsed.netloc.split('.')[-2].capitalize() if '.' in parsed.netloc else parsed.netloc.capitalize()
    if title:
        return f"{domain}: {title}"
    return domain

# --- Image Path Finding ---
def find_image_paths(md):
    img_tag_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    md_img_pattern = r'!\[[^\]]*\]\(([^)]+)\)'
    img_paths = set(re.findall(img_tag_pattern, md))
    img_paths.update(re.findall(md_img_pattern, md))
    return img_paths

# --- Utility for Moving Images ---
def move_images(img_paths, src_dir, dest_dir, skip_prefixes=("http://", "https://", "/images/blog/")):
    """
    Move images from src_dir to dest_dir if not remote or already in place.
    Returns a dict mapping old paths to new paths (for markdown replacement).
    """
    import shutil
    os.makedirs(dest_dir, exist_ok=True)
    moved = {}
    for img_path in img_paths:
        if any(img_path.startswith(prefix) for prefix in skip_prefixes):
            continue
        abs_img_path = os.path.abspath(os.path.join(src_dir, img_path))
        if os.path.isfile(abs_img_path):
            dest_path = os.path.join(dest_dir, os.path.basename(img_path))
            shutil.copy(abs_img_path, dest_path)
            moved[img_path] = dest_path
    return moved 