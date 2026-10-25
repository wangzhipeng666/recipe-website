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
    <div className="flex flex-col h-full">
      <div ref={listRef} className="flex-1 overflow-y-auto px-4 py-4">
        <div className="max-w-3xl mx-auto space-y-4">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex items-start gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'system' && (
              <span className="shrink-0 seal w-9 h-9 text-base rotate-[-4deg]">厨</span>
            )}
            <div
              className={`max-w-[85%] px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-accent text-[#FFF6E8] border-2 border-ink/80 rounded-2xl rounded-br-md shadow-hard-sm'
                  : 'paper-card-tight !rounded-2xl !rounded-bl-md text-ink/90'
              }`}
            >
              {msg.type === 'recipe_preview' && msg.recipe ? (
                <RecipePreviewCard recipe={msg.recipe} text={msg.text} onAction={handleAction} />
              ) : msg.type === 'confirm' ? (
                <div>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {msg.recipe_name && (
                      <button
                        onClick={() => handleAction(`生成图片：${msg.recipe_name}`)}
                        className="px-3 py-1.5 rounded-full bg-sun/30 border-2 border-sun/60 text-[#8A5A2B] text-xs active:translate-y-0.5 transition-transform"
                      >
                        🎨 为这道菜生成图片
                      </button>
                    )}
                    <button
                      onClick={() => handleAction('继续添加')}
                      className="px-3 py-1.5 rounded-full bg-paper border-2 border-ink/30 text-ink/80 text-xs active:translate-y-0.5 transition-transform"
                    >
                      继续添加其他菜谱
                    </button>
                  </div>
                </div>
              ) : (
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.text}</p>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-start gap-2.5">
            <span className="shrink-0 seal w-9 h-9 text-base rotate-[-4deg]">厨</span>
            <div className="paper-card-tight !rounded-2xl !rounded-bl-md px-4 py-3.5">
              <div className="flex gap-1.5">
                <span className="w-2 h-2 bg-accent/60 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-accent/60 rounded-full animate-bounce [animation-delay:0.12s]" />
                <span className="w-2 h-2 bg-accent/60 rounded-full animate-bounce [animation-delay:0.24s]" />
              </div>
            </div>
          </div>
        )}
        </div>
      </div>

      <div className="border-t-2 border-ink/12 bg-cream/95 backdrop-blur-sm px-4 py-3 relative z-30">
        <div className="max-w-3xl mx-auto flex gap-2.5">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
            placeholder="输入菜名，比如「红烧排骨」…"
            className="field flex-1 !rounded-full text-[15px]"
            disabled={loading}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || loading}
            aria-label="发送"
            className="shrink-0 w-12 h-12 rounded-full bg-accent text-[#FFF6E8] border-2 border-ink/80 shadow-hard-sm flex items-center justify-center disabled:opacity-40 active:translate-y-0.5 active:shadow-none transition-transform"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
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

      <div className="bg-paper/80 rounded-xl p-3 mb-3 space-y-2.5 border border-ink/12">
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="bg-cream px-2.5 py-1 rounded-full border border-ink/25">📂 {recipe.category}</span>
          {recipe.cook_time && (
            <span className="bg-cream px-2.5 py-1 rounded-full border border-ink/25">⏱ {recipe.cook_time}</span>
          )}
          <span className="bg-cream px-2.5 py-1 rounded-full border border-ink/25">📊 {recipe.difficulty}</span>
        </div>

        <div>
          <p className="text-xs font-display text-accent tracking-wider mb-1.5">🧺 食材</p>
          <div className="flex flex-wrap gap-1.5">
            {previewIngredients.map((item, i) => (
              <span key={i} className="text-xs bg-cream px-2 py-1 rounded-full border border-ink/20">
                {item}
              </span>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-display text-accent tracking-wider mb-1.5">🍳 做法</p>
          <ol className="text-xs space-y-1.5 text-ink/80">
            {previewSteps.map((step, i) => (
              <li key={i} className="flex gap-2">
                <span className="shrink-0 w-4.5 h-4.5 mt-0.5 rounded-full bg-sun/70 border border-ink/50 text-[10px] flex items-center justify-center">{i + 1}</span>
                {step}
              </li>
            ))}
          </ol>
        </div>

        {(recipe.ingredients.length > 5 || recipe.steps.length > 3) && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-accent underline underline-offset-2"
          >
            {expanded ? '收起' : '展开全部'}
          </button>
        )}

        {recipe.tips && (
          <p className="text-xs text-[#8A5A2B] bg-sun/25 border border-dashed border-accent/40 p-2 rounded-lg">💡 {recipe.tips}</p>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => onAction('确认')}
          className="flex-1 py-2.5 rounded-xl bg-accent text-[#FFF6E8] border-2 border-ink/80 text-sm font-display tracking-wider shadow-hard-sm active:translate-y-0.5 active:shadow-none transition-transform min-h-[40px]"
        >
          ✅ 确认添加
        </button>
        <button
          onClick={() => onAction('修改')}
          className="px-3.5 py-2.5 rounded-xl bg-cream border-2 border-ink/60 text-ink text-sm font-display tracking-wider shadow-hard-sm active:translate-y-0.5 active:shadow-none transition-transform min-h-[40px]"
        >
          ✏️ 修改
        </button>
        <button
          onClick={() => onAction('放弃')}
          className="px-3.5 py-2.5 rounded-xl bg-cream border-2 border-ink/25 text-ink-soft text-sm shadow-hard-sm active:translate-y-0.5 active:shadow-none transition-transform min-h-[40px]"
        >
          放弃
        </button>
      </div>
    </div>
  )
}
