import { useEffect, useState } from 'react'

interface Props {
  onSearch: (query: string) => void
  initial?: string
}

export function SearchBar({ onSearch, initial = '' }: Props) {
  const [value, setValue] = useState(initial)

  // 防抖：停止输入 300ms 后才触发搜索
  useEffect(() => {
    const t = setTimeout(() => onSearch(value), value ? 300 : 0)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="搜索菜名、食材…"
        className="peer w-full rounded-full bg-cream border-2 border-ink/65 py-2.5 pl-11 pr-10 text-[15px] text-ink
          placeholder:text-ink-soft/55 outline-none shadow-hard-sm
          transition-[border-color,box-shadow,transform] duration-150
          hover:border-ink/85
          focus:border-accent/80 focus:shadow-hard focus:-translate-y-0.5"
      />
      <svg
        className="absolute left-3.5 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-ink-soft transition-colors peer-focus:text-accent"
        fill="none" stroke="currentColor" strokeWidth={2.4} viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.2-5.2m2.2-5.3a7.5 7.5 0 11-15 0 7.5 7.5 0 0115 0z" />
      </svg>
      {value && (
        <button
          onClick={() => setValue('')}
          aria-label="清空搜索"
          className="absolute right-2.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-ink/10 hover:bg-accent hover:text-cream text-ink-soft flex items-center justify-center text-xs transition-colors active:scale-90"
        >
          ✕
        </button>
      )}
    </div>
  )
}
