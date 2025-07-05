import os
import re
import subprocess
import argparse
import pathlib
import datetime
import shutil
import sys
import bibtexparser
from urllib.parse import urlparse, unquote

parser = argparse.ArgumentParser()
parser.add_argument('ipynb_path', type=str)
args = parser.parse_args()


'''
Input paths
'''
this_script_dir: str = os.path.abspath(pathlib.Path(__file__).parent.resolve())
ipynb_file_name: str = os.path.basename(args.ipynb_path)
config_script_path: str = os.path.join(this_script_dir, 'nbconvert_config.py')
'''
Output paths
'''
output_abs_dir: str = os.path.abspath(pathlib.Path(args.ipynb_path).parent.resolve()) # '/Users/Desktop/_posts/YYYY-MM-DD-post-name/'
output_relative_dir: str = '/'.join(args.ipynb_path.split('/')[:-1]) # '_posts/YYYY-MM-DD-post-name/'
base_file_name_with_date_prefix: str = ipynb_file_name.lower().replace(' ', '-').replace('.ipynb', '') # 'YYYY-MM-DD-post-name'
output_image_abs_dir: str = os.path.abspath(os.path.join(this_script_dir, '..', 'images', 'blog', base_file_name_with_date_prefix))
output_image_relative_dir: str = os.path.join('images', 'blog', base_file_name_with_date_prefix)
base_file_name: str = re.sub(r'^\d{4}\-\d{2}\-\d{2}\-', '', base_file_name_with_date_prefix) # 'YYYY-MM-DD-post-name' => 'post-name'
output_markdown_abs_path: str = os.path.join(output_abs_dir, base_file_name + '.md') # '/Users/Desktop/_posts/YYYY-MM-DD-post-name/post-name.md'
jekyll_markdown_abs_path: str = os.path.join(output_abs_dir, base_file_name_with_date_prefix + '.md')  # '/Users/Desktop/_posts/YYYY-MM-DD-post-name/YYYY-MM-DD-post-name.md'

print(f"Converting {ipynb_file_name} => {os.path.basename(jekyll_markdown_abs_path)}")
subprocess.run(["jupyter", "nbconvert", args.ipynb_path, "--to", "markdown", "--config", config_script_path])

# Clean up markdown
with open(output_markdown_abs_path, 'r') as fd:
    md = fd.read()
md_clean = md

# HTML cleanup
#   Remove <style> tags
md_clean = re.sub(r'\<style scoped\>(.|\n)*\<\/style\>','', md_clean, flags=re.IGNORECASE)
#   Remove <axessubplot> tags
md_clean = re.sub(r'\<\/?axessubplot:.*\n','', md_clean, flags=re.IGNORECASE)
#   Avoid "Tag '{%' was not properly terminated with regexp" errors
idxs = [ x.start() for x in re.finditer('{%', md_clean) ] + \
        [ x.start() for x in re.finditer('%}', md_clean) ] 
        # [ x.start() for x in re.finditer('}}', md_clean) ] + \
        # [ x.start() for x in re.finditer('{{', md_clean) ]
added_offset = 0
for i in idxs:
    i += added_offset
    md_clean = md_clean[:i] + "{% raw %}" + md_clean[i:i+2] + "{% endraw %}" + md_clean[i + 2:]
    added_offset += len("{% raw %}{% endraw %}")

# Extract date from base_file_name_with_date_prefix (format: YYYY-MM-DD-post-name)
try:
    date_str = re.match(r'^(\d{4}-\d{2}-\d{2})-', base_file_name_with_date_prefix).group(1)
except Exception:
    date_str = datetime.date.today().isoformat()

# Insert YAML header for distill post
header = f'''---\nlayout: distillPost\ntitle:  {base_file_name}\ndate: {date_str}\ndescription: \n\n_styles: >\n h3, h2, h1 {{\n   padding-top: 0!important;\n }}\n\ndistill: true\nmathjax: true\nbibliography: llm.bib\n---\n\n'''

# Replace block math first to avoid double replacement
md_clean = re.sub(r'\$\$(.+?)\$\$', r'\\\[\1\\\]', md_clean, flags=re.DOTALL)
# Replace inline math, but avoid already replaced block math
md_clean = re.sub(r'(?<!\\)\$(.+?)\$', r'\\\( \1 \\\)', md_clean)

md_clean = header + md_clean

# Find and move images referenced in <img src=...> tags
img_tag_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
img_paths = re.findall(img_tag_pattern, md_clean)
img_moved = False
for img_path in img_paths:
    # Only process relative paths (not http/https)
    if img_path.startswith('http://') or img_path.startswith('https://'):
        continue
    # Try to resolve the image path relative to the notebook's directory
    abs_img_path = os.path.abspath(os.path.join(output_abs_dir, img_path))
    if os.path.isfile(abs_img_path):
        # Move the image to the new images/blog/<post-folder>/ location
        dest_path = os.path.join(output_image_abs_dir, os.path.basename(img_path))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy(abs_img_path, dest_path)
        # Update the path in the markdown to the new location
        new_img_path = f'/images/blog/{base_file_name_with_date_prefix}/{os.path.basename(img_path)}'
        md_clean = md_clean.replace(img_path, new_img_path)
        print(f"\033[94m[INFO] Moved image: {img_path} -> {new_img_path}\033[0m")
        img_moved = True
if img_moved:
    print("\033[96m[INFO] All referenced images have been moved and paths updated.\033[0m")

# --- Enhanced external link citation handling with BibTeX integration ---
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

bib_path = os.path.abspath(os.path.join(this_script_dir, '..', 'vendor', 'bibliography', 'llm.bib'))
url_to_key, title_to_key, bib_database = parse_bibtex(bib_path)

external_link_pattern_html = r'<a [^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>'
external_link_pattern_md = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
external_links = set(re.findall(external_link_pattern_html, md_clean))
external_links.update([(m[1], m[0]) for m in re.findall(external_link_pattern_md, md_clean)])

link_to_bib = {}
new_bib_entries = []

def suggest_title_from_url(url):
    parsed = urlparse(url)
    # Remove fragment and query
    path = parsed.path
    last = unquote(path.strip('/').split('/')[-1])
    # Remove trailing hashes or encoded strings
    last = re.sub(r'--[A-Za-z0-9]+$', '', last)
    # Replace dashes/underscores with spaces and title case
    title = re.sub(r'[-_]', ' ', last).title()
    # Optionally, add domain for context
    domain = parsed.netloc.split('.')[-2].capitalize() if '.' in parsed.netloc else parsed.netloc.capitalize()
    if title:
        return f"{domain}: {title}"
    return domain

for url, text in external_links:
    key = None
    # Check if URL is in bib
    if url in url_to_key:
        key = url_to_key[url]
    # Check if title is in bib
    elif text.lower() in title_to_key:
        key = title_to_key[text.lower()]
    if key:
        print(f"\033[92m[INFO] Found BibTeX entry for {url}: {key}\033[0m")
        link_to_bib[url] = key
        continue
    # Suggest a key
    parsed = urlparse(url)
    domain = parsed.netloc.split('.')[-2] if '.' in parsed.netloc else parsed.netloc
    year = re.search(r'(20\d{2})', url)
    year = year.group(1) if year else 'xxxx'
    titleword = re.sub(r'[^a-zA-Z0-9]', '', text.split()[0].lower()) if text else 'ref'
    suggested_key = f"{domain}{year}{titleword}"
    print(f"\033[93m[INFO] External link found: {url}\033[0m")
    print(f"Suggested BibTeX key: {suggested_key}")
    bib = input(f"\033[91mEnter BibTeX key for this link (or press Enter to use suggested): \033[0m")
    if not bib.strip():
        bib = suggested_key
        # Only prompt for title if using the suggested key
        if not text.strip() or text == "here":
            suggested_title = suggest_title_from_url(url)
            text = input(f"\033[91mEnter a title for {url} (or press Enter to use: '{suggested_title}'): \033[0m")
            if not text.strip():
                text = suggested_title
    link_to_bib[url] = bib
    # Create minimal BibTeX entry
    new_entry = {
        'ENTRYTYPE': 'misc',
        'ID': bib,
        'title': text,
        'url': url
    }
    bib_database.entries.append(new_entry)
    new_bib_entries.append(new_entry)
    print(f"\033[96m[INFO] Added new BibTeX entry: {bib}\033[0m")

def bib_entry_to_string(entry):
    bib = f"@{entry['ENTRYTYPE']}{{{entry['ID']},\n"
    for k, v in entry.items():
        if k not in ['ENTRYTYPE', 'ID']:
            bib += f"  {k} = {{{v}}},\n"
    bib = bib.rstrip(',\n') + "\n}\n\n"
    return bib

# Save new bib entries if any (append as raw text to preserve order)
if new_bib_entries:
    with open(bib_path, 'a') as bibfile:
        for entry in new_bib_entries:
            bibfile.write(bib_entry_to_string(entry))
    print(f"\033[92m[INFO] {len(new_bib_entries)} new BibTeX entries appended to llm.bib.\033[0m")

# Insert <d-cite> tags after links with BibTeX keys
for url, bib in link_to_bib.items():
    # HTML links
    md_clean = re.sub(
        rf'(<a [^>]*href=["\']{re.escape(url)}["\'][^>]*>.*?</a>)',
        rf'\1<d-cite key="{bib}"></d-cite>',
        md_clean
    )
    # Markdown links
    md_clean = re.sub(
        rf'(\[[^\]]+\]\({re.escape(url)}\))',
        rf'\1<d-cite key="{bib}"></d-cite>',
        md_clean
    )

with open(output_markdown_abs_path, 'w') as fd:
    fd.write(md_clean)

# Rename .md file to have 'YYYY-MM-DD' prefix that Jekyll expects for all posts
os.rename(output_markdown_abs_path, jekyll_markdown_abs_path)

print("\033[92m" + "="*60)
print("[SUCCESS] Conversion complete!")
print(f"Images for this post are stored in: \033[1mimages/blog/{base_file_name_with_date_prefix}/\033[0;92m")
print("To reference images in your markdown, use:")
print(f"  ![alt text](/images/blog/{base_file_name_with_date_prefix}/your_image.png)")
print("This path will work with Jekyll and on your deployed site.")
print("="*60 + "\033[0m")