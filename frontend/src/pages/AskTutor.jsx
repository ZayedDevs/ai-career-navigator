import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useAuth } from '../context/AuthContext'
import Spinner from '../components/ui/Spinner'

/* ── Quick-action chips ── */
const QUICK_ACTIONS = [
  'Help select a career path',
  'Help me find a job',
  'Learn a Topic',
  'Test my Knowledge',
]

/* ── Preset starter questions ── */
const STARTER_QUESTIONS = [
  'What roadmap should I pick?',
  'What are the best jobs for me?',
  'Recommend me a project based on my expertise',
  'Recommend me a topic I can learn in an hour',
  'How do I improve my resume?',
  'What skills should I learn next?',
]

/* ── Single chat bubble ── */
function Bubble({ role, content }) {
  const isUser = role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold"
        style={{
          backgroundColor: isUser ? 'var(--c-primary)' : 'var(--c-surface)',
          color: isUser ? '#fff' : 'var(--c-muted)',
          boxShadow: isUser
            ? '2px 2px 6px #004747, -2px -2px 6px #339999'
            : '3px 3px 7px #C8C6C5, -3px -3px 7px #FFFFFF',
        }}
      >
        {isUser ? 'Y' : 'AI'}
      </div>

      {/* Message */}
      <div
        className="max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed"
        style={
          isUser
            ? {
                backgroundColor: 'var(--c-primary)',
                color: '#fff',
                boxShadow: '3px 3px 8px #004747, -3px -3px 8px #339999',
                borderBottomRightRadius: '4px',
              }
            : {
                backgroundColor: 'var(--c-surface)',
                color: 'var(--c-text)',
                boxShadow: '4px 4px 10px #C8C6C5, -4px -4px 10px #FFFFFF',
                borderBottomLeftRadius: '4px',
              }
        }
      >
        {content}
      </div>
    </div>
  )
}

/* ── Typing indicator ── */
function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold"
        style={{
          backgroundColor: 'var(--c-surface)',
          color: 'var(--c-muted)',
          boxShadow: '3px 3px 7px #C8C6C5, -3px -3px 7px #FFFFFF',
        }}
      >
        AI
      </div>
      <div
        className="flex items-center gap-1.5 rounded-2xl px-4 py-3"
        style={{
          backgroundColor: 'var(--c-surface)',
          boxShadow: '4px 4px 10px #C8C6C5, -4px -4px 10px #FFFFFF',
          borderBottomLeftRadius: '4px',
        }}
      >
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-full"
            style={{
              backgroundColor: 'var(--c-muted)',
              animation: 'bounce 1.2s infinite',
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
    </div>
  )
}

/* ════════════════════════════════════════════════════════ */
export default function AskTutor() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [messages, setMessages]   = useState([])   // { role, content }
  const [input, setInput]         = useState('')
  const [sending, setSending]     = useState(false)
  const [apiError, setApiError]   = useState('')
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  /* Auto-scroll to latest message */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  /* Focus input on mount */
  useEffect(() => { inputRef.current?.focus() }, [])

  const sendMessage = async (text) => {
    const msg = (text ?? input).trim()
    if (!msg || sending) return

    setInput('')
    setApiError('')
    const newHistory = [...messages, { role: 'user', content: msg }]
    setMessages(newHistory)
    setSending(true)

    try {
      const res = await api.post('/api/chat/message', {
        message: msg,
        history: messages,   // send history before this new message
      })
      const reply = res.data.data.reply
      setMessages([...newHistory, { role: 'assistant', content: reply }])
    } catch (e) {
      const errMsg = e.response?.data?.message || 'Failed to reach the AI tutor.'
      setApiError(errMsg)
      // Remove the optimistic user message on error
      setMessages(messages)
    } finally {
      setSending(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]" style={{ maxHeight: '100vh' }}>

      {/* ── Page header ── */}
      <div className="shrink-0 mb-4">
        <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
          AI Career Navigator
        </p>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>Ask AI Tutor</h1>
      </div>

      {/* ── Chat area ── */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {isEmpty ? (
          /* ── Empty / welcome state ── */
          <div className="flex flex-col items-center gap-8 py-12">
            <div className="text-center">
              <h2 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>
                How can I help you{user?.name ? `, ${user.name.split(' ')[0]}` : ''}?
              </h2>
              <p className="mt-2 text-xs" style={{ color: 'var(--c-muted)' }}>
                Your personalized AI career companion
              </p>
            </div>

            {/* Quick-action chips */}
            <div className="flex flex-wrap justify-center gap-2">
              {QUICK_ACTIONS.map((action) => (
                <button
                  key={action}
                  onClick={() => sendMessage(action)}
                  className="rounded-full px-4 py-2 text-xs font-bold uppercase tracking-widest transition-all neu-raised-sm hover:neu-pressed-sm"
                  style={{ color: 'var(--c-text)', backgroundColor: 'var(--c-surface)' }}
                >
                  {action}
                </button>
              ))}
            </div>

            {/* Divider */}
            <div className="w-full max-w-lg">
              <div className="h-px w-full" style={{ backgroundColor: 'rgba(0,0,0,0.07)' }} />
            </div>

            {/* Starter questions */}
            <div className="w-full max-w-lg flex flex-col gap-0.5">
              {STARTER_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-sm text-left transition-all hover:neu-pressed-sm"
                  style={{ color: 'var(--c-primary)' }}
                >
                  <span className="text-base">→</span>
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* ── Message thread ── */
          <div className="flex flex-col gap-5 pb-6">
            {messages.map((msg, i) => (
              <Bubble key={i} role={msg.role} content={msg.content} />
            ))}
            {sending && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* ── Error banner ── */}
      {apiError && (
        <div
          className="shrink-0 mb-3 rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
          style={{ color: 'var(--c-danger)', backgroundColor: 'var(--c-surface)' }}
        >
          {apiError}
        </div>
      )}

      {/* ── Input bar ── */}
      <div
        className="shrink-0 rounded-2xl p-4 neu-raised"
        style={{ backgroundColor: 'var(--c-surface)' }}
      >
        {/* Contextual quick buttons */}
        <div className="mb-3 flex gap-2">
          <button
            onClick={() => sendMessage('Give me a summary of my current learning profile and skills.')}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-bold uppercase tracking-widest transition-all neu-raised-sm"
            style={{ color: 'var(--c-text)', backgroundColor: 'var(--c-surface)' }}
          >
            ✦ Personalize
          </button>
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-bold uppercase tracking-widest transition-all neu-raised-sm"
            style={{ color: 'var(--c-text)', backgroundColor: 'var(--c-surface)' }}
          >
            📄 Upload Resume
          </button>
        </div>

        {/* Text input row */}
        <div className="flex items-end gap-3">
          <textarea
            ref={inputRef}
            rows={1}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              // Auto-grow
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
            }}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything…"
            disabled={sending}
            className="flex-1 resize-none rounded-xl px-4 py-3 text-sm outline-none transition-all neu-pressed-sm disabled:opacity-50"
            style={{
              backgroundColor: 'var(--c-surface)',
              color: 'var(--c-text)',
              minHeight: '44px',
              maxHeight: '120px',
            }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || sending}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-white transition-all disabled:opacity-40"
            style={{
              backgroundColor: 'var(--c-primary)',
              boxShadow: '3px 3px 7px #004747, -3px -3px 7px #339999',
            }}
          >
            {sending ? <Spinner size="sm" /> : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
