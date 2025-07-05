# Jupyter to Jekyll Converter

This directory contains a script to convert Jupyter notebooks (`.ipynb`) to Jekyll-compatible markdown posts.

## Usage

1. **Ensure you have the required dependencies:**
   - Python 3
   - Jupyter (with `nbconvert`)

2. **Run the conversion script:**

   ```bash
   python jupyter_to_jekyll.py <path_to_your_notebook.ipynb>
   ```
   Replace `<path_to_your_notebook.ipynb>` with the path to your Jupyter notebook file.

3. **What the script does:**
   - Converts the notebook to markdown using `nbconvert` and a custom config.
   - Cleans up the markdown for Jekyll compatibility (removes certain HTML tags, escapes Jekyll template tags).
   - Handles citations for external links: checks your BibTeX file for existing entries, prompts for a BibTeX key or auto-suggests one, and auto-suggests a title if needed.
   - Appends new BibTeX entries to `llm.bib` without changing the order of existing entries.
   - Prompts for BibTeX keys and titles in color for clarity.
   - Renames the output markdown file to the format `YYYY-MM-DD-post-title.md` as required by Jekyll.
   - Places images in an `images/blog/<post-folder>/` subdirectory at the project root.
   - Adjusts math symbols for compatibility with distill theme.

4. **Output:**
   - The converted markdown file will be in the same directory as your notebook, with the correct Jekyll post filename format.
   - Images will be in an `images/blog/<post-folder>/` folder at the project root.

## Example

```bash
python jupyter_to_jekyll.py _notebooks/2024-06-01-my-notebook.ipynb
```

This will produce:
- `_notebooks/2024-06-01-my-notebook.md`
- `images/blog/2024-06-01-my-notebook/` (with any images from the notebook)

---

**Note:**
- The script expects the notebook filename to start with the date in `YYYY-MM-DD-` format for Jekyll posts.
- Make sure `nbconvert_config.py` is present in the same directory as the script.
- Images are referenced in the markdown as `/images/blog/<post-folder>/<image>` for compatibility with Jekyll and web serving.
- A Table of Contents is auto-generated in the summary field for easy navigation.
- External links are cited using `<d-cite>` tags and are cross-referenced with your BibTeX file. New entries are appended, and titles are auto-suggested if not provided.
- All prompts for user input are shown in red for visibility.

## Markdown Fixer Utility

The `markdown_fixer.py` script helps post-process your Jekyll-compatible markdown files to ensure math formatting, citation links, and image references are handled correctly.

### Usage

```bash
python markdown_fixer.py <your_markdown_file.md>
```
- Replace `<your_markdown_file.md>` with the path to your generated markdown file.

### What the script does
- **Math Notation:**
  - Converts block math from `$$...$$` to `\[ ... \]` (for distill theme compatibility).
  - Converts inline math from `$...$` to `\( ... \)` (unless already in that format).
- **Citations and External Links:**
  - Scans for all external links (both HTML `<a href=...>` and markdown `[text](url)` formats).
  - For each external link, checks your BibTeX file (as specified in the markdown front matter) for an existing entry by URL or title.
  - If not found, prompts you to enter a BibTeX key (with a suggested default) and optionally a title. You can skip any entry.
  - Appends new BibTeX entries to the bibliography file without altering the order of existing entries.
  - Inserts `<d-cite key="...">` tags after each cited link for cross-referencing.
- **Image Handling:**
  - Detects all local image references in both HTML `<img src=...>` and markdown `![alt](...)` formats.
  - Moves each local image to `images/blog/<post-folder>/` (where `<post-folder>` is derived from your markdown filename).
  - Updates the image paths in the markdown to reference the new location (e.g., `/images/blog/<post-folder>/image.png`).
  - Skips remote images and images already in the correct location.
  - Prints info messages for each image moved.
- **File Output:**
  - Overwrites the original markdown file with the updated content.
  - Prints a summary of changes and new BibTeX entries added.

### Notes
- The script expects the markdown file to have a YAML front matter with a `bibliography:` field pointing to your BibTeX file (relative to `vendor/bibliography/`).
- Prompts for BibTeX keys and titles are shown in the terminal.
- Skipped links will not be cited or added to the bibliography.
- The script requires the `bibtexparser` Python package.
