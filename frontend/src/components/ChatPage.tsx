import { useState, useRef, useEffect } from 'react'
import { api, type ChatRecipePreview } from '../api'

const sessionId = crypto.randomUUID?.() ?? 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16) })

interface Message {
  id: number
  role: 'user' | 'system'
  text: string
  recipe?: ChatRecipePreview
  type?: string
  recipe_name?: string
}

let msgId = 0

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: ++msgId,
      role: 'system',
      text: '你好！告诉我你想做什么菜，我来帮你生成菜谱。\n\n例如：\n• 红烧排骨\n• 宫保鸡丁，花生多放点\n• 鱼香肉丝',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    listRef.current?.scrollTo(0, listRef.current.scrollHeight)
  }, [messages])

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return

    const userMsg: Message = { id: ++msgId, role: 'user', text: text.trim() }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await api.sendMessage(text.trim(), sessionId)
      const sysMsg: Message = {
        id: ++msgId,
        role: 'system',
        text: res.message,
        recipe: res.recipe,
        type: res.type,
        recipe_name: res.recipe_name,
      }
      setMessages((prev) => [...prev, sysMsg])
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: ++msgId, role: 'system', text: '网络错误，请稍后重试。' },
      ])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleAction = (action: string) => {
    sendMessage(action)
  }

  return (
    <div className="flex flex-col h-full bg-orange-50/50">
      <div ref={listRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-orange-500 text-white rounded-br-md'
                  : 'bg-white text-gray-700 border border-orange-100 rounded-bl-md shadow-sm'
              }`}
            >
              {msg.type === 'recipe_preview' && msg.recipe ? (
                <RecipePreviewCard recipe={msg.recipe} text={msg.text} onAction={handleAction} />
              ) : msg.type === 'confirm' ? (
                <div>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>
                  {msg.recipe_name && (
                    <button
                      onClick={() => handleAction(`生成图片：${msg.recipe_name}`)}
                      className="mt-2 text-xs text-purple-500 underline"
                    >
                      🎨 为这道菜生成图片
                    </button>
                  )}
                  <button
                    onClick={() => handleAction('继续添加')}
                    className="mt-2 ml-2 text-xs text-orange-500 underline"
                  >
                    继续添加其他菜谱
                  </button>
                </div>
              ) : (
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-orange-100 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-orange-300 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-orange-300 rounded-full animate-bounce [animation-delay:0.1s]" />
                <span className="w-2 h-2 bg-orange-300 rounded-full animate-bounce [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-orange-100 bg-white px-4 py-3 relative z-30">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
            placeholder="输入菜名或指令..."
            className="flex-1 px-4 py-3 rounded-xl bg-orange-50 border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300 text-sm"
            disabled={loading}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            className="shrink-0 w-11 h-11 rounded-xl bg-orange-500 text-white flex items-center justify-center disabled:opacity-40 active:scale-95 transition-transform"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}

function RecipePreviewCard({
  recipe,
  text,
  onAction,
}: {
  recipe: ChatRecipePreview
  text: string
  onAction: (action: string) => void
}) {
  const [expanded, setExpanded] = useState(false)

  const previewIngredients = expanded ? recipe.ingredients : recipe.ingredients.slice(0, 5)
  const previewSteps = expanded ? recipe.steps : recipe.steps.slice(0, 3)

  return (
    <div>
      <p className="whitespace-pre-wrap text-sm leading-relaxed mb-3">{text}</p>

      <div className="bg-orange-50/80 rounded-xl p-3 mb-3 space-y-2">
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="bg-white px-2 py-0.5 rounded-full border border-orange-200">
            📂 {recipe.category}
          </span>
          {recipe.cook_time && (
            <span className="bg-white px-2 py-0.5 rounded-full border border-orange-200">
              ⏱ {recipe.cook_time}
            </span>
          )}
          <span className="bg-white px-2 py-0.5 rounded-full border border-orange-200">
            📊 {recipe.difficulty}
          </span>
        </div>

        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">🥬 食材</p>
          <div className="flex flex-wrap gap-1">
            {previewIngredients.map((item, i) => (
              <span key={i} className="text-xs bg-white px-2 py-0.5 rounded border border-orange-100">
                {item}
              </span>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">👨‍🍳 做法</p>
          <ol className="text-xs space-y-1 list-decimal list-inside text-gray-600">
            {previewSteps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>

        {(recipe.ingredients.length > 5 || recipe.steps.length > 3) && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-orange-500 underline"
          >
            {expanded ? '收起' : '展开全部'}
          </button>
        )}

        {recipe.tips && (
          <p className="text-xs text-yellow-600 bg-yellow-50 p-2 rounded-lg">💡 {recipe.tips}</p>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => onAction('确认')}
          className="flex-1 py-2.5 rounded-xl bg-orange-500 text-white text-sm font-medium active:scale-95 transition-transform min-h-[40px]"
        >
          ✅ 确认添加
        </button>
        <button
          onClick={() => onAction('修改')}
          className="px-3 py-2.5 rounded-xl bg-white border border-orange-200 text-orange-600 text-sm active:scale-95 transition-transform min-h-[40px]"
        >
          ✏️ 修改
        </button>
        <button
          onClick={() => onAction('放弃')}
          className="px-3 py-2.5 rounded-xl bg-white border border-gray-200 text-gray-500 text-sm active:scale-95 transition-transform min-h-[40px]"
        >
          放弃
        </button>
      </div>
    </div>
  )
}
