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

const difficultyStyle: Record<string, string> = {
  '简单': 'bg-leaf/15 text-[#5E8A45] border-leaf/45',
  '中等': 'bg-sun/25 text-[#A97816] border-sun/70',
  '较难': 'bg-accent/12 text-accent border-accent/45',
}

function SectionTitle({ icon, children }: { icon: string; children: React.ReactNode }) {
  return (
    <h2 className="font-display text-xl text-accent tracking-wider flex items-center gap-2.5">
      <span>{icon}</span>
      {children}
      <span className="flex-1 h-[3px] rounded-full bg-[repeating-linear-gradient(90deg,rgba(200,69,44,.4)_0_12px,transparent_12px_18px)]" />
    </h2>
  )
}

export function RecipeDetail({ recipe, onBack, onFavorite, onEdit, onDelete }: Props) {
  const ingredients: string[] = JSON.parse(recipe.ingredients || '[]')
  const steps: string[] = JSON.parse(recipe.steps || '[]')
  const images = getImages(recipe)
  const [currentImg, setCurrentImg] = useState(0)
  const [showPreview, setShowPreview] = useState(false)

  return (
    <div className="max-w-6xl mx-auto px-4 md:px-6 py-4 md:py-8 pb-24 md:pb-14 animate-fade-up">
      {/* 顶部操作 */}
      <div className="flex items-center justify-between gap-2 mb-9 lg:mb-8">
        <button
          onClick={onBack}
          aria-label="返回"
          className="w-11 h-11 rounded-full paper-card-tight flex items-center justify-center text-lg active:translate-y-0.5 active:shadow-none transition-transform"
        >
          ←
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={onEdit}
            className="btn-ghost !py-2 text-sm"
          >
            ✏️ 编辑
          </button>
          <button
            onClick={onDelete}
            className="btn-ghost !py-2 text-sm !text-accent !border-accent/50"
          >
            🗑 删除
          </button>
          <button
            onClick={onFavorite}
            aria-label="收藏"
            className="w-11 h-11 rounded-full paper-card-tight flex items-center justify-center text-lg active:translate-y-0.5 active:shadow-none transition-transform"
          >
            {recipe.is_favorite ? <span key="fav" className="animate-pop">❤️</span> : '🤍'}
          </button>
        </div>
      </div>

      <div className="lg:grid lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:gap-10 xl:gap-12">
        {/* 左栏：主图 + 标题（桌面吸顶） */}
        <div className="lg:sticky lg:top-[88px] lg:self-start">
          {/* 拍立得主图 */}
          <div className="relative">
            <div className="paper-card !rounded-2xl p-2.5 rotate-[-0.6deg]">
              <div className="relative overflow-hidden rounded-[12px] border-2 border-ink/15 bg-paper">
                {images.length > 0 ? (
                  <img
                    src={images[currentImg]}
                    alt={recipe.name}
                    onClick={() => setShowPreview(true)}
                    className="w-full aspect-[4/3] object-cover cursor-zoom-in"
                  />
                ) : (
                  <div className="w-full aspect-[4/3] flex items-center justify-center text-7xl">
                    {recipe.category?.icon || '🍽️'}
                  </div>
                )}
                {images.length > 1 && (
                  <>
                    <button
                      onClick={(e) => { e.stopPropagation(); setCurrentImg((p) => (p - 1 + images.length) % images.length) }}
                      className="absolute left-2.5 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-cream/85 border-2 border-ink/50 flex items-center justify-center text-lg"
                    >
                      ‹
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); setCurrentImg((p) => (p + 1) % images.length) }}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-cream/85 border-2 border-ink/50 flex items-center justify-center text-lg"
                    >
                      ›
                    </button>
                    <div className="absolute bottom-2.5 left-1/2 -translate-x-1/2 flex gap-1.5">
                      {images.map((_, i) => (
                        <button
                          key={i}
                          onClick={(e) => { e.stopPropagation(); setCurrentImg(i) }}
                          className={`w-2.5 h-2.5 rounded-full border border-ink/40 ${i === currentImg ? 'bg-accent' : 'bg-cream/80'}`}
                        />
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
            <span className="tape -top-2.5 left-8 rotate-[-6deg]" />
            <div className="seal w-14 h-14 text-2xl rotate-[7deg] absolute bottom-2 right-2">{recipe.name[0]}</div>
          </div>

          {/* 标题与信息 */}
          <div className="mt-8 lg:mt-7">
            <h1 className="font-display text-3xl md:text-4xl tracking-widest">{recipe.name}</h1>
            <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
              {recipe.category && (
                <span className="px-3 py-1 rounded-full bg-leaf/12 text-[#5E8A45] border-2 border-leaf/40">
                  {recipe.category.icon} {recipe.category.name}
                </span>
              )}
              <span className={`px-3 py-1 rounded-full border-2 ${difficultyStyle[recipe.difficulty] || 'bg-paper border-ink/20'}`}>
                ★ {recipe.difficulty}
              </span>
              {recipe.cook_time && (
                <span className="px-3 py-1 rounded-full bg-paper border-2 border-ink/20 text-ink-soft">
                  ⏱ {recipe.cook_time}
                </span>
              )}
            </div>
          </div>

          {/* 小贴士（桌面：贴在主图下方） */}
          {recipe.tips && (
            <div className="hidden lg:block mt-5 rotate-[0.5deg] bg-sun/25 border-2 dashed border-accent/45 rounded-2xl px-5 py-4">
              <p className="font-display text-accent tracking-wider mb-1">✦ 小贴士</p>
              <p className="font-hand text-xl leading-snug text-[#8A5A2B]">{recipe.tips}</p>
            </div>
          )}
        </div>

        {/* 右栏：食材 + 步骤 */}
        <div className="mt-6 lg:mt-0 space-y-4">
          {ingredients.length > 0 && (
            <section className="paper-card p-4 md:p-5">
              <SectionTitle icon="🧺">食材准备</SectionTitle>
              <div className="mt-3.5 flex flex-wrap gap-2">
                {ingredients.map((item, i) => (
                  <span
                    key={i}
                    className="px-3 py-1.5 rounded-full bg-paper border-2 border-ink/18 text-sm text-ink/90"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </section>
          )}

          {steps.length > 0 && (
            <section className="paper-card p-4 md:p-5">
              <SectionTitle icon="🍳">做法步骤</SectionTitle>
              <ol className="mt-4 space-y-4">
                {steps.map((step, i) => (
                  <li key={i} className="relative flex gap-3.5">
                    {i < steps.length - 1 && <span className="step-line" />}
                    <div className="shrink-0 z-10 w-8 h-8 rounded-full bg-sun border-[2.5px] border-ink/85 flex items-center justify-center font-display text-base">
                      {i + 1}
                    </div>
                    <p className="pt-1 leading-relaxed text-[15px] md:text-base text-ink/90">{step}</p>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {/* 小贴士（移动端：页面底部） */}
          {recipe.tips && (
            <div className="lg:hidden rotate-[0.5deg] bg-sun/25 border-2 dashed border-accent/45 rounded-2xl px-5 py-4">
              <p className="font-display text-accent tracking-wider mb-1">✦ 小贴士</p>
              <p className="font-hand text-xl leading-snug text-[#8A5A2B]">{recipe.tips}</p>
            </div>
          )}
        </div>
      </div>

      {/* 图片预览 */}
      {showPreview && images.length > 0 && (
        <div
          className="fixed inset-0 bg-ink/90 z-50 flex items-center justify-center cursor-pointer"
          onClick={() => setShowPreview(false)}
        >
          <button
            onClick={() => setShowPreview(false)}
            aria-label="关闭"
            className="absolute top-4 right-4 w-11 h-11 rounded-full bg-cream/15 border-2 border-cream/40 text-cream flex items-center justify-center text-xl z-10"
          >
            ✕
          </button>
          {images.length > 1 && (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); setCurrentImg((p) => (p - 1 + images.length) % images.length) }}
                className="absolute left-4 top-1/2 -translate-y-1/2 w-11 h-11 rounded-full bg-cream/15 border-2 border-cream/40 text-cream flex items-center justify-center text-xl"
              >
                ‹
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setCurrentImg((p) => (p + 1) % images.length) }}
                className="absolute right-4 top-1/2 -translate-y-1/2 w-11 h-11 rounded-full bg-cream/15 border-2 border-cream/40 text-cream flex items-center justify-center text-xl"
              >
                ›
              </button>
            </>
          )}
          <img
            src={images[currentImg]}
            alt={recipe.name}
            className="max-w-[92vw] max-h-[88vh] object-contain rounded-xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  )
}
