import { NextRequest, NextResponse } from 'next/server'
import { loadArticlesByDate, getAvailableDates, getLatestAvailableDate } from '@/lib/articleLoader'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const date = searchParams.get('date')
    const action = searchParams.get('action')

    if (action === 'dates') {
      // 获取所有可用日期
      const dates = getAvailableDates()
      return NextResponse.json({ dates })
    }

    if (action === 'latest') {
      // 获取最新可用日期
      const latestDate = getLatestAvailableDate()
      return NextResponse.json({ latestDate })
    }

    if (date) {
      // 获取指定日期的文章
      const articles = loadArticlesByDate(date)
      return NextResponse.json({ articles })
    }

    // 默认返回最新日期的文章
    const latestDate = getLatestAvailableDate()
    const articles = loadArticlesByDate(latestDate)
    return NextResponse.json({ articles, date: latestDate })

  } catch (error) {
    console.error('Error in articles API:', error)
    return NextResponse.json(
      { error: 'Failed to load articles' },
      { status: 500 }
    )
  }
} 