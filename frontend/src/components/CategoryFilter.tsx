import type { Category } from '../types/recipe'

interface Props {
  categories: Category[]
  selected: string
  onSelect: (name: string) => void
}

export function CategoryFilter({ categories, selected, onSelect }: Props) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      <button
        onClick={() => onSelect('')}
        className={`shrink-0 px-4 py-2.5 rounded-full text-sm font-medium transition-colors min-h-[40px] ${
          selected === ''
            ? 'bg-orange-500 text-white'
            : 'bg-white text-gray-600 border border-orange-200 active:bg-orange-50'
        }`}
      >
        全部
      </button>
      {categories.map((cat) => (
        <button
          key={cat.id}
          onClick={() => onSelect(cat.name)}
          className={`shrink-0 px-4 py-2.5 rounded-full text-sm font-medium transition-colors min-h-[40px] ${
            selected === cat.name
              ? 'bg-orange-500 text-white'
              : 'bg-white text-gray-600 border border-orange-200 active:bg-orange-50'
          }`}
        >
          {cat.icon} {cat.name}
        </button>
      ))}
    </div>
  )
}
