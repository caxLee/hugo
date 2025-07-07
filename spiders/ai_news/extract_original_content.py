#!/usr/bin/env python3

import json
import os
import glob
import re
from pathlib import Path

def extract_frontmatter(file_content):
    """Extract the frontmatter from a markdown file."""
    pattern = r'^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n'
    match = re.search(pattern, file_content, re.DOTALL)
    if match:
        return match.group(1)
    return None

def properly_escape_string(s):
    """Properly escape a string for TOML."""
    # Replace any backslashes with double backslashes
    s = s.replace('\\', '\\\\')
    # Replace any double quotes with escaped double quotes
    s = s.replace('"', '\\"')
    # Use double quotes for strings containing single quotes
    return s

def update_frontmatter(file_content, original_link, original_summary):
    """Update the frontmatter with original_link and original_summary."""
    frontmatter = extract_frontmatter(file_content)
    if frontmatter is None:
        print(f"No frontmatter found in the file")
        return file_content
    
    # Check if original_link or original_summary already exists
    if 'original_link' in frontmatter or 'original_summary' in frontmatter:
        print(f"Frontmatter already contains original_link or original_summary")
        return file_content
    
    # Add original_link and original_summary to frontmatter
    updated_frontmatter = frontmatter
    if original_link:
        escaped_link = properly_escape_string(original_link)
        updated_frontmatter += f'\noriginal_link = "{escaped_link}"'
    if original_summary:
        # Escape any special characters in the summary
        escaped_summary = properly_escape_string(original_summary)
        updated_frontmatter += f'\noriginal_summary = "{escaped_summary}"'
    
    # Replace old frontmatter with updated one
    updated_content = file_content.replace(f"+++\n{frontmatter}\n+++", f"+++\n{updated_frontmatter}\n+++", 1)
    return updated_content

def process_jsonl_and_md_files():
    """Process JSONL files and update corresponding MD files with original link and summary."""
    # Find all JSONL files in the spiders/ai_news directory
    jsonl_files = glob.glob('spiders/ai_news/*.jsonl')
    
    content_dir = Path('content/post')
    
    # Dictionary to store title -> (original_link, original_summary) mapping
    article_metadata = {}
    
    # Extract metadata from JSONL files
    for jsonl_file in jsonl_files:
        print(f"Processing JSONL file: {jsonl_file}")
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    article = json.loads(line.strip())
                    title = article.get('title', '').strip()
                    url = article.get('url', '').strip()
                    summary = article.get('summary_cn', article.get('summary', '')).strip()
                    
                    if title and (url or summary):
                        article_metadata[title] = (url, summary)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON line in {jsonl_file}")
                    continue
    
    # Find all index.md files in content directory (recursively)
    md_files = list(content_dir.glob('**/index.md'))
    print(f"Found {len(md_files)} markdown files to process")
    
    # Update markdown files with original_link and original_summary
    updated_count = 0
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from frontmatter
            frontmatter = extract_frontmatter(content)
            if frontmatter is None:
                continue
            
            title_match = re.search(r"title\s*=\s*['\"]([^'\"]+)['\"]", frontmatter)
            if not title_match:
                continue
            
            title = title_match.group(1).strip()
            
            # Find matching metadata
            if title in article_metadata:
                print(f"Found matching metadata for title: {title}")
                original_link, original_summary = article_metadata[title]
                updated_content = update_frontmatter(content, original_link, original_summary)
                
                if content != updated_content:
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    updated_count += 1
                    print(f"Updated: {md_file}")
            else:
                # Try a fuzzy match for titles with special characters
                for metadata_title in article_metadata:
                    # Normalize titles for comparison (remove special chars and lowercase)
                    norm_title = re.sub(r'[^\w\s]', '', title.lower())
                    norm_metadata_title = re.sub(r'[^\w\s]', '', metadata_title.lower())
                    
                    if norm_title and norm_metadata_title and norm_title in norm_metadata_title or norm_metadata_title in norm_title:
                        print(f"Found fuzzy match: '{title}' ~ '{metadata_title}'")
                        original_link, original_summary = article_metadata[metadata_title]
                        updated_content = update_frontmatter(content, original_link, original_summary)
                        
                        if content != updated_content:
                            with open(md_file, 'w', encoding='utf-8') as f:
                                f.write(updated_content)
                            updated_count += 1
                            print(f"Updated via fuzzy match: {md_file}")
                        break
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    print(f"Total updated files: {updated_count}")

if __name__ == "__main__":
    process_jsonl_and_md_files() 