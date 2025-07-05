import os
import re
import sys
import bibtexparser
from urllib.parse import urlparse, unquote
import shutil

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

# --- MATH FIXERS ---
def fix_math_notation(md):
    # Block math: $$...$$ => \\[ ... \\]
    md = re.sub(r'\$\$(.+?)\$\$', r'\\[\1\\]', md, flags=re.DOTALL)
    # Inline math: $...$ => \\( ... \\)
    # Avoid replacing already-correct \\( ... \\)
    md = re.sub(r'(?<!\\)\$(.+?)\$', r'\\( \1 \\)', md)
    return md

# --- BIBTEX HANDLING ---
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

def bib_entry_to_string(entry):
    bib = f"@{entry['ENTRYTYPE']}{{{entry['ID']},\n"
    for k, v in entry.items():
        if k not in ['ENTRYTYPE', 'ID']:
            bib += f"  {k} = {{{v}}},\n"
    bib = bib.rstrip(',\n') + "\n}\n\n"
    return bib

# --- MAIN SCRIPT ---
def main(md_path):
    bib_path = get_bib_path_from_md(md_path)
    with open(md_path, 'r') as f:
        md = f.read()
    md = fix_math_notation(md)

    # --- IMAGE MOVING LOGIC ---
    # Determine post-folder from markdown filename and parent directory
    md_abs_path = os.path.abspath(md_path)
    md_dir = os.path.dirname(md_abs_path)
    md_base = os.path.basename(md_path)
    parent_dir = os.path.basename(md_dir)
    # Check if parent_dir matches YYYY-MM-DD-title
    m = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)$', parent_dir)
    if m:
        # Use images/blog/title/name-of-the-file/
        title = m.group(2)
        post_folder = os.path.join(title, md_base.replace('.md', ''))
    else:
        # Fallback to previous logic
        post_folder = md_base.replace('.md', '')
    images_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'blog'))
    post_image_dir = os.path.join(images_root, post_folder)
    os.makedirs(post_image_dir, exist_ok=True)

    # Find <img src=...> and ![alt](...) images
    img_tag_pattern = r'<img[^>]+src=["\"]([^"\"]+)["\"]'
    md_img_pattern = r'!\[[^\]]*\]\(([^)]+)\)'
    img_paths = re.findall(img_tag_pattern, md)
    img_paths += re.findall(md_img_pattern, md)
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
        key = None
        if url in url_to_key:
            key = url_to_key[url]
        elif text.lower() in title_to_key:
            key = title_to_key[text.lower()]
        if key:
            link_to_bib[url] = key
            continue
        # Prompt for BibTeX key and title, allow skip
        parsed = urlparse(url)
        domain = parsed.netloc.split('.')[-2] if '.' in parsed.netloc else parsed.netloc
        year = re.search(r'(20\d{2})', url)
        year = year.group(1) if year else 'xxxx'
        titleword = re.sub(r'[^a-zA-Z0-9]', '', text.split()[0].lower()) if text else 'ref'
        suggested_key = f"{domain}{year}{titleword}"
        print(f"[INFO] External link found: {url}")
        print(f"Suggested BibTeX key: {suggested_key}")
        bib = input(f"Enter BibTeX key for this link (or press Enter to use suggested, or type 'skip' to skip): ")
        if bib.strip().lower() == 'skip':
            print(f"[SKIP] Skipped BibTeX entry and citation for: {url}")
            continue
        # if not bib.strip():
        #     bib = suggested_key
        #     if not text.strip() or text == "here":
        #         suggested_title = suggest_title_from_url(url)
        #         text = input(f"Enter a title for {url} (or press Enter to use: '{suggested_title}'): ")
        #         if not text.strip():
        #             text = suggested_title
        link_to_bib[url] = bib
        new_entry = {
            'ENTRYTYPE': 'misc',
            'ID': bib,
            'title': text,
            'url': url
        }
        bib_database.entries.append(new_entry)
        new_bib_entries.append(new_entry)
        print(f"[INFO] Added new BibTeX entry: {bib}")

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