import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import Spinner from '../components/ui/Spinner'
import Button from '../components/ui/Button'
import ProgressBar from '../components/ui/ProgressBar'

export default function MyRoadmaps() {
  const navigate = useNavigate()
  const [roadmaps, setRoadmaps] = useState([])
  const [progress, setProgress] = useState({})   // { skill: status }
  const [loading, setLoading]   = useState(true)
  const [deletingId, setDeletingId] = useState(null)
  const [error, setError]       = useState('')

  useEffect(() => {
    Promise.all([
      api.get('/api/dashboard/roadmaps'),
      api.get('/api/dashboard/progress'),
    ])
      .then(([rmRes, prRes]) => {
        setRoadmaps(rmRes.data.data.roadmaps ?? [])
        const map = {}
        for (const p of prRes.data.data.progress ?? []) map[p.skill] = p.status
        setProgress(map)
      })
      .catch(() => setError('Failed to load roadmaps.'))
      .finally(() => setLoading(false))
  }, [])

  const removeRoadmap = async (id) => {
    setDeletingId(id)
    try {
      await api.delete(`/api/dashboard/roadmaps/${id}`)
      setRoadmaps((prev) => prev.filter((r) => r.id !== id))
    } catch {
      setError('Failed to delete roadmap.')
    } finally {
      setDeletingId(null)
    }
  }

  const formatDate = (raw) => {
    if (!raw) return ''
    try {
      return new Date(raw.endsWith('Z') || raw.includes('+') ? raw : raw + 'Z')
        .toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
    } catch { return '' }
  }

  /* compute per-roadmap learned count from local progress map */
  const learnedCount = (roadmap) => {
    const skills = roadmap.phases?.flatMap((ph) => ph.skills?.map((s) => s.skill) ?? []) ?? []
    return skills.filter((s) => progress[s] === 'learned').length
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div>
        <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
          My Learning
        </p>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>Roadmaps</h1>
        <p className="mt-1 text-xs" style={{ color: 'var(--c-muted)' }}>
          Your saved learning roadmaps
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
      ) : roadmaps.length === 0 ? (
        /* ── Empty state ── */
        <div className="flex flex-col items-center gap-5 py-20 text-center rounded-2xl neu-pressed"
             style={{ backgroundColor: 'var(--c-surface)' }}>
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl text-3xl neu-raised"
               style={{ backgroundColor: 'var(--c-surface)' }}>
            🗺️
          </div>
          <h2 className="text-lg font-bold" style={{ color: 'var(--c-text)' }}>No roadmaps found</h2>
          <p className="text-xs max-w-xs" style={{ color: 'var(--c-muted)' }}>
            You haven't generated any roadmaps yet.
          </p>
          <Button onClick={() => navigate('/upload')}>Create your first roadmap →</Button>
        </div>
      ) : (
        /* ── Roadmap cards ── */
        <div className="grid gap-4 sm:grid-cols-2">
          {roadmaps.map((rm) => {
            const total   = rm.skill_count ?? 0
            const learned = learnedCount(rm)
            const pct     = total > 0 ? Math.round((learned / total) * 100) : 0
            return (
              <div
                key={rm.id}
                className="rounded-2xl overflow-hidden neu-raised animate-neu-rise"
                style={{ backgroundColor: 'var(--c-surface)' }}
              >
                {/* Accent bar */}
                <div className="h-1 w-full" style={{ backgroundColor: 'var(--c-primary)' }} />

                <div className="p-5 flex flex-col gap-4">
                  {/* Role + date */}
                  <div>
                    <h3 className="font-bold" style={{ color: 'var(--c-text)' }}>
                      {rm.target_role}
                    </h3>
                    {rm.created_at && (
                      <p className="mt-0.5 text-xs" style={{ color: 'var(--c-muted)' }}>
                        Saved {formatDate(rm.created_at)}
                      </p>
                    )}
                  </div>

                  {/* Meta pills */}
                  <div className="flex flex-wrap gap-2">
                    {[
                      total && `${total} skills`,
                      (rm.phase_count ?? rm.phases?.length) && `${rm.phase_count ?? rm.phases?.length} phases`,
                      rm.total_weeks && `${rm.total_weeks} weeks`,
                    ].filter(Boolean).map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
                        style={{ color: 'var(--c-muted)', backgroundColor: 'var(--c-surface)' }}
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  {/* Progress */}
                  {total > 0 && (
                    <div>
                      <div className="mb-1.5 flex justify-between text-xs font-bold" style={{ color: 'var(--c-muted)' }}>
                        <span>{learned}/{total} learned</span>
                        <span style={{ color: 'var(--c-primary)' }}>{pct}%</span>
                      </div>
                      <ProgressBar value={pct} color="var(--c-primary)" />
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2 mt-1">
                    <Button
                      variant="outline"
                      className="text-xs flex-1"
                      onClick={() => navigate(`/roadmap?id=${rm.id}`)}
                    >
                      Continue →
                    </Button>
                    <Button
                      variant="danger"
                      className="text-xs px-3"
                      loading={deletingId === rm.id}
                      onClick={() => removeRoadmap(rm.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
