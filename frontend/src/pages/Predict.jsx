import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useFlow } from '../context/FlowContext'
import Button from '../components/ui/Button'
import ProgressBar from '../components/ui/ProgressBar'
import Spinner from '../components/ui/Spinner'

export default function Predict() {
  const { skills, setTargetRole, setMissingSkills } = useFlow()
  const navigate = useNavigate()

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (skills.length === 0) return
    setLoading(true)
    api.post('/api/predict/career', { skills, top_k: 3 })
      .then((res) => setResult(res.data.data))
      .catch((e) => setError(e.response?.data?.message || 'Prediction failed.'))
      .finally(() => setLoading(false))
  }, [skills])

  const handleGoToRoadmap = async (role) => {
    setTargetRole(role)
    try {
      const encoded = encodeURIComponent(role)
      const res = await api.post(`/api/gap/analyze/${encoded}`, { skills })
      setMissingSkills(res.data.data.missing_critical_skills || [])
    } catch {
      setMissingSkills([])
    }
    navigate('/roadmap')
  }

  if (skills.length === 0) {
    return (
      <div className="flex flex-col items-center gap-5 py-20 text-center">
        <div
          className="flex h-20 w-20 items-center justify-center rounded-2xl text-3xl neu-raised"
          style={{ backgroundColor: 'var(--c-surface)' }}
        >
          🔮
        </div>
        <h2 className="text-lg font-bold" style={{ color: 'var(--c-text)' }}>No skills loaded</h2>
        <p className="text-xs" style={{ color: 'var(--c-muted)' }}>Upload your resume first to get career predictions.</p>
        <Button onClick={() => navigate('/upload')}>Upload Resume</Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
            Career Prediction
          </p>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>
            AI-powered match
          </h1>
          <p className="mt-1 text-xs" style={{ color: 'var(--c-muted)' }}>
            Based on your {skills.length} skills
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate('/gap')}>View gap analysis</Button>
      </div>

      {error && (
        <div
          className="rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
          style={{ color: 'var(--c-danger)', backgroundColor: 'var(--c-surface)' }}
        >
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-3" style={{ color: 'var(--c-muted)' }}>
          <Spinner />
          <span className="text-xs font-bold uppercase tracking-widest">Predicting your best-fit career…</span>
        </div>
      )}

      {result && (
        <>
          {/* Primary prediction card — teal neumorphic */}
          <div
            className="rounded-2xl p-8 text-white neu-teal"
            style={{ backgroundColor: 'var(--c-primary)' }}
          >
            <p className="mb-1 text-xs font-bold uppercase tracking-widest opacity-70">
              Primary prediction
            </p>
            <h2 className="mb-5 text-3xl font-bold leading-tight">
              {result.primary_prediction?.role}
            </h2>

            <div className="flex items-end gap-6">
              <span className="text-5xl font-bold leading-none">
                {result.primary_prediction?.confidence?.toFixed(1)}%
              </span>
              <div className="flex-1">
                <div
                  className="h-3 w-full overflow-hidden rounded-full"
                  style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}
                >
                  <div
                    className="h-full rounded-full bg-white transition-all duration-500"
                    style={{ width: `${Math.min(100, result.primary_prediction?.confidence ?? 0)}%` }}
                  />
                </div>
                <p className="mt-1 text-xs opacity-60">confidence score</p>
              </div>
            </div>

            <div className="mt-4 text-xs opacity-70">
              
            </div>

            <Button
              variant="secondary"
              className="mt-6"
              style={{
                backgroundColor: 'rgba(255,255,255,0.15)',
                color: 'white',
                boxShadow: 'inset 2px 2px 5px rgba(0,0,0,0.2), inset -2px -2px 5px rgba(255,255,255,0.1)',
              }}
              onClick={() => handleGoToRoadmap(result.primary_prediction?.role)}
            >
              Get roadmap for this role →
            </Button>
          </div>

          {/* Top predictions */}
          {result.top_predictions?.length > 1 && (
            <div>
              <p className="mb-3 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
                Top predictions
              </p>
              <div className="flex flex-col gap-3">
                {result.top_predictions.map((p) => (
                  <div
                    key={p.role}
                    className="flex items-center gap-4 rounded-2xl px-5 py-4 neu-raised"
                    style={{ backgroundColor: 'var(--c-surface)' }}
                  >
                    <span
                      className="w-44 text-xs font-bold uppercase tracking-wide"
                      style={{ color: 'var(--c-text)' }}
                    >
                      {p.role}
                    </span>
                    <div className="flex-1">
                      <ProgressBar value={p.confidence} color="var(--c-primary)" />
                    </div>
                    <span
                      className="w-12 text-right text-xs font-bold"
                      style={{ color: 'var(--c-primary)' }}
                    >
                      {p.confidence?.toFixed(1)}%
                    </span>
                    <Button
                      variant="outline"
                      className="text-xs py-1.5 px-3"
                      onClick={() => handleGoToRoadmap(p.role)}
                    >
                      Roadmap
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* All role confidences */}
          <div
            className="rounded-2xl p-6 neu-raised"
            style={{ backgroundColor: 'var(--c-surface)' }}
          >
            <p className="mb-5 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
              All role confidences
            </p>
            <div className="flex flex-col gap-3">
              {[...(result.all_role_confidences ?? [])]
                .sort((a, b) => b.confidence - a.confidence)
                .map((r) => (
                  <div key={r.role} className="flex items-center gap-3">
                    <span
                      className="w-44 truncate text-xs font-bold uppercase tracking-wide"
                      style={{ color: 'var(--c-muted)' }}
                    >
                      {r.role}
                    </span>
                    <div className="flex-1">
                      <ProgressBar value={r.confidence} color="var(--c-primary)" />
                    </div>
                    <span className="w-12 text-right text-xs font-bold" style={{ color: 'var(--c-muted)' }}>
                      {r.confidence?.toFixed(1)}%
                    </span>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
