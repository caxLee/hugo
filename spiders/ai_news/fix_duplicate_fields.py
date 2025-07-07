#!/usr/bin/env python3

import os
import re
from pathlib import Path

def fix_frontmatter(content):
    """修复frontmatter中的重复字段问题"""
    # 提取frontmatter部分
    pattern = r'^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content
    
    frontmatter = match.group(1)
    
    # 检查是否有重复的original_summary或original_link字段
    original_summary_count = frontmatter.count('original_summary')
    original_link_count = frontmatter.count('original_link')
    
    if original_summary_count > 1 or original_link_count > 1:
        print(f"检测到重复字段: original_summary: {original_summary_count}, original_link: {original_link_count}")
        
        # 删除重复的字段，只保留一个空值的字段
        lines = frontmatter.split('\n')
        unique_lines = []
        has_original_summary = False
        has_original_link = False
        
        for line in lines:
            line_strip = line.strip()
            
            if line_strip.startswith('original_summary'):
                if not has_original_summary:
                    unique_lines.append('original_summary = ""')
                    has_original_summary = True
            elif line_strip.startswith('original_link'):
                if not has_original_link:
                    unique_lines.append('original_link = ""')
                    has_original_link = True
            else:
                unique_lines.append(line)
        
        new_frontmatter = '\n'.join(unique_lines)
        
        # 替换修复后的frontmatter
        new_content = content.replace(
            f"+++\n{frontmatter}\n+++", 
            f"+++\n{new_frontmatter}\n+++", 
            1
        )
        
        return new_content
    
    return content

def process_md_files():
    """处理所有markdown文件"""
    content_dir = Path('content/post')
    
    # 查找所有index.md文件
    md_files = list(content_dir.glob('**/index.md'))
    print(f"找到 {len(md_files)} 个markdown文件需要处理")
    
    fixed_count = 0
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查文件内容
            if 'original_summary' in content or 'original_link' in content:
                new_content = fix_frontmatter(content)
                
                if content != new_content:
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    fixed_count += 1
                    print(f"已修复: {md_file}")
        
        except Exception as e:
            print(f"处理 {md_file} 时出错: {e}")
    
    print(f"共修复 {fixed_count} 个文件")

if __name__ == "__main__":
    process_md_files() 