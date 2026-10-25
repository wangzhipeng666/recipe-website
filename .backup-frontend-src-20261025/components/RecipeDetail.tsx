import { useState } from 'react'
import type { Recipe } from '../types/recipe'

interface Props {
  recipe: Recipe
  onBack: () => void
  onFavorite: () => void
  onEdit: () => void
  onDelete: () => void
}

function getImages(recipe: Recipe): string[] {
  if (recipe.images) {
    try {
      const arr = JSON.parse(recipe.images)
      if (Array.isArray(arr) && arr.length > 0) return arr
    } catch { /* ignore */ }
  }
  return recipe.image_url ? [recipe.image_url] : []
}

export function RecipeDetail({ recipe, onBack, onFavorite, onEdit, onDelete }: Props) {
  const ingredients: string[] = JSON.parse(recipe.ingredients || '[]')
  const steps: string[] = JSON.parse(recipe.steps || '[]')
  const images = getImages(recipe)
  const [currentImg, setCurrentImg] = useState(0)
  const [showPreview, setShowPreview] = useState(false)

  return (
    <div className="min-h-screen bg-white pb-20">
      <div className="relative">
        <div className="bg-orange-50">
          {images.length > 0 ? (
            <div className="relative">
              <img
                src={images[currentImg]}
                alt={recipe.name}
                className="w-full max-h-48 sm:max-h-80 object-contain cursor-pointer"
                onClick={() => setShowPreview(true)}
              />
              {images.length > 1 && (
                <>
                  <button
                    onClick={(e) => { e.stopPropagation(); setCurrentImg((p) => (p - 1 + images.length) % images.length) }}
                    className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/30 backdrop-blur text-white flex items-center justify-center"
                  >
                    ‹
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); setCurrentImg((p) => (p + 1) % images.length) }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/30 backdrop-blur text-white flex items-center justify-center"
                  >
                    ›
                  </button>
                  <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5">
                    {images.map((_, i) => (
                      <button
                        key={i}
                        onClick={(e) => { e.stopPropagation(); setCurrentImg(i) }}
                        className={`w-2 h-2 rounded-full ${i === currentImg ? 'bg-orange-500' : 'bg-white/60'}`}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="w-full h-60 flex items-center justify-center text-6xl">
              {recipe.category?.icon || '🍽️'}
            </div>
          )}
        </div>
        <button
          onClick={onBack}
          className="absolute top-4 left-4 w-11 h-11 rounded-full bg-black/30 backdrop-blur text-white flex items-center justify-center"
        >
          ←
        </button>
        <button
          onClick={onFavorite}
          className="absolute top-4 right-4 w-11 h-11 rounded-full bg-black/30 backdrop-blur text-white flex items-center justify-center text-xl"
        >
          {recipe.is_favorite ? '❤️' : '🤍'}
        </button>
      </div>

      {images.length > 1 && (
        <div className="px-4 mt-2 flex gap-2 overflow-x-auto pb-2">
          {images.map((url, i) => (
            <button
              key={i}
              onClick={() => setCurrentImg(i)}
              className={`shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 ${i === currentImg ? 'border-orange-500' : 'border-transparent'}`}
            >
              <img src={url} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}

      <div className="px-4 pt-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-800 min-w-0">{recipe.name}</h1>
          <div className="flex gap-2 shrink-0">
            <button onClick={onEdit} className="text-sm text-orange-500 px-3 py-1.5 rounded-lg bg-orange-50 min-h-[36px]">
              编辑
            </button>
            <button onClick={onDelete} className="text-sm text-red-500 px-3 py-1.5 rounded-lg bg-red-50 min-h-[36px]">
              删除
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-3 text-sm text-gray-500">
          {recipe.category && (
            <span className="bg-orange-50 text-orange-600 px-2 py-1 rounded-full">
              {recipe.category.icon} {recipe.category.name}
            </span>
          )}
          <span className="bg-gray-50 px-2 py-1 rounded-full">{recipe.difficulty}</span>
          {recipe.cook_time && <span>⏱ {recipe.cook_time}</span>}
        </div>

        {ingredients.length > 0 && (
          <div className="mt-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">🥬 食材</h2>
            <div className="flex flex-wrap gap-2">
              {ingredients.map((item, i) => (
                <span key={i} className="bg-orange-50 text-orange-700 px-3 py-1.5 rounded-lg text-sm">
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}

        {steps.length > 0 && (
          <div className="mt-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">👨‍🍳 做法</h2>
            <div className="space-y-3">
              {steps.map((step, i) => (
                <div key={i} className="flex gap-3">
                  <div className="shrink-0 w-7 h-7 rounded-full bg-orange-500 text-white flex items-center justify-center text-sm font-medium">
                    {i + 1}
                  </div>
                  <p className="text-gray-700 leading-relaxed pt-0.5">{step}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {recipe.tips && (
          <div className="mt-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">💡 小贴士</h2>
            <p className="text-gray-600 bg-yellow-50 p-4 rounded-xl leading-relaxed">{recipe.tips}</p>
          </div>
        )}
      </div>

      {showPreview && images.length > 0 && (
        <div
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center cursor-pointer"
          onClick={() => setShowPreview(false)}
        >
          <button
            onClick={() => setShowPreview(false)}
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/20 text-white flex items-center justify-center text-xl z-10"
          >
            ✕
          </button>
          {images.length > 1 && (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); setCurrentImg((p) => (p - 1 + images.length) % images.length) }}
                className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 text-white flex items-center justify-center text-xl"
              >
                ‹
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setCurrentImg((p) => (p + 1) % images.length) }}
                className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 text-white flex items-center justify-center text-xl"
              >
                ›
              </button>
            </>
          )}
          <img
            src={images[currentImg]}
            alt={recipe.name}
            className="max-w-[90vw] max-h-[90vh] object-contain"
            onClick={(e) => e.stopPropagation()}
          />
          {images.length > 1 && (
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2">
              {images.map((_, i) => (
                <button
                  key={i}
                  onClick={(e) => { e.stopPropagation(); setCurrentImg(i) }}
                  className={`w-2.5 h-2.5 rounded-full ${i === currentImg ? 'bg-white' : 'bg-white/40'}`}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
