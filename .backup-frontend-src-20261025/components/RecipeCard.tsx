import type { Recipe } from '../types/recipe'

interface Props {
  recipe: Recipe
  onClick: () => void
  onFavorite: (e: React.MouseEvent) => void
}

const difficultyColor: Record<string, string> = {
  '简单': 'bg-green-100 text-green-700',
  '中等': 'bg-yellow-100 text-yellow-700',
  '较难': 'bg-red-100 text-red-700',
}

export function RecipeCard({ recipe, onClick, onFavorite }: Props) {
  return (
    <div
      onClick={onClick}
      className="bg-white rounded-2xl shadow-sm border border-orange-100 overflow-hidden cursor-pointer active:scale-[0.98] transition-transform"
    >
      <div className="relative h-36 bg-orange-50 overflow-hidden">
        {recipe.image_url ? (
          <img
            src={recipe.image_url}
            alt={recipe.name}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl">
            {recipe.category?.icon || '🍽️'}
          </div>
        )}
        <button
          onClick={onFavorite}
          className="absolute top-2 right-2 w-9 h-9 rounded-full bg-white/80 backdrop-blur flex items-center justify-center text-lg"
        >
          {recipe.is_favorite ? '❤️' : '🤍'}
        </button>
      </div>
      <div className="p-3">
        <h3 className="font-semibold text-gray-800 text-base line-clamp-2">{recipe.name}</h3>
        <div className="flex items-center gap-2 mt-1.5">
          <span className={`text-xs px-2 py-0.5 rounded-full ${difficultyColor[recipe.difficulty] || 'bg-gray-100 text-gray-600'}`}>
            {recipe.difficulty}
          </span>
          {recipe.cook_time && (
            <span className="text-xs text-gray-400">⏱ {recipe.cook_time}</span>
          )}
        </div>
      </div>
    </div>
  )
}
