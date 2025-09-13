import { getArticles } from '../../../../lib/data'
import { Article } from '../../../../types/article'
import Link from 'next/link'
import Image from 'next/image'
import { notFound } from 'next/navigation'

interface ArticlePageProps {
  params: Promise<{ id: string }>
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const { id } = await params
  const articles = await getArticles()
  const article = articles.find((a: Article) => a.id === id)

  if (!article) {
    notFound()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <Link href="/" className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">AI新闻</h1>
            </Link>
            <nav className="hidden md:flex space-x-8">
              <Link href="/" className="text-gray-700 hover:text-gray-900">首页</Link>
              <Link href="/articles" className="text-gray-700 hover:text-gray-900">所有文章</Link>
              <Link href="/categories" className="text-gray-700 hover:text-gray-900">分类</Link>
              <Link href="/tags" className="text-gray-700 hover:text-gray-900">标签</Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Article Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumb */}
        <nav className="mb-8">
          <ol className="flex items-center space-x-2 text-sm text-gray-500">
            <li><Link href="/" className="hover:text-gray-700">首页</Link></li>
            <li>/</li>
            <li><Link href="/articles" className="hover:text-gray-700">文章</Link></li>
            <li>/</li>
            <li className="text-gray-900">{article.title}</li>
          </ol>
        </nav>

        {/* Article Header */}
        <header className="mb-8">
          <div className="flex items-center mb-4">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
              {article.category}
            </span>
            <span className="ml-3 text-gray-500">{article.date}</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            {article.title}
          </h1>
          <p className="text-xl text-gray-600 mb-6">
            {article.summary}
          </p>
          <div className="flex flex-wrap gap-2">
            {article.tags?.map((tag: string) => (
              <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                {tag}
              </span>
            ))}
          </div>
        </header>

        {/* Article Image */}
        {article.image && (
          <div className="relative h-96 mb-8 rounded-lg overflow-hidden">
            <Image
              src={`/${article.image}`}
              alt={article.title}
              fill
              className="object-cover"
            />
          </div>
        )}

        {/* Article Content */}
        <div className="prose prose-lg max-w-none mb-8">
          <div dangerouslySetInnerHTML={{ __html: article.content }} />
        </div>

        {/* Article Footer */}
        <footer className="border-t pt-8">
          <div className="flex justify-between items-center">
            <div>
              {article.link && (
                <a
                  href={article.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  查看原文 →
                </a>
              )}
            </div>
            <Link
              href="/articles"
              className="text-gray-600 hover:text-gray-900"
            >
              ← 返回文章列表
            </Link>
          </div>
        </footer>
      </main>
    </div>
  )
}

export async function generateStaticParams() {
  const articles = await getArticles()
  return articles.map((article: Article) => ({
    id: article.id,
  }))
} 