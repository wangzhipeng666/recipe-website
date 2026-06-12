import { useState } from 'react'

interface Props {
  onSearch: (query: string) => void
}

export function SearchBar({ onSearch }: Props) {
  const [value, setValue] = useState('')

  const handleChange = (v: string) => {
    setValue(v)
    onSearch(v)
  }

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        placeholder="搜索菜谱..."
        className="w-full pl-10 pr-4 py-3 rounded-xl bg-white border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300 text-gray-700 placeholder-gray-400"
      />
      <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    </div>
  )
}
