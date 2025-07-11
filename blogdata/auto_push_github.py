import os
import subprocess
import sys
from datetime import datetime
import shutil

def run_command(command, cwd, silent=False):
    """在指定目录下运行命令并处理错误"""
    try:
        if not silent:
            print(f"▶️ 在 {cwd} 中执行: {' '.join(command)}")
        
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if not silent and result.stdout.strip():
            print(f"   输出: {result.stdout.strip()}")
        if not silent and result.stderr.strip():
            print(f"   错误输出: {result.stderr.strip()}")
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {' '.join(e.cmd)}")
        print(f"   返回码: {e.returncode}")
        if e.stdout.strip():
            print(f"   输出:\n{e.stdout.strip()}")
        if e.stderr.strip():
            print(f"   错误输出:\n{e.stderr.strip()}")
        return False, None
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        return False, None

def ensure_hugo_config(hugo_source_path):
    """确保Hugo配置文件存在"""
    config_file = os.path.join(hugo_source_path, 'hugo.yaml')
    config_toml = os.path.join(hugo_source_path, 'config.toml')
    
    # 如果配置文件不存在，创建一个基本的配置
    if not os.path.exists(config_file) and not os.path.exists(config_toml):
        print("⚠️ 未找到Hugo配置文件，创建一个基本配置...")
        
        # 创建一个最小化的hugo.yaml文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write("""baseURL: "/"
languageCode: "zh-cn"
title: "My Hugo Site"
theme: "hugo-theme-stack"

languages:
  zh-cn:
    languageName: "中文"
    weight: 1
  en:
    languageName: "English"
    weight: 2
""")
        
        print(f"✅ 已创建基本配置文件: {config_file}")
    
    # 确保content目录存在
    content_dir = os.path.join(hugo_source_path, 'content')
    if not os.path.exists(content_dir):
        os.makedirs(content_dir)
        print(f"✅ 已创建content目录: {content_dir}")
    
    # 确保themes目录存在
    themes_dir = os.path.join(hugo_source_path, 'themes')
    if not os.path.exists(themes_dir):
        os.makedirs(themes_dir)
        print(f"✅ 已创建themes目录: {themes_dir}")
    
    # 确保hugo-theme-stack主题目录存在
    theme_dir = os.path.join(themes_dir, 'hugo-theme-stack')
    if not os.path.exists(theme_dir):
        os.makedirs(theme_dir)
        # 创建一个最小化的theme.toml文件
        with open(os.path.join(theme_dir, 'theme.toml'), 'w', encoding='utf-8') as f:
            f.write("""name = "Stack"
license = "GPL-3.0-only"
description = "Card-style Hugo theme"
min_version = "0.87.0"
""")
        print(f"✅ 已创建主题目录和基本配置: {theme_dir}")

def main():
    """
    该脚本首先运行hugo构建站点, 然后在public目录中执行Git操作。
    - 在本地运行时, 它会 commit 但不会 push。
    - 在GitHub Actions中, 它会完成 commit 和 push。
    """
    # --- 智能路径和环境配置 ---
    is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    hugo_source_path = ''
    
    if is_github_actions:
        hugo_source_path = os.getenv('HUGO_PROJECT_PATH')
        if not hugo_source_path:
            print("❌ 错误: 在GitHub Actions中运行时必须设置HUGO_PROJECT_PATH环境变量")
            sys.exit(1)
        print(f"🤖 在GitHub Actions中运行, Hugo源路径: {hugo_source_path}")
    else:
        hugo_source_path = r'C:\Users\kongg\0'
        print(f"💻 在本地运行, Hugo源路径: {hugo_source_path}")
    
    public_path = os.path.join(hugo_source_path, 'public')
    temp_build_path = os.path.join(hugo_source_path, 'temp_build')
    # --- 配置结束 ---

    # --- 1. 运行Hugo构建 ---
    print("\n--- 步骤1: 构建Hugo站点 ---")
    if not os.path.isdir(hugo_source_path):
        print(f"❌ 错误: Hugo源路径不存在: {hugo_source_path}")
        sys.exit(1)
    
    # 确保Hugo配置文件和必要的目录结构存在
    ensure_hugo_config(hugo_source_path)
    
    # 构建到临时目录
    build_command = ['hugo', '--destination', temp_build_path]
    success, _ = run_command(build_command, cwd=hugo_source_path)
    if not success:
        print("❌ Hugo构建失败, 终止操作")
        sys.exit(1)
    print("✅ Hugo站点构建成功")
    
    # --- 2. 准备public目录作为Git仓库 ---
    print(f"\n--- 步骤2: 准备Git仓库 ---")
    
    if is_github_actions:
        repo_url_env = os.getenv('PAGES_REPO_URL')
        branch = os.getenv('PAGES_BRANCH', 'main')  # 默认为main分支
        token = os.getenv('GH_PAT')

        if not all([repo_url_env, token]):
            print("❌ 错误: 脚本在GitHub Actions环境中运行, 但缺少必要的环境变量。")
            print("   这是因为驱动此脚本的 GitHub Actions 工作流 (.yml 文件) 没有正确提供这些值。")
            print("   要解决此问题, 您必须在您的仓库中创建一个位于 .github/workflows/ 目录下的工作流文件 (例如 daily-run.yml)。")
            print("   该文件中运行此脚本的步骤必须包含以下 'env' 配置:")
            print("""
----------------------------------------------------------------------------------
      - name: Run Python Script
        run: python blogdata/auto_push_github.py
        env:
          PAGES_REPO_URL: ${{ secrets.PAGES_REPO_URL }}
          PAGES_BRANCH: ${{ secrets.PAGES_BRANCH }}
          GH_PAT: ${{ secrets.GH_PAT }}
          HUGO_PROJECT_PATH: ${{ github.workspace }}/hugo_source # 根据上次日志调整
          GIT_COMMIT_EMAIL: 'github-actions[bot]@users.noreply.github.com'
          GIT_COMMIT_NAME: 'github-actions[bot]'
----------------------------------------------------------------------------------
            """)
            sys.exit(1)

        # 处理仓库URL，确保格式正确
        if '/' not in repo_url_env:
            print(f"❌ 错误: PAGES_REPO_URL 格式不正确: {repo_url_env}")
            print("   应该是 'owner/repo' 格式")
            sys.exit(1)
            
        remote_url = f"https://{token}@github.com/{repo_url_env}.git"
        
        # 删除旧的public目录(如果存在)
        if os.path.isdir(public_path):
            print(f"🗑️ 删除旧的发布目录: {public_path}")
            shutil.rmtree(public_path)

        # 克隆目标仓库到public目录
        print(f"🔄 克隆仓库 {repo_url_env} (分支: {branch}) 到 {public_path}")
        clone_command = ['git', 'clone', '--depth', '1', '--branch', branch, remote_url, public_path]
        success, _ = run_command(clone_command, cwd=hugo_source_path)
        if not success:
            print("❌ 克隆仓库失败, 尝试创建新的仓库...")
            # 创建新的仓库目录
            os.makedirs(public_path, exist_ok=True)
            init_commands = [
                ['git', 'init'],
                ['git', 'checkout', '-b', branch],
                ['git', 'remote', 'add', 'origin', remote_url]
            ]
            for cmd in init_commands:
                success, _ = run_command(cmd, cwd=public_path)
                if not success:
                    print(f"❌ 初始化仓库失败: {' '.join(cmd)}")
                    sys.exit(1)
        
        # 将构建好的文件从临时目录移动到public目录
        print("🚚 移动构建文件到发布目录...")
        # 删除public目录中除了.git之外的所有内容
        for item in os.listdir(public_path):
            if item == '.git':
                continue
            item_path = os.path.join(public_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        
        # 从temp_build移动文件
        for item in os.listdir(temp_build_path):
            src_path = os.path.join(temp_build_path, item)
            dst_path = os.path.join(public_path, item)
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
        
        shutil.rmtree(temp_build_path) # 清理临时构建目录
        
    else: # 本地环境逻辑
        if not os.path.isdir(os.path.join(public_path, '.git')):
            print(f"❌ 错误: 本地运行时, {public_path} 必须是一个Git仓库。")
            print("   请手动设置: git clone <your-pages-repo> public")
            sys.exit(1)

    # --- 3. 在public目录中执行Git操作 ---
    print(f"\n--- 步骤3: 在public目录中执行Git操作 ---")
    
    if is_github_actions:
        commit_email = os.getenv('GIT_COMMIT_EMAIL', 'github-actions[bot]@users.noreply.github.com')
        commit_name = os.getenv('GIT_COMMIT_NAME', 'github-actions[bot]')
        run_command(['git', 'config', 'user.email', commit_email], cwd=public_path)
        run_command(['git', 'config', 'user.name', commit_name], cwd=public_path)

    # 添加所有更改
    print("添加更改到暂存区...")
    run_command(['git', 'add', '.'], cwd=public_path)
    
    # 检查是否有更改需要提交
    success, status_output = run_command(['git', 'status', '--porcelain'], cwd=public_path, silent=True)
    if not status_output:
        print("✅ 没有检测到更改, 无需提交")
        # 在CI环境中, 即使没有更改也应该正常退出, 而不是sys.exit(0)
        # 因为后续的步骤可能还需要执行。这里我们直接结束脚本。
        print("脚本执行完毕。")
        return
    
    # 提交更改
    commit_message = f"docs: 发布每日更新 {datetime.now().strftime('%Y-%m-%d')}"
    print(f"提交更改: {commit_message}")
    success, _ = run_command(['git', 'commit', '-m', commit_message], cwd=public_path)
    if not success:
        print("❌ 提交失败")
        sys.exit(1)
    print("✅ 提交成功")
    
    # 仅在GitHub Actions中推送
    if is_github_actions:
        print("🚀 推送到远程仓库...")
        # 分支已经在克隆时设置好, 直接推送即可
        branch = os.getenv('PAGES_BRANCH', 'main')  # 默认为main分支
        success, _ = run_command(['git', 'push', '-f', 'origin', branch], cwd=public_path)
        if success:
            print("🎉 成功推送到远程仓库!")
        else:
            print("❌ 推送失败")
            sys.exit(1)
    else:
        print("ℹ️ 在本地环境中跳过推送, 请手动执行 'git push'")

if __name__ == "__main__":
    main() 