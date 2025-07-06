import os
import re
import subprocess
import argparse
import pathlib
import datetime
import shutil
import sys
from markdown_utils import (
    parse_bibtex, bib_entry_to_string, fix_math_notation, suggest_title_from_url, find_image_paths, get_or_create_bibtex_key
)
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
img_paths = find_image_paths(md_clean)
img_moved = False
for img_path in set(img_paths):
    if img_path.startswith('http://') or img_path.startswith('https://'):
        continue
    abs_img_path = os.path.abspath(os.path.join(output_abs_dir, img_path))
    if os.path.isfile(abs_img_path):
        dest_path = os.path.join(output_image_abs_dir, os.path.basename(img_path))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy(abs_img_path, dest_path)
        new_img_path = f'/images/blog/{base_file_name_with_date_prefix}/{os.path.basename(img_path)}'
        md_clean = md_clean.replace(img_path, new_img_path)
        print(f"\033[94m[INFO] Moved image: {img_path} -> {new_img_path}\033[0m")
        img_moved = True
if img_moved:
    print("\033[96m[INFO] All referenced images have been moved and paths updated.\033[0m")

# --- Enhanced external link citation handling with BibTeX integration ---
def get_bib_path():
    return os.path.abspath(os.path.join(this_script_dir, '..', 'vendor', 'bibliography', 'llm.bib'))

bib_path = get_bib_path()
url_to_key, title_to_key, bib_database = parse_bibtex(bib_path)

external_link_pattern_html = r'<a [^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>'
external_link_pattern_md = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
external_links = set(re.findall(external_link_pattern_html, md_clean))
external_links.update([(m[1], m[0]) for m in re.findall(external_link_pattern_md, md_clean)])

link_to_bib = {}
new_bib_entries = []

def get_domain(url):
    parsed = urlparse(url)
    return parsed.netloc.split('.')[-2] if '.' in parsed.netloc else parsed.netloc

def get_titleword(text):
    return re.sub(r'[^a-zA-Z0-9]', '', text.split()[0].lower()) if text else 'ref'

for url, text in external_links:
    bib, new_entry = get_or_create_bibtex_key(url, text, url_to_key, title_to_key, bib_database)
    if bib is None:
        continue
    link_to_bib[url] = bib
    if new_entry:
        new_bib_entries.append(new_entry)

if new_bib_entries:
    with open(bib_path, 'a') as bibfile:
        for entry in new_bib_entries:
            bibfile.write(bib_entry_to_string(entry))
    print(f"\033[92m[INFO] {len(new_bib_entries)} new BibTeX entries appended to llm.bib.\033[0m")

for url, bib in link_to_bib.items():
    md_clean = re.sub(
        rf'(<a [^>]*href=["\']{re.escape(url)}["\'][^>]*>.*?</a>)',
        rf'\1<d-cite key="{bib}"></d-cite>',
        md_clean
    )
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