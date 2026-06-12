import { useState } from 'react'
import type { Category, Recipe } from '../types/recipe'
import { api } from '../api'

interface Props {
  categories: Category[]
  initial?: Recipe
  onSave: () => void
  onCancel: () => void
}

export function RecipeForm({ categories, initial, onSave, onCancel }: Props) {
  const [name, setName] = useState(initial?.name || '')
  const [categoryId, setCategoryId] = useState(initial?.category_id || categories[0]?.id || 1)
  const [difficulty, setDifficulty] = useState(initial?.difficulty || '简单')
  const [cookTime, setCookTime] = useState(initial?.cook_time || '')
  const [images, setImages] = useState<string[]>(() => {
    if (initial?.images) {
      try { return JSON.parse(initial.images) } catch { /* ignore */ }
    }
    return initial?.image_url ? [initial.image_url] : []
  })
  const [ingredients, setIngredients] = useState<string[]>(
    initial ? JSON.parse(initial.ingredients || '[]') : ['']
  )
  const [steps, setSteps] = useState<string[]>(
    initial ? JSON.parse(initial.steps || '[]') : ['']
  )
  const [tips, setTips] = useState(initial?.tips || '')
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [generateProgress, setGenerateProgress] = useState('')

  const handleAddIngredient = () => setIngredients([...ingredients, ''])
  const handleRemoveIngredient = (i: number) => setIngredients(ingredients.filter((_, idx) => idx !== i))
  const handleIngredientChange = (i: number, v: string) => {
    const next = [...ingredients]
    next[i] = v
    setIngredients(next)
  }

  const handleAddStep = () => setSteps([...steps, ''])
  const handleRemoveStep = (i: number) => setSteps(steps.filter((_, idx) => idx !== i))
  const handleStepChange = (i: number, v: string) => {
    const next = [...steps]
    next[i] = v
    setSteps(next)
  }

  const [dragIndex, setDragIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)
  const [touchStartY, setTouchStartY] = useState<number | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleDragStart = (i: number) => setDragIndex(i)
  const handleDragEnter = (i: number) => { if (dragIndex !== null && i !== dragIndex) setDragOverIndex(i) }
  const handleDragEnd = () => { setDragIndex(null); setDragOverIndex(null) }

  const handleDrop = (targetIndex: number) => {
    if (dragIndex === null || dragIndex === targetIndex) return
    const next = [...steps]
    const [moved] = next.splice(dragIndex, 1)
    next.splice(targetIndex, 0, moved)
    setSteps(next)
    setDragIndex(null)
    setDragOverIndex(null)
  }

  const handleTouchStart = (i: number, e: React.TouchEvent) => {
    setTouchStartY(e.touches[0].clientY)
    setDragIndex(i)
    setIsDragging(false)
  }

  const handleTouchMove = (e: React.TouchEvent) => {
    if (dragIndex === null) return
    if (!isDragging) setIsDragging(true)
    const touch = e.touches[0]
    const elements = document.elementsFromPoint(touch.clientX, touch.clientY)
    for (const el of elements) {
      const stepEl = el.closest('[data-step-index]')
      if (stepEl) {
        const idx = Number(stepEl.getAttribute('data-step-index'))
        if (idx !== dragIndex) setDragOverIndex(idx)
        break
      }
    }
  }

  const handleTouchEnd = () => {
    if (dragIndex !== null && dragOverIndex !== null && dragIndex !== dragOverIndex) {
      const next = [...steps]
      const [moved] = next.splice(dragIndex, 1)
      next.splice(dragOverIndex, 0, moved)
      setSteps(next)
    }
    setDragIndex(null)
    setDragOverIndex(null)
    setTouchStartY(null)
    setIsDragging(false)
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true)
    try {
      const res = await api.uploadImage(file)
      setImages((prev) => [...prev, res.image_url])
    } catch {
      alert('上传失败')
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSetMainImage = (index: number) => {
    if (index === 0) return
    setImages((prev) => {
      const next = [...prev]
      const [moved] = next.splice(index, 1)
      next.unshift(moved)
      return next
    })
  }

  const handleGenerate = async () => {
    if (!name.trim()) return alert('请先输入菜名')
    setGenerating(true)
    setGenerateProgress('正在提交任务...')
    try {
      const prompt = `一道精美的中式菜肴：${name}，美食摄影风格，高清，暖色调，白色盘子，自然光`
      const submitRes = await api.generateImageAsync(prompt)
      const taskId = submitRes.task_id

      setGenerateProgress('图片生成中，请稍候...')

      for (let i = 0; i < 36; i++) {
        await new Promise((r) => setTimeout(r, 5000))
        const status = await api.getImageStatus(taskId)
        if (status.status === 'completed' && status.image_url) {
          setImages((prev) => [...prev, status.image_url!])
          setGenerateProgress('')
          return
        }
        if (status.status === 'failed') {
          throw new Error(status.error_message || '生成失败')
        }
        setGenerateProgress(`生成中...(${(i + 1) * 5}秒)`)
      }
      throw new Error('生成超时，请重试')
    } catch (e: any) {
      alert(e.message || '图片生成失败')
      setGenerateProgress('')
    } finally {
      setGenerating(false)
    }
  }

  const handleSubmit = async () => {
    if (!name.trim()) return alert('请输入菜名')
    setLoading(true)
    try {
      const imagesJson = JSON.stringify(images)
      const data = {
        name,
        category_id: categoryId,
        difficulty,
        cook_time: cookTime,
        image_url: images[0] || '',
        images: imagesJson,
        ingredients: JSON.stringify(ingredients.filter(Boolean)),
        steps: JSON.stringify(steps.filter(Boolean)),
        tips,
      }
      if (initial) {
        await api.updateRecipe(initial.id, data)
      } else {
        await api.createRecipe(data)
      }
      onSave()
    } catch (e: any) {
      alert(e.message || '保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-white pb-20">
      <div className="sticky top-0 bg-white border-b border-orange-100 px-4 py-3 flex items-center justify-between z-10">
        <button onClick={onCancel} className="text-gray-500">取消</button>
        <h1 className="font-semibold text-gray-800">{initial ? '编辑菜谱' : '添加菜谱'}</h1>
        <button onClick={handleSubmit} disabled={loading} className="text-orange-500 font-medium disabled:opacity-50">
          {loading ? '保存中...' : '保存'}
        </button>
      </div>

      <div className="p-4 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">菜名 *</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例如：红烧肉"
            className="w-full px-4 py-3 rounded-xl border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">图片</label>
          <div className="flex flex-col sm:flex-row gap-2">
            <label className="flex-1 px-4 py-3 rounded-xl border border-dashed border-orange-300 text-center text-orange-500 cursor-pointer active:bg-orange-50 min-h-[48px] flex items-center justify-center">
              {loading ? '上传中...' : '📷 上传图片'}
              <input type="file" accept="image/*" onChange={handleUpload} className="hidden" />
            </label>
            <button
              type="button"
              onClick={handleGenerate}
              disabled={generating}
              className="px-4 py-3 rounded-xl bg-purple-50 text-purple-600 border border-purple-200 active:bg-purple-100 disabled:opacity-50 min-h-[48px]"
            >
              {generating ? '生成中...' : '🎨 AI生成'}
            </button>
          </div>
          {images.length > 0 && (
            <div className="mt-2 grid grid-cols-3 gap-2">
              {images.map((url, i) => (
                <div key={i} className="relative group cursor-pointer" onClick={() => handleSetMainImage(i)}>
                  <img src={url} alt={`图片${i + 1}`} className={`w-full h-24 object-contain rounded-xl bg-orange-50 ${i === 0 ? 'ring-2 ring-orange-500' : ''}`} />
                  <span className={`absolute top-1 left-1 text-[10px] px-1.5 py-0.5 rounded-full ${i === 0 ? 'bg-orange-500 text-white' : 'bg-black/40 text-white opacity-0 group-hover:opacity-100'}`}>
                    {i === 0 ? '主图' : '设为主图'}
                  </span>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleRemoveImage(i) }}
                    className="absolute top-1 right-1 w-6 h-6 rounded-full bg-black/50 text-white text-xs flex items-center justify-center"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          {generateProgress && (
            <div className="mt-2 flex items-center gap-2 text-sm text-purple-600">
              <div className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
              {generateProgress}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(Number(e.target.value))}
              className="w-full px-4 py-3 rounded-xl border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300 bg-white"
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.icon} {c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">难度</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300 bg-white"
            >
              <option>简单</option>
              <option>中等</option>
              <option>较难</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">烹饪时间</label>
          <input
            type="text"
            value={cookTime}
            onChange={(e) => setCookTime(e.target.value)}
            placeholder="例如：30分钟"
            className="w-full px-4 py-3 rounded-xl border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">食材</label>
          <div className="space-y-2">
            {ingredients.map((item, i) => (
              <div key={i} className="flex gap-2">
                <input
                  type="text"
                  value={item}
                  onChange={(e) => handleIngredientChange(i, e.target.value)}
                  placeholder={`食材 ${i + 1}`}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300 text-sm"
                />
                {ingredients.length > 1 && (
                  <button onClick={() => handleRemoveIngredient(i)} className="text-gray-400 active:text-red-500 px-2 min-w-[36px] min-h-[36px] flex items-center justify-center">
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>
          <button onClick={handleAddIngredient} className="mt-2 text-sm text-orange-500 hover:text-orange-600">
            + 添加食材
          </button>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">做法步骤</label>
          <div className="space-y-2">
            {steps.map((step, i) => (
              <div
                key={i}
                data-step-index={i}
                draggable
                onDragStart={() => handleDragStart(i)}
                onDragEnter={() => handleDragEnter(i)}
                onDragEnd={handleDragEnd}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => handleDrop(i)}
                onTouchStart={(e) => handleTouchStart(i, e)}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
                className={`flex gap-2 rounded-xl transition-all touch-none select-none ${dragIndex === i ? 'opacity-40 scale-[0.98]' : ''} ${dragOverIndex === i ? 'ring-2 ring-orange-400 ring-offset-1' : ''}`}
              >
                <div className="shrink-0 flex flex-col items-center gap-0.5 mt-1.5 cursor-grab active:cursor-grabbing text-gray-300 hover:text-orange-400 transition-colors" title="拖拽排序">
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                    <circle cx="5" cy="3" r="1.5"/><circle cx="11" cy="3" r="1.5"/>
                    <circle cx="5" cy="8" r="1.5"/><circle cx="11" cy="8" r="1.5"/>
                    <circle cx="5" cy="13" r="1.5"/><circle cx="11" cy="13" r="1.5"/>
                  </svg>
                </div>
                <span className="shrink-0 w-7 h-7 rounded-full bg-orange-500 text-white flex items-center justify-center text-xs font-medium mt-1.5">
                  {i + 1}
                </span>
                <textarea
                  value={step}
                  onChange={(e) => handleStepChange(i, e.target.value)}
                  placeholder={`步骤 ${i + 1}`}
                  rows={2}
                  className="flex-1 px-4 py-2.5 rounded-xl border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300 text-sm resize-none"
                />
                {steps.length > 1 && (
                  <button onClick={() => handleRemoveStep(i)} className="text-gray-400 active:text-red-500 px-2 self-start mt-2 min-w-[36px] min-h-[36px] flex items-center justify-center">
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>
          <button onClick={handleAddStep} className="mt-2 text-sm text-orange-500 hover:text-orange-600">
            + 添加步骤
          </button>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">小贴士</label>
          <textarea
            value={tips}
            onChange={(e) => setTips(e.target.value)}
            placeholder="可选：烹饪小技巧..."
            rows={3}
            className="w-full px-4 py-3 rounded-xl border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300 text-sm resize-none"
          />
        </div>
      </div>
    </div>
  )
}
