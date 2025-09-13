export interface Article {
  id: string
  title: string
  summary: string
  content: string
  date: string
  tags?: string[]
  image?: string
  link?: string
  category: string
} 