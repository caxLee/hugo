'use client'

import { useState, useEffect } from 'react'
import ArticleCard from '@/components/ArticleCard'
import FloatingHeader from '@/components/FloatingHeader'
import { Article } from '../../types/article'



export default function Home() {
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>('')

  // 获取最新可用日期作为初始日期
  useEffect(() => {
    const fetchLatestDate = async () => {
      try {
        const response = await fetch('/api/articles?action=latest')
        const data = await response.json()
        if (data.latestDate) {
          setSelectedDate(data.latestDate)
        } else {
          // 如果没有返回最新日期，尝试使用可用日期列表中的最新日期
          const datesResponse = await fetch('/api/articles?action=dates')
          const datesData = await datesResponse.json()
          if (datesData.dates && datesData.dates.length > 0) {
            // 假设日期是按降序排列的，取第一个
            setSelectedDate(datesData.dates[0])
          } else {
            // 如果都失败了，设置一个固定的回退日期
            setSelectedDate('2024-12-15')
          }
        }
      } catch (err) {
        console.error('Error fetching latest date:', err)
        // 不再回退到今天，而是使用固定的有数据的日期
        setSelectedDate('2024-12-15')
      }
    }

    fetchLatestDate()
  }, [])

  // 根据选择的日期加载文章
  useEffect(() => {
    if (!selectedDate) return

    const fetchArticles = async () => {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(`/api/articles?date=${selectedDate}`)
        const data = await response.json()
        
        if (data.error) {
          setError(data.error)
          setArticles([])
        } else {
          setArticles(data.articles || [])
        }
      } catch (err) {
        console.error('Error fetching articles:', err)
        setError('加载文章失败')
        setArticles([])
      } finally {
        setLoading(false)
      }
    }

    fetchArticles()
  }, [selectedDate])

  const handleDateChange = (date: string) => {
    setSelectedDate(date)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <FloatingHeader onDateChange={handleDateChange} currentDate={selectedDate} />
      
      {/* Main content with top padding to account for fixed header */}
      <main className="pt-16 pb-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="article-list space-y-6">
            {loading ? (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">加载中...</p>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-red-500 text-lg">{error}</p>
              </div>
            ) : articles.length > 0 ? (
              articles.map((article: Article) => (
                <ArticleCard key={article.id} article={article} />
              ))
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">该日期暂无文章</p>
                <p className="text-gray-400 text-sm mt-2">请选择其他日期查看文章</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
