import { useState, useEffect, useCallback } from 'react'
import { api } from './api'
import type { Category, Recipe } from './types/recipe'
import { SearchBar } from './components/SearchBar'
import { CategoryFilter } from './components/CategoryFilter'
import { RecipeCard } from './components/RecipeCard'
import { RecipeDetail } from './components/RecipeDetail'
import { RecipeForm } from './components/RecipeForm'
import { ChatPage } from './components/ChatPage'

type Page = 'home' | 'detail' | 'add' | 'edit' | 'chat'

// --- Hash 路由工具 ---
interface HashState {
  page: Page
  category: string
  search: string
}

function parseHash(): HashState {
  const raw = window.location.hash.slice(1) || '/home'
  const [path, qs] = raw.split('?')
  const params = new URLSearchParams(qs || '')
  const segment = path.split('/')[1]
  const page = (['detail', 'add', 'edit', 'chat'].includes(segment) ? segment : 'home') as Page
  return {
    page,
    category: params.get('category') || '',
    search: params.get('search') || '',
  }
}

function getHashRecipeId(): number | null {
  const match = window.location.hash.match(/\/detail\/(\d+)/)
  return match ? Number(match[1]) : null
}

function buildHash(page: Page, opts?: { recipeId?: number; category?: string; search?: string }) {
  if (page === 'detail' && opts?.recipeId != null) return `#/detail/${opts.recipeId}`
  const params = new URLSearchParams()
  if (opts?.category) params.set('category', opts.category)
  if (opts?.search) params.set('search', opts.search)
  const qs = params.toString()
  return `#/${page}${qs ? `?${qs}` : ''}`
}

function App() {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const initHash = parseHash()
  const [page, setPage] = useState<Page>(initHash.page)
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null)
  const [selectedCategory, setSelectedCategory] = useState(initHash.category)
  const [searchQuery, setSearchQuery] = useState(initHash.search)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<'home' | 'favorites' | 'chat'>('home')

  // 同步 hash → state（浏览器前进/后退时）
  useEffect(() => {
    const onHashChange = () => {
      const h = parseHash()
      setPage(h.page)
      setSelectedCategory(h.category)
      setSearchQuery(h.search)
      if (h.page === 'detail') {
        const id = getHashRecipeId()
        if (id) {
          setRecipes((prev) => {
            const found = prev.find((r) => r.id === id)
            if (found) setSelectedRecipe(found)
            else api.getRecipe(id).then(setSelectedRecipe).catch(() => {})
            return prev
          })
        }
      }
    }
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  // 包装导航，同步到 hash（home 页携带 category/search）
  const navigate = (newPage: Page, recipeId?: number) => {
    setPage(newPage)
    window.location.hash = buildHash(newPage, { recipeId, category: selectedCategory, search: searchQuery })
  }

  const loadRecipes = useCallback(async () => {
    try {
      const params: any = { size: 100 }
      if (selectedCategory) params.category = selectedCategory
      if (searchQuery) params.search = searchQuery
      const res = await api.getRecipes(params)
      setRecipes(res.items)
    } catch {
      console.error('加载菜谱失败')
    } finally {
      setLoading(false)
    }
  }, [selectedCategory, searchQuery])

  const loadCategories = useCallback(async () => {
    try {
      const res = await api.getCategories()
      setCategories(res)
    } catch {
      console.error('加载分类失败')
    }
  }, [])

  useEffect(() => { loadCategories() }, [loadCategories])
  useEffect(() => { loadRecipes() }, [loadRecipes])

  // 分类/搜索变化时同步到 hash（仅首页）
  useEffect(() => {
    if (page === 'home') {
      window.location.hash = buildHash('home', { category: selectedCategory, search: searchQuery })
    }
  }, [selectedCategory, searchQuery])

  const handleToggleFavorite = async (id: number, e?: React.MouseEvent) => {
    e?.stopPropagation()
    try {
      const updated = await api.toggleFavorite(id)
      setRecipes((prev) => prev.map((r) => (r.id === id ? updated : r)))
      if (selectedRecipe?.id === id) setSelectedRecipe(updated)
    } catch {
      console.error('收藏操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定删除这个菜谱吗？')) return
    try {
      await api.deleteRecipe(id)
      setRecipes((prev) => prev.filter((r) => r.id !== id))
      navigate('home')
      setSelectedRecipe(null)
    } catch {
      alert('删除失败')
    }
  }

  if (page === 'detail' && selectedRecipe) {
    return (
      <RecipeDetail
        recipe={selectedRecipe}
        onBack={() => navigate('home')}
        onFavorite={() => handleToggleFavorite(selectedRecipe.id)}
        onEdit={() => navigate('edit')}
        onDelete={() => handleDelete(selectedRecipe.id)}
      />
    )
  }

  if (page === 'add' || page === 'edit') {
    return (
      <RecipeForm
        categories={categories}
        initial={page === 'edit' ? selectedRecipe || undefined : undefined}
        onSave={() => {
          loadRecipes()
          navigate('home')
        }}
        onCancel={() => navigate('home')}
      />
    )
  }

  if (page === 'chat') {
    return (
      <div className="flex flex-col h-screen pb-16">
        <header className="sticky top-0 bg-white/90 backdrop-blur border-b border-orange-100 z-10 px-4 pt-4 pb-3">
          <h1 className="text-xl font-bold text-gray-800">💬 对话添加菜谱</h1>
          <p className="text-xs text-gray-400 mt-0.5">告诉我菜名，我来帮你生成菜谱</p>
        </header>
        <div className="flex-1 overflow-hidden">
          <ChatPage />
        </div>
        <BottomNav tab={tab} onTabChange={(t) => { setTab(t); navigate(t === 'chat' ? 'chat' : 'home'); if (t !== 'chat') loadRecipes() }} onAdd={() => navigate('add')} />
      </div>
    )
  }

  const displayRecipes = tab === 'favorites' ? recipes.filter((r) => r.is_favorite) : recipes

  return (
    <div className="flex flex-col min-h-screen pb-20">
      <header className="sticky top-0 bg-white/90 backdrop-blur border-b border-orange-100 z-10">
        <div className="px-4 pt-4 pb-3">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-bold text-gray-800">
              {tab === 'favorites' ? '❤️ 我的收藏' : '🍳 我的菜谱'}
            </h1>
            <button
              onClick={() => navigate('add')}
              className="w-11 h-11 rounded-full bg-orange-500 text-white flex items-center justify-center text-lg shadow-sm"
            >
              +
            </button>
          </div>
          {tab === 'home' && (
            <>
              <SearchBar onSearch={setSearchQuery} />
              <div className="mt-3">
                <CategoryFilter
                  categories={categories}
                  selected={selectedCategory}
                  onSelect={setSelectedCategory}
                />
              </div>
            </>
          )}
        </div>
      </header>

      <main className="flex-1 px-4 py-4">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-gray-400">
            加载中...
          </div>
        ) : displayRecipes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-gray-400">
            <span className="text-5xl mb-4">{tab === 'favorites' ? '💔' : '🍽️'}</span>
            <p className="text-lg mb-2">
              {tab === 'favorites' ? '还没有收藏的菜谱' : '还没有菜谱'}
            </p>
            {tab === 'home' && (
              <div className="flex flex-col items-center gap-2 mt-2">
                <button
                  onClick={() => navigate('add')}
                  className="text-orange-500 font-medium"
                >
                  添加第一个菜谱 →
                </button>
                <span className="text-xs text-gray-400">或试试对话添加 💬</span>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayRecipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                onClick={() => {
                  setSelectedRecipe(recipe)
                  navigate('detail', recipe.id)
                }}
                onFavorite={(e) => handleToggleFavorite(recipe.id, e)}
              />
            ))}
          </div>
        )}
      </main>

      <BottomNav tab={tab} onTabChange={(t) => { setTab(t); navigate(t === 'chat' ? 'chat' : 'home'); if (t !== 'chat') loadRecipes() }} onAdd={() => navigate('add')} />
    </div>
  )
}

function BottomNav({ tab, onTabChange, onAdd }: { tab: string; onTabChange: (t: 'home' | 'favorites' | 'chat') => void; onAdd: () => void }) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-orange-100 z-20" style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
      <div className="flex">
        <button
          onClick={() => onTabChange('home')}
          className={`flex-1 pt-3 pb-2 flex flex-col items-center gap-0.5 transition-colors min-h-[48px] ${
            tab === 'home' ? 'text-orange-500' : 'text-gray-400'
          }`}
        >
          <span className="text-xl">🏠</span>
          <span className="text-xs">首页</span>
        </button>
        <button
          onClick={() => onTabChange('chat')}
          className={`flex-1 pt-3 pb-2 flex flex-col items-center gap-0.5 transition-colors min-h-[48px] ${
            tab === 'chat' ? 'text-orange-500' : 'text-gray-400'
          }`}
        >
          <span className="text-xl">💬</span>
          <span className="text-xs">对话</span>
        </button>
        <button
          onClick={() => onTabChange('favorites')}
          className={`flex-1 pt-3 pb-2 flex flex-col items-center gap-0.5 transition-colors min-h-[48px] ${
            tab === 'favorites' ? 'text-orange-500' : 'text-gray-400'
          }`}
        >
          <span className="text-xl">❤️</span>
          <span className="text-xs">收藏</span>
        </button>
        <button
          onClick={onAdd}
          className="flex-1 pt-3 pb-2 flex flex-col items-center gap-0.5 text-gray-400 min-h-[48px]"
        >
          <span className="w-11 h-11 -mt-5 rounded-full bg-orange-500 text-white flex items-center justify-center text-2xl shadow-lg">
            +
          </span>
          <span className="text-xs">添加</span>
        </button>
      </div>
    </nav>
  )
}

export default App
