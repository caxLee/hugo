import Link from 'next/link'
import { getArticlesByCategory, getCategories } from '../../../../lib/data'
import ArticleCard from '../../../components/ArticleCard'

export default async function CategoryPage({ params }: { params: Promise<{ category: string }> }) {
  const { category: rawCategory } = await params
  const category = decodeURIComponent(rawCategory)
  const articles = getArticlesByCategory(category)

  return (
    <div>
      <div className="mb-8">
        <nav className="text-sm text-gray-500 mb-4">
          <Link href="/" className="hover:text-blue-600">首页</Link>
          <span className="mx-2">/</span>
          <span>分类: {category}</span>
        </nav>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {category} 分类
        </h1>
        <p className="text-gray-600">
          找到 {articles.length} 篇相关文章
        </p>
      </div>
      
      <div className="article-grid">
        {articles.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))}
      </div>
      
      {articles.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">该分类下暂无文章</p>
          <Link 
            href="/" 
            className="text-blue-600 hover:text-blue-800 mt-4 inline-block"
          >
            返回首页
          </Link>
        </div>
      )}
    </div>
  )
}

// 生成静态路径
export async function generateStaticParams() {
  const categories = getCategories()
  
  return categories.map((category) => ({
    category: encodeURIComponent(category),
  }))
} 