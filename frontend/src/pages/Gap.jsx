import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useFlow } from '../context/FlowContext'
import Button from '../components/ui/Button'
import ProgressBar from '../components/ui/ProgressBar'
import Spinner from '../components/ui/Spinner'
import SkillTag from '../components/ui/SkillTag'

export default function Gap() {
  const { skills, setTargetRole, setMissingSkills } = useFlow()
  const navigate = useNavigate()

  const [overview, setOverview] = useState(null)
  const [deepDive, setDeepDive] = useState(null)
  const [selectedRole, setSelectedRole] = useState(null)
  const [loadingOverview, setLoadingOverview] = useState(false)
  const [loadingDive, setLoadingDive] = useState(false)
  const [error, setError] = useState('')
  const [showAllSkills, setShowAllSkills] = useState(false)

  useEffect(() => {
    if (skills.length === 0) return
    setLoadingOverview(true)
    api.post('/api/gap/analyze', { skills })
      .then((res) => setOverview(res.data.data))
      .catch((e) => setError(e.response?.data?.message || 'Analysis failed.'))
      .finally(() => setLoadingOverview(false))
  }, [skills])

  const selectRole = async (role) => {
    setSelectedRole(role)
    setLoadingDive(true)
    setDeepDive(null)
    try {
      const encoded = encodeURIComponent(role)
      const res = await api.post(`/api/gap/analyze/${encoded}`, { skills })
      setDeepDive(res.data.data)
    } catch (e) {
      setError(e.response?.data?.message || 'Deep dive failed.')
    } finally {
      setLoadingDive(false)
    }
  }

  const goToRoadmap = () => {
    if (!deepDive) return
    setTargetRole(selectedRole)
    setMissingSkills(deepDive.missing_critical_skills || [])
    navigate('/roadmap')
  }

  if (skills.length === 0) {
    return (
      <div className="flex flex-col items-center gap-5 py-20 text-center">
        <div
          className="flex h-20 w-20 items-center justify-center rounded-2xl text-3xl neu-raised"
          style={{ backgroundColor: 'var(--c-surface)' }}
        >
          📄
        </div>
        <h2 className="text-lg font-bold" style={{ color: 'var(--c-text)' }}>No skills loaded</h2>
        <p className="text-xs" style={{ color: 'var(--c-muted)' }}>Upload your resume first to analyse your skill gap.</p>
        <Button onClick={() => navigate('/upload')}>Upload Resume</Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
            Skill Gap Analysis
          </p>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>
            {skills.length} skills analysed
          </h1>
          <p className="mt-1 text-xs" style={{ color: 'var(--c-muted)' }}>
            Click a role card to dive deeper
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate('/predict')}>Predict career</Button>
          <Button variant="secondary" onClick={() => navigate('/upload')}>Re-upload</Button>
        </div>
      </div>

      {error && (
        <div
          className="rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
          style={{ color: 'var(--c-danger)', backgroundColor: 'var(--c-surface)' }}
        >
          {error}
        </div>
      )}

      {loadingOverview && (
        <div className="flex items-center gap-3" style={{ color: 'var(--c-muted)' }}>
          <Spinner />
          <span className="text-xs font-bold uppercase tracking-widest">Analysing your skills…</span>
        </div>
      )}

      {overview && (
        <>
          {/* Readiness summary */}

          {/* Role cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {overview.top_5_matches?.map((match) => {
              const isSelected = selectedRole === match.role
              return (
                <button
                  key={match.role}
                  onClick={() => selectRole(match.role)}
                  className="rounded-2xl p-5 text-left transition-all"
                  style={{
                    backgroundColor: 'var(--c-surface)',
                    boxShadow: isSelected
                      ? `inset 4px 4px 9px #C8C6C5, inset -4px -4px 9px #FFFFFF, 0 0 0 2px var(--c-primary)`
                      : '6px 6px 14px #C8C6C5, -6px -6px 14px #FFFFFF',
                    color: 'var(--c-text)',
                  }}
                >
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <span className="text-xs font-bold uppercase tracking-wide" style={{ color: isSelected ? 'var(--c-primary)' : 'var(--c-text)' }}>
                      #{match.rank} {match.role}
                    </span>
                    <span className="text-sm font-bold" style={{ color: 'var(--c-primary)' }}>
                      {match.match_percentage?.toFixed(1)}%
                    </span>
                  </div>
                  <ProgressBar
                    value={match.match_percentage}
                    color="var(--c-primary)"
                    className="mb-3"
                  />
                  <div className="flex gap-4 text-xs" style={{ color: 'var(--c-muted)' }}>
                    
                  </div>
                </button>
              )
            })}
          </div>
        </>
      )}

      {/* Deep dive */}
      {selectedRole && (
        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
                Deep dive
              </p>
              <h2 className="text-xl font-bold" style={{ color: 'var(--c-text)' }}>
                {selectedRole}
              </h2>
            </div>
            {deepDive && (
              <Button onClick={goToRoadmap}>Generate roadmap →</Button>
            )}
          </div>

          {loadingDive && (
            <div className="flex items-center gap-3" style={{ color: 'var(--c-muted)' }}>
              <Spinner />
              <span className="text-xs font-bold uppercase tracking-widest">Loading deep dive…</span>
            </div>
          )}

          {deepDive && (
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <div
                className="rounded-2xl p-6 neu-raised"
                style={{ backgroundColor: 'var(--c-surface)' }}
              >
                <p className="mb-4 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
                  Matching skills 
                </p>
                <div className="flex flex-wrap gap-2">
                  {deepDive.matching_skills?.map((s) => (
                    <SkillTag
                      key={s}
                      skill={s}
                      style={{ color: 'var(--c-success)' }}
                    />
                  ))}
                </div>
                <p className="mb-4 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
                  These are your skills that are Related to this Career
                </p>
              </div>

              <div
                className="rounded-2xl p-6 neu-raised"
                style={{ backgroundColor: 'var(--c-surface)' }}
              >
                <p className="mb-4 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
                  Missing critical skills
                </p>
                <div className="flex flex-col gap-3">
                  {(showAllSkills
                    ? deepDive.missing_critical_skills
                    : deepDive.missing_critical_skills?.slice(0, 6)
                  )?.map((ms) => (
                    <div key={ms.skill} className="flex items-center gap-3">
                      <span
                        className="w-28 truncate text-xs font-bold uppercase tracking-wide capitalize"
                        style={{ color: 'var(--c-text)' }}
                      >
                        {ms.skill}
                      </span>
                      <div className="flex-1">
                        <ProgressBar value={ms.frequency_pct} />
                      </div>
                      <span className="text-xs font-bold" style={{ color: 'var(--c-muted)' }}>
                        {ms.frequency_pct?.toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
                {deepDive.missing_critical_skills?.length > 6 && (
                  <button
                    onClick={() => setShowAllSkills((v) => !v)}
                    className="mt-4 w-full rounded-xl py-2 text-xs font-bold uppercase tracking-widest transition-all neu-pressed-sm"
                    style={{ color: 'var(--c-primary)', backgroundColor: 'var(--c-surface)' }}
                  >
                    {showAllSkills
                      ? '↑ Show less'
                      : `↓ ${deepDive.missing_critical_skills.length - 6} more skills`}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
