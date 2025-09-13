'use client'

import { useRouter } from 'next/navigation'
import { Article } from '../../types/article'

export default function ArticleCard({ article }: { article: Article }) {
  const router = useRouter()

  const handleCardClick = () => {
    window.open(article.link, '_blank', 'noopener,noreferrer')
  }

  const handleTagClick = (e: React.MouseEvent, tag: string) => {
    e.stopPropagation() // 阻止事件冒泡到卡片点击
    router.push(`/tags/${encodeURIComponent(tag)}`)
  }

  return (
    <article 
      className="bg-white border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer rounded-lg overflow-hidden"
      onClick={handleCardClick}
    >
      <div className="p-8 h-full">
        <div className="flex flex-col h-full space-y-6">
          {/* Title */}
          <h2 className="text-xl font-semibold text-gray-900 leading-tight hover:text-blue-600 transition-colors">
            {article.title}
          </h2>
          
          {/* Summary */}
          {article.summary && (
            <p className="text-gray-700 leading-relaxed flex-grow text-base">
              {article.summary}
            </p>
          )}
          
          {/* Tags */}
          {article.tags && article.tags.length > 0 && (
            <div className="flex flex-wrap gap-3 pt-4">
              {article.tags
                .filter((tag: string) => tag.toLowerCase() !== 'ai' && tag !== 'AI')
                .slice(0, 3)
                .map((tag: string, index: number) => (
                <span 
                  key={index}
                  className="inline-block px-4 py-2 text-sm bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 hover:text-blue-800 transition-all duration-200 cursor-pointer font-medium hover:shadow-sm"
                  onClick={(e) => handleTagClick(e, tag)}
                  title={`查看 "${tag}" 标签的所有文章`}
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </article>
  )
} 