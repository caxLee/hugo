#!/usr/bin/env python3

import os
import re
from pathlib import Path

def fix_frontmatter(content):
    """修复frontmatter格式问题，特别是引号和特殊字符处理"""
    # 提取frontmatter部分
    pattern = r'^\+\+\+\s*\n(.*?)\n\+\+\+\s*\n'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print("未找到frontmatter部分")
        return content
    
    frontmatter = match.group(1)
    print("原始frontmatter:\n", frontmatter)
    
    # 检测可能存在的问题
    if re.search(r'original_summary\s*=\s*"[^"]*"', frontmatter):
        print("检测到可能有问题的original_summary字段")
    
    if re.search(r'original_link\s*=\s*"[^"]*"', frontmatter):
        print("检测到可能有问题的original_link字段")
    
    # 替换任何包含original_summary或original_link的行
    lines = frontmatter.split('\n')
    new_lines = []
    for line in lines:
        if line.strip().startswith('original_summary') or line.strip().startswith('original_link'):
            new_lines.append('original_summary = ""')
        else:
            new_lines.append(line)
    
    new_frontmatter = '\n'.join(new_lines)
    print("修复后的frontmatter:\n", new_frontmatter)
    
    # 替换修复后的frontmatter
    new_content = content.replace(
        f"+++\n{frontmatter}\n+++", 
        f"+++\n{new_frontmatter}\n+++", 
        1
    )
    
    return new_content

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
            
            # 检查是否包含原始内容字段
            if 'original_summary' in content or 'original_link' in content:
                print(f"处理文件: {md_file}")
                new_content = fix_frontmatter(content)
                
                if content != new_content:
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    fixed_count += 1
                    print(f"已修复: {md_file}")
                else:
                    print(f"文件无需修复: {md_file}")
        
        except Exception as e:
            print(f"处理 {md_file} 时出错: {e}")
    
    print(f"共修复 {fixed_count} 个文件")

if __name__ == "__main__":
    process_md_files() 