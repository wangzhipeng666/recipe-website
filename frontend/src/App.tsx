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
type Tab = 'home' | 'favorites' | 'chat'

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
  const [tab, setTab] = useState<Tab>('home')

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

  // 初始加载/刷新直接落在详情页时，按 hash 里的 id 拉取菜谱
  useEffect(() => {
    if (page === 'detail' && !selectedRecipe) {
      const id = getHashRecipeId()
      if (id) {
        api.getRecipe(id).then(setSelectedRecipe).catch(() => {})
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

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

  const goTab = (t: Tab) => {
    setTab(t)
    if (t === 'chat') {
      navigate('chat')
    } else {
      navigate('home')
      loadRecipes()
    }
  }

  const activeTab: Tab = page === 'chat' ? 'chat' : tab
  const showChrome = page === 'home' || page === 'chat'

  return (
    <div className="min-h-screen flex flex-col">
      <TopNav tab={activeTab} onTab={goTab} onAdd={() => navigate('add')} />

      <div className="flex-1" key={page}>
        {page === 'detail' && selectedRecipe ? (
          <RecipeDetail
            recipe={selectedRecipe}
            onBack={() => navigate('home')}
            onFavorite={() => handleToggleFavorite(selectedRecipe.id)}
            onEdit={() => navigate('edit')}
            onDelete={() => handleDelete(selectedRecipe.id)}
          />
        ) : page === 'add' || page === 'edit' ? (
          <RecipeForm
            categories={categories}
            initial={page === 'edit' ? selectedRecipe || undefined : undefined}
            onSave={() => {
              loadRecipes()
              navigate('home')
            }}
            onCancel={() => navigate('home')}
          />
        ) : page === 'chat' ? (
          <div className="flex flex-col h-[calc(100dvh-60px)] md:h-[calc(100dvh-66px)]">
            <div className="md:hidden px-4 pt-3 pb-1 bg-transparent">
              <h1 className="font-display text-xl tracking-wider">💬 对话添加菜谱</h1>
              <p className="text-xs text-ink-soft mt-0.5">告诉我菜名，我来帮你生成菜谱</p>
            </div>
            <div className="flex-1 overflow-hidden">
              <ChatPage />
            </div>
          </div>
        ) : (
          <HomeView
            recipes={recipes}
            categories={categories}
            loading={loading}
            tab={tab}
            searchQuery={searchQuery}
            selectedCategory={selectedCategory}
            onSearch={setSearchQuery}
            onSelectCategory={setSelectedCategory}
            onOpenRecipe={(r) => {
              setSelectedRecipe(r)
              navigate('detail', r.id)
            }}
            onFavorite={handleToggleFavorite}
            onAdd={() => navigate('add')}
            onGoChat={() => goTab('chat')}
          />
        )}
      </div>

      {showChrome && (
        <BottomNav tab={activeTab} onTab={goTab} onAdd={() => navigate('add')} />
      )}
    </div>
  )
}

// ---------------------------------------------------------------- 首页

function HomeView({
  recipes, categories, loading, tab, searchQuery, selectedCategory,
  onSearch, onSelectCategory, onOpenRecipe, onFavorite, onAdd, onGoChat,
}: {
  recipes: Recipe[]
  categories: Category[]
  loading: boolean
  tab: Tab
  searchQuery: string
  selectedCategory: string
  onSearch: (q: string) => void
  onSelectCategory: (c: string) => void
  onOpenRecipe: (r: Recipe) => void
  onFavorite: (id: number, e?: React.MouseEvent) => void
  onAdd: () => void
  onGoChat: () => void
}) {
  const displayRecipes = tab === 'favorites' ? recipes.filter((r) => r.is_favorite) : recipes

  return (
    <div className="pb-24 md:pb-12">
      {/* 移动端吸顶头部 */}
      <header className="sticky top-0 z-20 md:hidden bg-paper/95 backdrop-blur-sm border-b-2 border-ink/10">
        <div className="px-4 pt-3.5 pb-3">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <span className="seal w-9 h-9 text-base rotate-[-4deg]">菜</span>
              <h1 className="font-display text-xl tracking-wide">
                {tab === 'favorites' ? '我的收藏' : '私房菜谱'}
              </h1>
            </div>
            <span className="text-xs text-ink-soft font-hand text-base">
              {tab === 'favorites' ? `${displayRecipes.length} 道喜欢` : `共 ${recipes.length} 道`}
            </span>
          </div>
          {tab === 'home' && (
            <>
              <SearchBar onSearch={onSearch} initial={searchQuery} />
              <div className="mt-3">
                <CategoryFilter categories={categories} selected={selectedCategory} onSelect={onSelectCategory} />
              </div>
            </>
          )}
        </div>
      </header>

      {/* 桌面头部 */}
      <div className="hidden md:block max-w-6xl mx-auto px-6 pt-10">
        <div className="flex items-end justify-between gap-6">
          <div>
            <h1 className="font-display text-4xl tracking-wider">
              {tab === 'favorites' ? '我的收藏' : '今天吃什么？'}
            </h1>
            <p className="font-hand text-xl text-ink-soft mt-1">
              {tab === 'favorites' ? `${displayRecipes.length} 道最喜欢的菜` : `手作家常菜 · 共 ${recipes.length} 道`}
            </p>
          </div>
          {tab === 'home' && (
            <div className="flex-1 max-w-md">
              <SearchBar onSearch={onSearch} initial={searchQuery} />
            </div>
          )}
        </div>
        {tab === 'home' && (
          <div className="mt-5">
            <CategoryFilter categories={categories} selected={selectedCategory} onSelect={onSelectCategory} />
          </div>
        )}
      </div>

      <main className="max-w-6xl mx-auto px-4 md:px-6 pt-4 md:pt-7">
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3.5 md:gap-5">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="paper-card overflow-hidden">
                <div className="skeleton aspect-[2.15/1] rounded-none" />
                <div className="p-3.5 space-y-2.5">
                  <div className="skeleton h-5 w-3/5" />
                  <div className="skeleton h-3.5 w-2/5" />
                </div>
              </div>
            ))}
          </div>
        ) : displayRecipes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 animate-fade-up">
            <span className="text-6xl mb-5">{tab === 'favorites' ? '🤍' : '🍽️'}</span>
            <p className="font-display text-2xl">
              {tab === 'favorites' ? '还没有收藏的菜谱' : searchQuery || selectedCategory ? '没有找到匹配的菜谱' : '菜谱本还是空的'}
            </p>
            <p className="font-hand text-lg text-ink-soft mt-2">
              {tab === 'favorites' ? '做菜的时候记得点右上角的小爱心呀' : '从第一道家常菜开始记录吧'}
            </p>
            {tab === 'home' && !searchQuery && !selectedCategory && (
              <div className="flex flex-wrap items-center justify-center gap-3 mt-6">
                <button onClick={onAdd} className="btn-primary">✚ 添加菜谱</button>
                <button onClick={onGoChat} className="btn-ghost">💬 试试对话添加</button>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3.5 md:gap-5">
            {displayRecipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                onClick={() => onOpenRecipe(recipe)}
                onFavorite={(e) => onFavorite(recipe.id, e)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

// ---------------------------------------------------------------- 桌面顶栏

function TopNav({ tab, onTab, onAdd }: { tab: Tab; onTab: (t: Tab) => void; onAdd: () => void }) {
  const items: Array<{ key: Tab; label: string; icon: string }> = [
    { key: 'home', label: '菜谱', icon: '📖' },
    { key: 'favorites', label: '收藏', icon: '❤️' },
    { key: 'chat', label: '对话', icon: '💬' },
  ]
  return (
    <header className="hidden md:block sticky top-0 z-30 bg-cream/95 backdrop-blur-sm border-b-2 border-ink/10">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center gap-8">
        <button onClick={() => onTab('home')} className="flex items-center gap-3 shrink-0">
          <span className="seal w-10 h-10 text-xl rotate-[-5deg]">菜</span>
          <span className="font-display text-2xl tracking-widest">私房菜谱</span>
        </button>
        <nav className="flex items-center gap-2">
          {items.map((it) => (
            <button
              key={it.key}
              onClick={() => onTab(it.key)}
              className={`px-4 py-2 rounded-full font-display text-base tracking-wider transition-colors ${
                tab === it.key
                  ? 'bg-accent text-[#FFF6E8] border-2 border-ink/80 shadow-hard-sm'
                  : 'text-ink/75 hover:bg-paper border-2 border-transparent'
              }`}
            >
              {it.icon} {it.label}
            </button>
          ))}
        </nav>
        <div className="flex-1" />
        <button onClick={onAdd} className="btn-primary text-base">✚ 新菜谱</button>
      </div>
    </header>
  )
}

// ---------------------------------------------------------------- 移动底栏

function BottomNav({ tab, onTab, onAdd }: { tab: Tab; onTab: (t: Tab) => void; onAdd: () => void }) {
  const items: Array<{ key: Tab; label: string; icon: string }> = [
    { key: 'home', label: '菜谱', icon: '📖' },
    { key: 'chat', label: '对话', icon: '💬' },
    { key: 'favorites', label: '收藏', icon: '❤️' },
  ]
  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-cream/97 backdrop-blur-sm border-t-2 border-ink/12"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
    >
      <div className="relative flex items-stretch">
        {items.map((it, idx) => (
          <div key={it.key} className="flex-1 flex justify-center">
            {idx === 1 && (
              <button
                onClick={onAdd}
                aria-label="添加菜谱"
                className="absolute -top-6 left-1/2 -translate-x-1/2 w-14 h-14 rounded-2xl bg-accent text-[#FFF6E8] border-2 border-ink/85 shadow-hard flex items-center justify-center text-2xl active:translate-y-0.5 active:shadow-none transition-transform font-light"
              >
                ＋
              </button>
            )}
            <button
              onClick={() => onTab(it.key)}
              className={`w-full pt-2.5 pb-2 flex flex-col items-center gap-0.5 transition-colors ${
                tab === it.key ? 'text-accent' : 'text-ink-soft'
              }`}
            >
              <span className="text-lg leading-none">{it.icon}</span>
              <span className="font-display text-xs tracking-wider">{it.label}</span>
            </button>
          </div>
        ))}
      </div>
    </nav>
  )
}

export default App
