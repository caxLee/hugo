#!/usr/bin/env python3

import os
import re
from pathlib import Path

def remove_url_from_frontmatter(content):
    """Removes the 'url' field from the frontmatter."""
    pattern = r'^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content, False

    frontmatter = match.group(1)
    
    # More aggressive regex to find and remove the url line
    new_frontmatter, count = re.subn(r'^\s*url\s*=\s*.*$', '', frontmatter, flags=re.MULTILINE)

    if count > 0:
        # Remove any blank lines that might be left
        new_frontmatter = "\n".join(line for line in new_frontmatter.splitlines() if line.strip())
        new_content = content.replace(match.group(0), f"+++\n{new_frontmatter}\n+++", 1)
        return new_content, True
    
    return content, False

def process_and_clean_posts():
    """Scans all posts and removes the 'url' field from frontmatter."""
    content_dir = Path('content/post')
    md_files = list(content_dir.glob('**/index.md'))
    print(f"Found {len(md_files)} markdown files to process.")
    
    cleaned_count = 0
    for md_file in md_files:
        print(f"Checking file: {md_file}")
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, was_cleaned = remove_url_from_frontmatter(content)
            
            if was_cleaned:
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Cleaned {md_file}")
                cleaned_count += 1
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
            
    print(f"Finished cleaning. Total files cleaned: {cleaned_count}")

if __name__ == "__main__":
    process_and_clean_posts() 