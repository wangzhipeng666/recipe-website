export interface Category {
  id: number
  name: string
  icon: string
}

export interface Recipe {
  id: number
  name: string
  category_id: number
  image_url: string
  images: string
  ingredients: string
  steps: string
  difficulty: string
  cook_time: string
  tips: string
  is_favorite: boolean
  created_at: string
  updated_at: string
  category?: Category
}

export interface RecipeListResponse {
  items: Recipe[]
  total: number
  page: number
  size: number
}

export interface RecipeCreate {
  name: string
  category_id: number
  image_url?: string
  images?: string
  ingredients?: string
  steps?: string
  difficulty?: string
  cook_time?: string
  tips?: string
}

export interface RecipeUpdate {
  name?: string
  category_id?: number
  image_url?: string
  images?: string
  ingredients?: string
  steps?: string
  difficulty?: string
  cook_time?: string
  tips?: string
}
