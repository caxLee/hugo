import ArticleCard from '@/components/ArticleCard'
import FloatingHeader from '@/components/FloatingHeader'
import { Article } from '../../../../types/article'

// 模拟数据 - 根据标签筛选
const getArticlesByTag = (tag: string): Article[] => {
  const allArticles: Article[] = [
    {
      id: '1',
      title: 'OpenAI 发布 GPT-4 Turbo，性能大幅提升',
      summary: 'OpenAI 在其开发者大会上宣布了 GPT-4 Turbo 的发布，新模型在处理速度和成本效率方面都有显著改进。',
      content: 'OpenAI 在其开发者大会上宣布了 GPT-4 Turbo 的发布，新模型在处理速度和成本效率方面都有显著改进。该模型支持更长的上下文窗口，能够处理多达 128K tokens 的输入，相当于约 300 页的文本。',
      link: 'https://example.com/article1',
      date: '2024-01-15',
      category: '技术发布',
      tags: ['OpenAI', 'GPT-4', '大语言模型', '技术发布']
    },
    {
      id: '2',
      title: 'Google Bard 集成 Gemini Pro，多模态能力升级',
      summary: 'Google 宣布将其最先进的 Gemini Pro 模型集成到 Bard 中，为用户提供更强大的多模态 AI 体验。',
      content: 'Google 宣布将其最先进的 Gemini Pro 模型集成到 Bard 中，为用户提供更强大的多模态 AI 体验。新版本能够同时理解和生成文本、图像和代码，在复杂推理任务上表现出色。',
      link: 'https://example.com/article2',
      date: '2024-01-14',
      category: '产品更新',
      tags: ['Google', 'Bard', 'Gemini', '多模态AI']
    },
    {
      id: '3',
      title: 'Meta 开源 Code Llama 70B，编程能力再突破',
      summary: 'Meta 发布了 Code Llama 的 70B 参数版本，这是迄今为止最大的开源代码生成模型。',
      content: 'Meta 发布了 Code Llama 的 70B 参数版本，这是迄今为止最大的开源代码生成模型。该模型在 HumanEval 基准测试中达到了 67% 的准确率，显著超越了之前的开源模型。',
      link: 'https://example.com/article3',
      date: '2024-01-13',
      category: '开源发布',
      tags: ['Meta', 'Code Llama', '开源', '代码生成']
    }
  ]

  return allArticles.filter(article => 
    article.tags?.some(t => t.toLowerCase() === tag.toLowerCase())
  )
}

export default async function TagPage({ params }: { params: Promise<{ tag: string }> }) {
  const { tag } = await params
  const decodedTag = decodeURIComponent(tag)
  const articles = getArticlesByTag(decodedTag)

  return (
    <div className="min-h-screen bg-gray-50">
      <FloatingHeader />
      
      {/* Main content with top padding to account for fixed header */}
      <main className="pt-20 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Tag header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              标签: #{decodedTag}
            </h1>
            <p className="text-gray-600">
              找到 {articles.length} 篇相关文章
            </p>
          </div>
          
          {/* Articles list */}
          {articles.length > 0 ? (
            <div className="article-list space-y-6">
              {articles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">暂无关于 &quot;{decodedTag}&quot; 的文章</p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
} 