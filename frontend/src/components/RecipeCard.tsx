import type { Recipe } from '../types/recipe'

interface Props {
  recipe: Recipe
  onClick: () => void
  onFavorite: (e: React.MouseEvent) => void
}

const difficultyStyle: Record<string, string> = {
  '简单': 'bg-leaf/15 text-[#5E8A45] border-leaf/45',
  '中等': 'bg-sun/25 text-[#A97816] border-sun/70',
  '较难': 'bg-accent/12 text-accent border-accent/45',
}

export function RecipeCard({ recipe, onClick, onFavorite }: Props) {
  return (
    <article
      onClick={onClick}
      className="paper-card overflow-hidden cursor-pointer group transition-all duration-200 hover:-translate-y-1.5 hover:shadow-hard-lg active:translate-y-0 active:shadow-hard-sm animate-fade-up"
    >
      <div className="relative aspect-[2.15/1] overflow-hidden bg-paper border-b-2 border-ink/80">
        {recipe.image_url ? (
          <img
            src={recipe.image_url}
            alt={recipe.name}
            loading="lazy"
            // 菜谱卡图是 4:3 信息长图，缩略图裁取顶部「标题+插画」最有辨识度
            className="w-full h-full object-cover object-[50%_24%] transition-transform duration-500 group-hover:scale-[1.045]"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl">
            {recipe.category?.icon || '🍽️'}
          </div>
        )}
        <button
          onClick={onFavorite}
          aria-label="收藏"
          className="absolute top-2 right-2 w-9 h-9 rounded-full bg-cream/92 border-2 border-ink/65 flex items-center justify-center text-sm active:scale-90 transition-transform"
        >
          {recipe.is_favorite ? (
            <span key="fav" className="animate-pop">❤️</span>
          ) : (
            <span className="opacity-70 grayscale-[30%]">🤍</span>
          )}
        </button>
      </div>
      <div className="p-3 md:p-3.5">
        <h3 className="font-display text-[17px] md:text-lg leading-tight tracking-wide line-clamp-1">
          {recipe.name}
        </h3>
        <div className="mt-2 flex items-center gap-2 text-xs md:text-[13px] text-ink-soft">
          <span className={`px-2 py-0.5 rounded-full border ${difficultyStyle[recipe.difficulty] || 'bg-paper border-ink/20'}`}>
            {recipe.difficulty}
          </span>
          {recipe.cook_time && <span className="whitespace-nowrap">⏱ {recipe.cook_time}</span>}
          {recipe.category && <span className="ml-auto truncate opacity-80">{recipe.category.name}</span>}
        </div>
      </div>
    </article>
  )
}
