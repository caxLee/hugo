'use client'

import { useState, useEffect } from 'react'

interface FloatingHeaderProps {
  onDateChange?: (date: string) => void
  currentDate?: string
}

export default function FloatingHeader({ onDateChange, currentDate }: FloatingHeaderProps) {
  const [selectedDate, setSelectedDate] = useState(currentDate || '')

  useEffect(() => {
    if (currentDate) {
      setSelectedDate(currentDate)
    }
  }, [currentDate])

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = e.target.value
    setSelectedDate(newDate)
    onDateChange?.(newDate)
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white shadow-md border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center h-12">
          {/* Date Picker */}
          <div className="flex items-center space-x-2">
            <label htmlFor="date-picker" className="text-sm font-medium text-gray-700">
              日期:
            </label>
            <input
              id="date-picker"
              type="date"
              value={selectedDate}
              onChange={handleDateChange}
              className="px-2 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm"
              max={new Date().toISOString().split('T')[0]}
            />
          </div>
        </div>
      </div>
    </header>
  )
} 