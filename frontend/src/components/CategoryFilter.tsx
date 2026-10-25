import type { Category } from '../types/recipe'

interface Props {
  categories: Category[]
  selected: string
  onSelect: (name: string) => void
}

export function CategoryFilter({ categories, selected, onSelect }: Props) {
  const chip = (active: boolean) =>
    `shrink-0 px-4 py-2 rounded-full font-display text-[15px] tracking-wider transition-all border-2 min-h-[40px] ${
      active
        ? 'bg-accent text-[#FFF6E8] border-ink/80 shadow-hard-sm'
        : 'bg-cream text-ink/75 border-ink/20 hover:border-ink/45 active:translate-y-0.5'
    }`

  return (
    <div className="flex gap-2.5 overflow-x-auto pb-1.5 scrollbar-hide">
      <button onClick={() => onSelect('')} className={chip(selected === '')}>
        全部
      </button>
      {categories.map((cat) => (
        <button
          key={cat.id}
          onClick={() => onSelect(cat.name === selected ? '' : cat.name)}
          className={chip(selected === cat.name)}
        >
          {cat.icon} {cat.name}
        </button>
      ))}
    </div>
  )
}
