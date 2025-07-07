#!/usr/bin/env python3
import json
import os
import re
import glob
from datetime import datetime

# Base directory for posts
POST_DIR = "content/post"
# Source JSONL files
SOURCE_FILES = [
    "spiders/ai_news/jiqizhixin_articles_summarized.jsonl",
    "spiders/ai_news/mit_news_articles.jsonl"
]

# Function to extract data from JSONL files
def load_source_data():
    articles = {}
    
    for source_file in SOURCE_FILES:
        if not os.path.exists(source_file):
            print(f"Warning: Source file {source_file} not found, skipping.")
            continue
            
        with open(source_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        article = json.loads(line)
                        # Use title as the key for matching
                        title = article.get('title', '')
                        if title:
                            # Store source data with original link and summary
                            articles[title] = {
                                'original_link': article.get('url', ''),
                                'original_summary': article.get('content', '').split('\n\n')[0] if article.get('content') else ''
                            }
                    except json.JSONDecodeError:
                        print(f"Error: Could not parse JSON line in {source_file}")
                        continue
    
    return articles

# Function to update post frontmatter
def update_post_frontmatter(source_data):
    updated_count = 0
    
    # Find all post directories
    post_dirs = []
    for date_dir in glob.glob(os.path.join(POST_DIR, "*")):
        if os.path.isdir(date_dir):
            post_dirs.extend(glob.glob(os.path.join(date_dir, "*")))
    
    for post_dir in post_dirs:
        index_file = os.path.join(post_dir, "index.md")
        
        if not os.path.exists(index_file):
            continue
            
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse the frontmatter
        frontmatter_match = re.search(r'^(---|\+\+\+)\s*(.*?)\s*(---|\+\+\+)', content, re.DOTALL)
        if not frontmatter_match:
            continue
            
        frontmatter_start = frontmatter_match.group(1)
        frontmatter = frontmatter_match.group(2)
        frontmatter_end = frontmatter_match.group(3)
        
        # Extract title
        title_match = re.search(r'title\s*=\s*[\'"](.*?)[\'"]', frontmatter)
        if not title_match:
            continue
            
        title = title_match.group(1)
        
        # Try to find a matching article
        matched_article = None
        for article_title, article_data in source_data.items():
            # Exact match
            if title == article_title:
                matched_article = article_data
                break
                
            # Partial match (if the title is abbreviated in the post)
            if title in article_title or article_title in title:
                matched_article = article_data
                break
        
        # If no match found, try to find by content
        if not matched_article:
            post_content = content.split(frontmatter_end, 1)[1].strip()
            
            for article_title, article_data in source_data.items():
                # Check if first paragraph matches
                if article_data['original_summary'] and article_data['original_summary'] in post_content:
                    matched_article = article_data
                    break
        
        # If we found a match, update the frontmatter
        if matched_article:
            original_link = matched_article['original_link']
            original_summary = matched_article['original_summary']
            
            # Check if frontmatter already has these fields
            has_original_link = re.search(r'original_link\s*=', frontmatter)
            has_original_summary = re.search(r'original_summary\s*=', frontmatter)
            
            # Only update if fields don't exist
            if not has_original_link and not has_original_summary and (original_link or original_summary):
                # Add the fields to the frontmatter
                new_frontmatter = frontmatter.rstrip()
                if original_link:
                    new_frontmatter += f'\noriginal_link = "{original_link}"'
                if original_summary:
                    # Trim the summary to avoid overly long frontmatter
                    trimmed_summary = original_summary[:500] + "..." if len(original_summary) > 500 else original_summary
                    # Escape quotes
                    trimmed_summary = trimmed_summary.replace('"', '\\"')
                    new_frontmatter += f'\noriginal_summary = "{trimmed_summary}"'
                
                # Replace the old frontmatter with the new one
                new_content = content.replace(
                    f"{frontmatter_start}{frontmatter}{frontmatter_end}", 
                    f"{frontmatter_start}{new_frontmatter}{frontmatter_end}"
                )
                
                # Write the updated content back to the file
                with open(index_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
                print(f"Updated: {index_file}")
                updated_count += 1
    
    return updated_count

def main():
    print("Loading source data from JSONL files...")
    source_data = load_source_data()
    print(f"Found {len(source_data)} articles in source data.")
    
    print("Updating post frontmatter...")
    updated_count = update_post_frontmatter(source_data)
    
    print(f"Completed! Updated {updated_count} posts.")

if __name__ == "__main__":
    main() 