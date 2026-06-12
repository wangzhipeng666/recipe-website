import type { Category, Recipe, RecipeCreate, RecipeListResponse, RecipeUpdate } from '../types/recipe'

export interface ChatRecipePreview {
  name: string
  category: string
  ingredients: string[]
  steps: string[]
  difficulty: string
  cook_time: string
  tips: string
}

export interface ChatResponse {
  type: 'text' | 'recipe_preview' | 'confirm' | 'error'
  message: string
  recipe?: ChatRecipePreview
  recipe_id?: number
  recipe_name?: string
}

const BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const hasBody = options?.body != null
  const defaultHeaders: Record<string, string> = hasBody ? { 'Content-Type': 'application/json' } : {}
  const res = await fetch(`${BASE}${url}`, {
    ...options,
    headers: { ...defaultHeaders, ...options?.headers },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || '请求失败')
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  getRecipes(params?: { category?: string; search?: string; page?: number; size?: number }) {
    const query = new URLSearchParams()
    if (params?.category) query.set('category', params.category)
    if (params?.search) query.set('search', params.search)
    if (params?.page) query.set('page', String(params.page))
    if (params?.size) query.set('size', String(params.size))
    const qs = query.toString()
    return request<RecipeListResponse>(`/recipes${qs ? `?${qs}` : ''}`)
  },

  getRecipe(id: number) {
    return request<Recipe>(`/recipes/${id}`)
  },

  createRecipe(data: RecipeCreate) {
    return request<Recipe>('/recipes', { method: 'POST', body: JSON.stringify(data) })
  },

  updateRecipe(id: number, data: RecipeUpdate) {
    return request<Recipe>(`/recipes/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  },

  deleteRecipe(id: number) {
    return request<void>(`/recipes/${id}`, { method: 'DELETE' })
  },

  toggleFavorite(id: number) {
    return request<Recipe>(`/recipes/${id}/favorite`, { method: 'POST' })
  },

  getCategories() {
    return request<Category[]>('/categories')
  },

  createCategory(data: { name: string; icon: string }) {
    return request<Category>('/categories', { method: 'POST', body: JSON.stringify(data) })
  },

  async uploadImage(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${BASE}/images/upload`, { method: 'POST', body: formData })
    if (!res.ok) throw new Error('上传失败')
    return res.json() as Promise<{ image_url: string }>
  },

  generateImage(name: string) {
    return request<{ image_url: string }>('/images/generate', {
      method: 'POST',
      body: JSON.stringify({ name }),
    })
  },

  generateImageAsync(prompt: string, width = 1024, height = 768, steps = 4) {
    return request<{ task_id: number; status: string; status_url: string; image_url: string }>(
      '/images/generate-async',
      { method: 'POST', body: JSON.stringify({ prompt, width, height, steps }) },
    )
  },

  getImageStatus(taskId: number) {
    return request<{ task_id: number; status: string; image_url?: string; error_message?: string }>(
      `/images/status/${taskId}`,
    )
  },

  sendMessage(message: string, sessionId?: string) {
    return request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId || 'default' }),
    })
  },
}
