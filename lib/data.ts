import { Article } from '../types/article'
import fs from 'fs'
import path from 'path'

// 从迁移的JSON文件中加载真实文章数据
export function getArticles(): Article[] {
  try {
    const articlesPath = path.join(process.cwd(), 'lib', 'data', 'articles.json')
    const articlesData = fs.readFileSync(articlesPath, 'utf-8')
    const articles = JSON.parse(articlesData)
    
    // 按日期排序，最新的在前
    return articles.sort((a: Article, b: Article) => 
      new Date(b.date).getTime() - new Date(a.date).getTime()
    )
  } catch (error) {
    console.error('加载文章数据失败:', error)
    return []
  }
}

// 获取所有分类
export function getCategories(): string[] {
  try {
    const categoriesPath = path.join(process.cwd(), 'lib', 'data', 'categories.json')
    const categoriesData = fs.readFileSync(categoriesPath, 'utf-8')
    return JSON.parse(categoriesData)
  } catch (error) {
    console.error('加载分类数据失败:', error)
    return ['AI']
  }
}

// 获取所有标签
export function getTags(): string[] {
  try {
    const tagsPath = path.join(process.cwd(), 'lib', 'data', 'tags.json')
    const tagsData = fs.readFileSync(tagsPath, 'utf-8')
    return JSON.parse(tagsData)
  } catch (error) {
    console.error('加载标签数据失败:', error)
    return []
  }
}

// 获取网站配置
export function getSiteConfig() {
  try {
    const configPath = path.join(process.cwd(), 'lib', 'data', 'site-config.json')
    const configData = fs.readFileSync(configPath, 'utf-8')
    return JSON.parse(configData)
  } catch (error) {
    console.error('加载网站配置失败:', error)
    return {
      title: 'AI News',
      description: 'AI新闻聚合网站',
      pagination: { pagerSize: 10 }
    }
  }
}

// 根据分类筛选文章
export function getArticlesByCategory(category: string): Article[] {
  const articles = getArticles()
  return articles.filter(article => article.category === category)
}

// 根据标签筛选文章
export function getArticlesByTag(tag: string): Article[] {
  const articles = getArticles()
  return articles.filter(article => article.tags?.includes(tag))
}

// 搜索文章
export function searchArticles(query: string): Article[] {
  const articles = getArticles()
  const lowerQuery = query.toLowerCase()
  
  return articles.filter(article => 
    article.title.toLowerCase().includes(lowerQuery) ||
    article.summary.toLowerCase().includes(lowerQuery) ||
    article.tags?.some((tag: string) => tag.toLowerCase().includes(lowerQuery))
  )
}

// 获取单篇文章
export function getArticleById(id: string): Article | null {
  const articles = getArticles()
  return articles.find(article => article.id === id) || null
}

// 获取相关文章
export function getRelatedArticles(article: Article, limit = 3): Article[] {
  const articles = getArticles()
  
  // 基于标签和分类找相关文章
  const related = articles.filter(a => 
    a.id !== article.id && (
      a.category === article.category ||
      a.tags?.some((tag: string) => article.tags?.includes(tag))
    )
  )
  
  return related.slice(0, limit)
} 