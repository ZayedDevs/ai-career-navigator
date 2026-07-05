import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { useFlow } from '../context/FlowContext'
import Button from '../components/ui/Button'
import ProgressBar from '../components/ui/ProgressBar'
import Spinner from '../components/ui/Spinner'

const STAT_ACCENTS = [
  'var(--c-primary)',
  'var(--c-success)',
  'var(--c-warning)',
  '#7c3aed',
]

function StatCard({ label, value, sub, accentColor }) {
  return (
    <div
      className="rounded-2xl p-5 neu-raised"
      style={{ backgroundColor: 'var(--c-surface)' }}
    >
      <p className="text-3xl font-bold" style={{ color: accentColor ?? 'var(--c-primary)' }}>
        {value ?? '—'}
      </p>
      <p className="mt-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-text)' }}>
        {label}
      </p>
      {sub && (
        <p className="mt-0.5 text-xs" style={{ color: 'var(--c-muted)' }}>{sub}</p>
      )}
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const { setSkills, setTargetRole, setMissingSkills } = useFlow()
  const navigate = useNavigate()

  const [stats, setStats] = useState(null)
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState(null)
  const [clearingSkills, setClearingSkills] = useState(false)
  const [learnedOpen, setLearnedOpen] = useState(false)
  const [learnedSkills, setLearnedSkills] = useState(null)
  const [unlearnId, setUnlearnId] = useState(null)
  const [error, setError] = useState('')

  const load = () => {
    setLoading(true)
    Promise.all([
      api.get('/api/dashboard/stats'),
      api.get('/api/dashboard/analyses'),
    ])
      .then(([statsRes, analysesRes]) => {
        setStats(statsRes.data.data)
        setAnalyses(analysesRes.data.data.analyses ?? [])
      })
      .catch((e) => setError(e.response?.data?.message || 'Failed to load dashboard.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const openLearned = async () => {
    setLearnedOpen(true)
    if (learnedSkills !== null) return
    try {
      const res = await api.get('/api/dashboard/progress')
      setLearnedSkills((res.data.data.progress ?? []).filter((p) => p.status === 'learned'))
    } catch (e) {
      setError(e.response?.data?.message || 'Failed to load learned skills.')
    }
  }

  const unlearn = async (skill) => {
    setUnlearnId(skill)
    try {
      await api.delete(`/api/dashboard/progress/${encodeURIComponent(skill)}`)
      setLearnedSkills((prev) => prev.filter((p) => p.skill !== skill))
      setStats((prev) =>
        prev ? { ...prev, skills_learned: Math.max(0, (prev.skills_learned ?? 1) - 1) } : prev
      )
    } catch (e) {
      setError(e.response?.data?.message || 'Failed to remove skill.')
    } finally {
      setUnlearnId(null)
    }
  }

  const clearActiveSkills = async () => {
    setClearingSkills(true)
    try {
      await api.delete('/api/dashboard/active-skills')
      setStats((prev) => prev ? { ...prev, user: { ...prev.user, active_skill_count: 0 } } : prev)
    } catch (e) {
      setError(e.response?.data?.message || 'Failed to clear active skills.')
    } finally {
      setClearingSkills(false)
    }
  }

  const deleteAnalysis = async (id) => {
    setDeletingId(id)
    try {
      await api.delete(`/api/dashboard/analyses/${id}`)
      setAnalyses((prev) => prev.filter((a) => a.id !== id))
    } catch (e) {
      setError(e.response?.data?.message || 'Delete failed.')
    } finally {
      setDeletingId(null)
    }
  }

  const resumeFlow = (analysis) => {
    if (analysis.extracted_skills?.length) setSkills(analysis.extracted_skills)
    if (analysis.target_role) setTargetRole(analysis.target_role)
    navigate('/gap')
  }

  const formatDate = (raw) => {
    if (!raw) return '—'
    try {
      return new Date(raw.endsWith('Z') || raw.includes('+') ? raw : raw + 'Z').toLocaleDateString()
    } catch {
      return raw
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner size="lg" />
      </div>
    )
  }

  const rp = stats?.roadmap_progress

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
            Dashboard
          </p>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>
            Welcome back, {user?.name}
          </h1>
        </div>
        <Button onClick={() => navigate('/upload')}>Upload Resume</Button>
      </div>

      {error && (
        <div
          className="rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
          style={{ color: 'var(--c-danger)', backgroundColor: 'var(--c-surface)' }}
        >
          {error}
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Analyses" value={stats?.total_analyses} accentColor={STAT_ACCENTS[0]} />
        {/* Learned — expandable */}
        <div
          className="rounded-2xl p-5 neu-raised"
          style={{ backgroundColor: 'var(--c-surface)' }}
        >
          <button
            className="flex w-full items-start justify-between gap-2 text-left"
            onClick={learnedOpen ? () => setLearnedOpen(false) : openLearned}
          >
            <div>
              <p className="text-3xl font-bold" style={{ color: STAT_ACCENTS[1] }}>
                {stats?.skills_learned ?? '—'}
              </p>
              <p className="mt-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-text)' }}>
                Learned
              </p>
            </div>
            <span
              className="mt-1 shrink-0 text-xs transition-transform duration-200"
              style={{
                color: 'var(--c-muted)',
                display: 'inline-block',
                transform: learnedOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              }}
            >
              ▾
            </span>
          </button>

          {learnedOpen && (
            <div
              className="mt-3 border-t pt-3 flex flex-col gap-2"
              style={{ borderColor: 'rgba(0,0,0,0.07)' }}
            >
              {learnedSkills === null ? (
                <Spinner size="sm" />
              ) : learnedSkills.length === 0 ? (
                <p className="text-xs" style={{ color: 'var(--c-muted)' }}>No learned skills yet.</p>
              ) : (
                learnedSkills.map(({ skill }) => (
                  <div key={skill} className="flex items-center justify-between gap-2">
                    <span
                      className="text-xs font-bold capitalize leading-snug"
                      style={{ color: 'var(--c-text)' }}
                    >
                      {skill}
                    </span>
                    <button
                      disabled={unlearnId === skill}
                      onClick={() => unlearn(skill)}
                      className="shrink-0 text-xs font-bold uppercase tracking-widest transition-colors disabled:opacity-40"
                      style={{ color: 'var(--c-danger)' }}
                    >
                      {unlearnId === skill ? '…' : '× Remove'}
                    </button>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
        <StatCard label="Learning" value={stats?.skills_learning} accentColor={STAT_ACCENTS[2]} />
        <div
          className="rounded-2xl p-5 neu-raised"
          style={{ backgroundColor: 'var(--c-surface)' }}
        >
          <p className="text-3xl font-bold" style={{ color: STAT_ACCENTS[3] }}>
            {stats?.user?.active_skill_count ?? '—'}
          </p>
          <p className="mt-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-text)' }}>
            Active skills
          </p>
          {(stats?.user?.active_skill_count ?? 0) > 0 && (
            <button
              onClick={clearActiveSkills}
              disabled={clearingSkills}
              className="mt-2 text-xs font-bold uppercase tracking-widest transition-colors disabled:opacity-50"
              style={{ color: 'var(--c-danger)' }}
            >
              {clearingSkills ? 'Clearing…' : '× Clear all'}
            </button>
          )}
        </div>
      </div>

      {/* Active roadmap */}
      {rp && (
        <div
          className="rounded-2xl overflow-hidden neu-raised"
          style={{ backgroundColor: 'var(--c-surface)' }}
        >
          <div className="h-1 w-full" style={{ backgroundColor: 'var(--c-primary)' }} />
          <div className="p-6">
            <div className="mb-3 flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
                  Active roadmap
                </p>
                <h2 className="font-bold" style={{ color: 'var(--c-text)' }}>
                  {rp.target_role}
                </h2>
                <p className="text-xs" style={{ color: 'var(--c-muted)' }}>
                  {rp.skills_completed} / {rp.total_skills} skills completed
                </p>
              </div>
              <span className="text-2xl font-bold" style={{ color: 'var(--c-primary)' }}>
                {Math.min(100, rp.percent_complete ?? 0).toFixed(1)}%
              </span>
            </div>
            <ProgressBar value={Math.min(100, rp.percent_complete ?? 0)} color="var(--c-primary)" />
            <Button variant="outline" className="mt-4 text-xs" onClick={() => navigate('/roadmap')}>
              Continue roadmap →
            </Button>
          </div>
        </div>
      )}

      {/* Latest analysis */}
      {stats?.latest_analysis && (
        <div
          className="rounded-2xl p-6 neu-raised"
          style={{ backgroundColor: 'var(--c-surface)' }}
        >
          <p className="mb-4 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
            Latest analysis
          </p>
          <div className="flex flex-wrap gap-x-8 gap-y-2 text-xs">
            <div>
              <span style={{ color: 'var(--c-muted)' }}>File </span>
              <strong style={{ color: 'var(--c-text)' }}>{stats.latest_analysis.filename}</strong>
            </div>
            {stats.latest_analysis.predicted_career && (
              <div>
                <span style={{ color: 'var(--c-muted)' }}>Predicted </span>
                <strong style={{ color: 'var(--c-primary)' }}>{stats.latest_analysis.predicted_career}</strong>
              </div>
            )}
            {stats.latest_analysis.overall_readiness != null && (
              <div>
                <span style={{ color: 'var(--c-muted)' }}>Readiness </span>
                <strong style={{ color: 'var(--c-text)' }}>{stats.latest_analysis.overall_readiness?.toFixed(1)}%</strong>
              </div>
            )}
            <div>
              <span style={{ color: 'var(--c-muted)' }}>Skills </span>
              <strong style={{ color: 'var(--c-text)' }}>{stats.latest_analysis.skill_count ?? stats.latest_analysis.extracted_skills?.length}</strong>
            </div>
          </div>
          <Button variant="outline" className="mt-4 text-xs" onClick={() => resumeFlow(stats.latest_analysis)}>
            Resume this session →
          </Button>
        </div>
      )}

      {/* All analyses */}
      <div>
        <p className="mb-5 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
          All analyses
        </p>
        {analyses.length === 0 ? (
          <div
            className="rounded-2xl py-14 text-center neu-pressed"
            style={{ backgroundColor: 'var(--c-surface)' }}
          >
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
              No analyses yet.{' '}
              <button
                className="font-bold transition-colors"
                style={{ color: 'var(--c-primary)' }}
                onClick={() => navigate('/upload')}
              >
                Upload a resume
              </button>
              {' '}to get started.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {analyses.map((analysis) => (
              <div
                key={analysis.id}
                className="flex flex-col gap-3 rounded-2xl p-5 transition-all sm:flex-row sm:items-center sm:justify-between neu-raised"
                style={{ backgroundColor: 'var(--c-surface)' }}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-3">
                    <span
                      className="truncate text-xs font-bold uppercase tracking-wide"
                      style={{ color: 'var(--c-text)' }}
                    >
                      {analysis.filename}
                    </span>
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
                      style={{ color: 'var(--c-muted)', backgroundColor: 'var(--c-surface)' }}
                    >
                      {formatDate(analysis.timestamp ?? analysis.created_at)}
                    </span>
                  </div>
                  <div className="mt-1.5 flex flex-wrap gap-4 text-xs" style={{ color: 'var(--c-muted)' }}>
                    <span>{analysis.skill_count ?? analysis.extracted_skills?.length} skills</span>
                    {analysis.predicted_career && (
                      <span style={{ color: 'var(--c-primary)' }}>→ {analysis.predicted_career}</span>
                    )}
                    {analysis.overall_readiness != null && (
                      <span>{analysis.overall_readiness?.toFixed(1)}% ready</span>
                    )}
                    {analysis.target_role && <span>Target: {analysis.target_role}</span>}
                  </div>
                  {analysis.top_matches?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {analysis.top_matches.slice(0, 3).map((m) => (
                        <span
                          key={m.role}
                          className="rounded-full px-2 py-0.5 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
                          style={{ color: 'var(--c-primary)', backgroundColor: 'var(--c-surface)' }}
                        >
                          {m.role} {m.match_percentage?.toFixed(0)}%
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex shrink-0 gap-2">
                  <Button variant="outline" className="text-xs py-1.5 px-3" onClick={() => resumeFlow(analysis)}>
                    Resume
                  </Button>
                  <Button
                    variant="danger"
                    className="text-xs py-1.5 px-3"
                    loading={deletingId === analysis.id}
                    onClick={() => deleteAnalysis(analysis.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
