import os
import re
import sys
import shutil
from markdown_utils import (
    parse_bibtex, bib_entry_to_string, fix_math_notation, suggest_title_from_url, find_image_paths, get_or_create_bibtex_key
)

# --- CONFIG ---
def get_bib_path_from_md(md_path):
    # Parse YAML front matter for bibliography
    with open(md_path, 'r') as f:
        lines = f.readlines()
    bibfile = None
    for i, line in enumerate(lines):
        if line.strip().startswith('bibliography:'):
            bibfile = line.split(':', 1)[1].strip()
            break
        if line.strip() == '---' and i > 0:
            break  # End of front matter
    if not bibfile:
        raise ValueError('No bibliography found in front matter.')
    # Assume vendor/bibliography/ as root
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vendor', 'bibliography', bibfile)

# --- MAIN SCRIPT ---
def main(md_path):
    bib_path = get_bib_path_from_md(md_path)
    with open(md_path, 'r') as f:
        md = f.read()
    md = fix_math_notation(md)

    # --- IMAGE MOVING LOGIC ---
    md_abs_path = os.path.abspath(md_path)
    md_dir = os.path.dirname(md_abs_path)
    md_base = os.path.basename(md_path)
    parent_dir = os.path.basename(md_dir)
    m = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)$', parent_dir)
    if m:
        title = m.group(2)
        post_folder = os.path.join(title, md_base.replace('.md', ''))
    else:
        post_folder = md_base.replace('.md', '')
    images_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'blog'))
    post_image_dir = os.path.join(images_root, post_folder)
    os.makedirs(post_image_dir, exist_ok=True)

    img_paths = find_image_paths(md)
    img_moved = False
    for img_path in set(img_paths):
        if img_path.startswith('http://') or img_path.startswith('https://') or img_path.startswith('/images/blog/'):
            continue  # Skip remote or already-correct images
        abs_img_path = os.path.abspath(os.path.join(md_dir, img_path))
        if os.path.isfile(abs_img_path):
            dest_path = os.path.join(post_image_dir, os.path.basename(img_path))
            shutil.copy(abs_img_path, dest_path)
            new_img_path = f'/images/blog/{post_folder}/{os.path.basename(img_path)}'
            md = md.replace(img_path, new_img_path)
            print(f"[INFO] Moved image: {img_path} -> {new_img_path}")
            img_moved = True
    if img_moved:
        print(f"[INFO] All referenced images have been moved and paths updated.")

    url_to_key, title_to_key, bib_database = parse_bibtex(bib_path)

    # Find all hyperlinks
    external_link_pattern_html = r'<a [^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>'
    external_link_pattern_md = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    external_links = set(re.findall(external_link_pattern_html, md))
    external_links.update([(m[1], m[0]) for m in re.findall(external_link_pattern_md, md)])

    link_to_bib = {}
    new_bib_entries = []

    for url, text in external_links:
        bib, new_entry = get_or_create_bibtex_key(url, text, url_to_key, title_to_key, bib_database)
        if bib is None:
            continue
        link_to_bib[url] = bib
        if new_entry:
            new_bib_entries.append(new_entry)

    # Save new bib entries
    if new_bib_entries:
        with open(bib_path, 'a') as bibfile:
            for entry in new_bib_entries:
                bibfile.write(bib_entry_to_string(entry))
        print(f"[INFO] {len(new_bib_entries)} new BibTeX entries appended to {os.path.basename(bib_path)}.")

    # Insert <d-cite> tags after links
    for url, bib in link_to_bib.items():
        # HTML links
        md = re.sub(
            rf'(<a [^>]*href=["\']{re.escape(url)}["\'][^>]*>.*?</a>)',
            rf'\1<d-cite key="{bib}"></d-cite>',
            md
        )
        # Markdown links
        md = re.sub(
            rf'(\[[^\]]+\]\({re.escape(url)}\))',
            rf'\1<d-cite key="{bib}"></d-cite>',
            md
        )

    # Save the modified markdown
    with open(md_path, 'w') as f:
        f.write(md)
    print(f"[SUCCESS] Markdown file updated: {md_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(__file__)} <markdown_file.md>")
        sys.exit(1)
    main(sys.argv[1]) 