import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import Spinner from '../components/ui/Spinner'
import Button from '../components/ui/Button'

export default function MyCourses() {
  const navigate = useNavigate()
  const [courses, setCourses]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [removingId, setRemoving] = useState(null)
  const [error, setError]       = useState('')

  useEffect(() => {
    api.get('/api/dashboard/progress')
      .then((res) => {
        const all = res.data.data.progress ?? []
        setCourses(all.filter((p) => p.status === 'learned'))
      })
      .catch(() => setError('Failed to load courses.'))
      .finally(() => setLoading(false))
  }, [])

  const remove = async (skill) => {
    setRemoving(skill)
    try {
      await api.delete(`/api/dashboard/progress/${encodeURIComponent(skill)}`)
      setCourses((prev) => prev.filter((c) => c.skill !== skill))
    } catch {
      setError('Failed to remove course.')
    } finally {
      setRemoving(null)
    }
  }

  const formatDate = (raw) => {
    if (!raw) return ''
    try {
      return new Date(raw.endsWith('Z') || raw.includes('+') ? raw : raw + 'Z')
        .toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
    } catch { return '' }
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div>
        <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
          My Learning
        </p>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>Courses</h1>
        <p className="mt-1 text-xs" style={{ color: 'var(--c-muted)' }}>
          Skills you have marked as learned on your roadmap
        </p>
      </div>

      {error && (
        <div className="rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
             style={{ color: 'var(--c-danger)', backgroundColor: 'var(--c-surface)' }}>
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : courses.length === 0 ? (
        /* ── Empty state ── */
        <div className="flex flex-col items-center gap-5 py-20 text-center rounded-2xl neu-pressed"
             style={{ backgroundColor: 'var(--c-surface)' }}>
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl text-3xl neu-raised"
               style={{ backgroundColor: 'var(--c-surface)' }}>
            📚
          </div>
          <h2 className="text-lg font-bold" style={{ color: 'var(--c-text)' }}>No courses yet</h2>
          <p className="text-xs max-w-xs" style={{ color: 'var(--c-muted)' }}>
            Mark skills as learned on your roadmap and they'll appear here.
          </p>
          <Button onClick={() => navigate('/upload')}>Start a roadmap →</Button>
        </div>
      ) : (
        /* ── Course grid ── */
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {courses.map(({ skill, updated_at }) => (
            <div
              key={skill}
              className="rounded-2xl p-5 flex flex-col gap-3 neu-raised animate-neu-rise"
              style={{ backgroundColor: 'var(--c-surface)' }}
            >
              {/* Top: name + learned badge */}
              <div className="flex items-start justify-between gap-2">
                <h3
                  className="text-sm font-bold capitalize leading-snug"
                  style={{ color: 'var(--c-text)' }}
                >
                  {skill}
                </h3>
                <span
                  className="shrink-0 rounded-full px-2 py-0.5 text-xs font-bold uppercase tracking-wide"
                  style={{ color: 'var(--c-success)', backgroundColor: 'rgba(0,166,61,0.10)' }}
                >
                  ✓ Learned
                </span>
              </div>

              {/* Date */}
              {updated_at && (
                <p className="text-xs" style={{ color: 'var(--c-muted)' }}>
                  Learned {formatDate(updated_at)}
                </p>
              )}

              {/* Remove */}
              <div className="mt-auto pt-2 border-t" style={{ borderColor: 'rgba(0,0,0,0.07)' }}>
                <button
                  disabled={removingId === skill}
                  onClick={() => remove(skill)}
                  className="text-xs font-bold uppercase tracking-widest transition-colors disabled:opacity-40"
                  style={{ color: 'var(--c-danger)' }}
                >
                  {removingId === skill ? 'Removing…' : '× Remove'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
