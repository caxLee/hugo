import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'
import { Article } from '../../types/article'

// 文章根目录路径
const CONTENT_PATH = path.join(process.cwd(), 'articles')

// 解析文件夹名称获取日期和序号
const parseFolderName = (folderName: string) => {
  // 格式: "01_文章标题" 或者 "01_MIT_researchers_develop_AI_tool_to_impro"
  const match = folderName.match(/^(\d+)_(.+)$/)
  if (match) {
    return {
      order: parseInt(match[1], 10),
      titleSlug: match[2]
    }
  }
  return null
}

// 转换日期格式从 "2025_08_29" 到 "2025-08-29"
const convertDateFormat = (dateStr: string): string => {
  return dateStr.replace(/_/g, '-')
}

// 从单个文章目录加载文章
const loadArticleFromDir = (dateDir: string, articleDir: string): Article | null => {
  try {
    const articlePath = path.join(CONTENT_PATH, dateDir, articleDir, 'index.md')
    
    if (!fs.existsSync(articlePath)) {
      return null
    }

    const fileContent = fs.readFileSync(articlePath, 'utf-8')
    const { data: frontmatter, content } = matter(fileContent)
    
    const parsedInfo = parseFolderName(articleDir)
    if (!parsedInfo) {
      return null
    }

    const date = convertDateFormat(dateDir)
    
    return {
      id: `${dateDir}-${parsedInfo.order}`,
      title: frontmatter.title || parsedInfo.titleSlug.replace(/_/g, ' '),
      summary: frontmatter.summary || '',
      content: content.replace(/!\[.*?\]\(.*?\)/g, '').trim(), // 移除图片markdown
      link: frontmatter.link || '',
      date: date,
      category: frontmatter.tags?.[0] || '技术资讯',
      tags: frontmatter.tags || [],
      image: frontmatter.image || ''
    }
  } catch (error) {
    console.error(`Error loading article from ${dateDir}/${articleDir}:`, error)
    return null
  }
}

// 加载指定日期的所有文章
export const loadArticlesByDate = (date: string): Article[] => {
  try {
    const dateDir = date.replace(/-/g, '_') // 转换为目录格式
    const datePath = path.join(CONTENT_PATH, dateDir)
    
    if (!fs.existsSync(datePath)) {
      return []
    }

    const articleDirs = fs.readdirSync(datePath, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name)
      .sort()

    const articles: Article[] = []
    
    for (const articleDir of articleDirs) {
      const article = loadArticleFromDir(dateDir, articleDir)
      if (article) {
        articles.push(article)
      }
    }

    return articles.sort((a, b) => {
      // 按照文件夹序号排序
      const aOrder = parseFolderName(articleDirs.find(dir => a.id.includes(dir.split('_')[0])) || '')?.order || 0
      const bOrder = parseFolderName(articleDirs.find(dir => b.id.includes(dir.split('_')[0])) || '')?.order || 0
      return aOrder - bOrder
    })
  } catch (error) {
    console.error(`Error loading articles for date ${date}:`, error)
    return []
  }
}

// 获取所有可用的日期
export const getAvailableDates = (): string[] => {
  try {
    if (!fs.existsSync(CONTENT_PATH)) {
      return []
    }

    const dateDirs = fs.readdirSync(CONTENT_PATH, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name)
      .filter(name => /^\d{4}_\d{2}_\d{2}$/.test(name))
      .map(convertDateFormat)
      .sort()
      .reverse() // 最新的日期在前

    return dateDirs
  } catch (error) {
    console.error('Error getting available dates:', error)
    return []
  }
}

// 获取最新的可用日期
export const getLatestAvailableDate = (): string => {
  const dates = getAvailableDates()
  return dates.length > 0 ? dates[0] : new Date().toISOString().split('T')[0]
} 