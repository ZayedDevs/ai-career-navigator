import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../lib/api'
import { useFlow } from '../context/FlowContext'
import Button from '../components/ui/Button'
import Spinner from '../components/ui/Spinner'

const PRIORITY = {
  critical: { color: 'var(--c-danger)',  label: 'Critical' },
  high:     { color: 'var(--c-warning)', label: 'High'     },
  medium:   { color: '#c09000',          label: 'Medium'   },
  low:      { color: 'var(--c-primary)', label: 'Low'      },
}

const PHASE_ACCENT = {
  1: { color: 'var(--c-success)',  hex: '#00A63D', dim: 'rgba(0,166,61,0.12)'  },
  2: { color: 'var(--c-warning)', hex: '#FE9900', dim: 'rgba(254,153,0,0.12)' },
  3: { color: 'var(--c-primary)', hex: '#006666', dim: 'rgba(0,102,102,0.12)' },
}

const PLATFORM_BADGE = {
  udemy:    { color: '#7C3AED', dim: 'rgba(124,58,237,0.12)' },
  coursera: { color: '#2563EB', dim: 'rgba(37,99,235,0.12)' },
}

const TIERS = [
  { key: 'free',     emoji: '🆓', label: 'Free'     },
  { key: 'udemy',    emoji: '💰', label: 'Udemy'    },
  { key: 'coursera', emoji: '🎓', label: 'Coursera' },
]

function renderStars(rating) {
  if (rating == null) return null
  return `⭐ ${rating.toFixed(1)}`
}

function normalizeResources(resources) {
  if (Array.isArray(resources)) {
    return { free: resources, udemy: [], coursera: [] }
  }
  return {
    free: resources?.free ?? [],
    udemy: resources?.udemy ?? [],
    coursera: resources?.coursera ?? [],
  }
}

/* ── Single resource card ── */
function ResourceCard({ resource: r, tier }) {
  const badge = PLATFORM_BADGE[tier]
  return (
    <a
      href={r.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex gap-3 rounded-xl p-2 transition-all neu-pressed-sm"
      style={{ backgroundColor: 'var(--c-surface)' }}
    >
      {tier === 'free' && r.thumbnail && (
        <img
          src={r.thumbnail}
          alt={r.title}
          className="h-10 w-16 shrink-0 rounded-lg object-cover"
        />
      )}
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <p className="text-xs font-bold line-clamp-2" style={{ color: 'var(--c-text)' }}>
            {r.title}
          </p>
          {badge && (
            <span
              className="shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide"
              style={{ color: badge.color, backgroundColor: badge.dim }}
            >
              {r.platform}
            </span>
          )}
        </div>
        {tier === 'free' && (
          <p className="text-xs mt-0.5" style={{ color: 'var(--c-muted)' }}>
            {r.channel} · {r.platform}
          </p>
        )}
        {tier === 'udemy' && (
          <p className="text-xs mt-0.5" style={{ color: 'var(--c-muted)' }}>
            {[renderStars(r.rating), r.difficulty].filter(Boolean).join(' · ')}
          </p>
        )}
        {tier === 'coursera' && (
          <p className="text-xs mt-0.5" style={{ color: 'var(--c-muted)' }}>
            {[r.organization, renderStars(r.rating), r.duration].filter(Boolean).join(' · ')}
          </p>
        )}
      </div>
    </a>
  )
}

/* ── One tier (Free / Udemy / Coursera) ── */
function TierBlock({ emoji, label, items, tier }) {
  if (!items?.length) return null
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-bold uppercase tracking-wide" style={{ color: 'var(--c-muted)' }}>
        {emoji} {label}
      </p>
      <div className="flex flex-col gap-2">
        {items.map((r, i) => (
          <ResourceCard key={i} resource={r} tier={tier} />
        ))}
      </div>
    </div>
  )
}

/* ── Resource accordion (all tiers) ── */
function ResourceSection({ free, udemy, coursera, totalCount }) {
  const [open, setOpen] = useState(false)
  if (!totalCount) return null
  const byTier = { free, udemy, coursera }
  return (
    <div className="border-t mt-3 pt-3" style={{ borderColor: 'rgba(0,0,0,0.07)' }}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-xs font-bold uppercase tracking-widest transition-colors"
        style={{ color: 'var(--c-muted)' }}
      >
        <span>Resources ({totalCount})</span>
        <span
          className="transition-transform duration-200"
          style={{ display: 'inline-block', transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}
        >
          ▾
        </span>
      </button>
      {open && (
        <div className="mt-2 flex flex-col gap-3">
          {TIERS.map(({ key, emoji, label }) => (
            <TierBlock key={key} emoji={emoji} label={label} items={byTier[key]} tier={key} />
          ))}
        </div>
      )}
    </div>
  )
}

/* ── Skill card ── */
function SkillCard({ skill, learned, marking, onMark, phaseColor, index }) {
  const priority = PRIORITY[skill.priority] ?? PRIORITY.low
  const { free, udemy, coursera } = normalizeResources(skill.resources)
  const totalCount = skill.resource_count?.total ?? (free.length + udemy.length + coursera.length)
  return (
    <div
      className="rounded-xl overflow-hidden transition-all animate-neu-rise"
      style={{
        backgroundColor: 'var(--c-surface)',
        boxShadow: learned
          ? 'inset 3px 3px 7px #C8C6C5, inset -3px -3px 7px #FFFFFF'
          : '4px 4px 10px #C8C6C5, -4px -4px 10px #FFFFFF',
        opacity: learned ? 0.65 : 1,
        animationDelay: `${0.08 * index}s`,
      }}
    >
      {/* Priority colour bar — left edge */}
      <div className="flex">
        <div className="w-1 shrink-0 rounded-l-xl" style={{ backgroundColor: priority.color }} />
        <div className="flex-1 p-4">

          {/* Top row: name + action */}
          <div className="flex items-start justify-between gap-2">
            <span
              className="text-xs font-bold uppercase tracking-wide capitalize leading-snug"
              style={{ color: 'var(--c-text)' }}
            >
              {skill.skill}
            </span>
            {learned ? (
              <span
                className="shrink-0 rounded-full px-2 py-0.5 text-xs font-bold uppercase tracking-wide"
                style={{ color: 'var(--c-success)', backgroundColor: 'rgba(0,166,61,0.10)' }}
              >
                ✓ Learned
              </span>
            ) : (
              <Button
                variant="secondary"
                className="shrink-0 py-1 px-2.5 text-xs"
                loading={marking}
                onClick={() => onMark(skill.skill)}
              >
                Mark learned
              </Button>
            )}
          </div>

          {/* Meta row */}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span
              className="rounded-full px-2 py-0.5 text-xs font-bold uppercase tracking-wide"
              style={{ color: priority.color, backgroundColor: `${priority.color}14` }}
            >
              {priority.label}
            </span>
            <span
              className="rounded-full px-2 py-0.5 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
              style={{ color: 'var(--c-muted)', backgroundColor: 'var(--c-surface)' }}
            >
              {skill.estimated_weeks}w
            </span>
            <span
              className="rounded-full px-2 py-0.5 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
              style={{ color: 'var(--c-muted)', backgroundColor: 'var(--c-surface)' }}
            >
              {skill.frequency_pct?.toFixed(1)}% jobs
            </span>
          </div>

          <ResourceSection free={free} udemy={udemy} coursera={coursera} totalCount={totalCount} />
        </div>
      </div>
    </div>
  )
}

/* ── Phase header ── */
function PhaseHeader({ phase, accent, doneCount }) {
  return (
    <div className="flex items-center gap-4">
      {/* Circle node */}
      <div
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white text-sm font-bold neu-teal-sm"
        style={{ backgroundColor: accent.color }}
      >
        {phase.phase}
      </div>

      {/* Label block */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-baseline gap-2">
          <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--c-text)' }}>
            {phase.tier}
          </h2>
          <span className="text-xs" style={{ color: 'var(--c-muted)' }}>
            {phase.description}
          </span>
        </div>
        <div className="mt-1 flex flex-wrap gap-3 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
          <span>{phase.duration_weeks} weeks</span>
          <span>·</span>
          <span>{phase.skill_count} skills</span>
          <span>·</span>
          <span style={{ color: doneCount > 0 ? accent.color : 'var(--c-muted)' }}>
            {doneCount}/{phase.skill_count} done
          </span>
        </div>
      </div>

      {/* Horizontal rule */}
      <div className="flex-1 h-px" style={{ backgroundColor: accent.hex + '40' }} />
    </div>
  )
}

/* ── Toast ── */
function Toast({ message, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3500)
    return () => clearTimeout(t)
  }, [onClose])
  return (
    <div
      className="fixed bottom-6 right-6 z-50 rounded-2xl px-5 py-3 text-xs font-bold uppercase tracking-wide neu-raised"
      style={{ backgroundColor: 'var(--c-surface)', color: 'var(--c-success)' }}
    >
      ✓ {message}
    </div>
  )
}

/* ══════════════════════════════════════════════════════ */
export default function Roadmap() {
  const { targetRole, missingSkills } = useFlow()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const savedId = searchParams.get('id')   // present when opening a saved roadmap

  const [roadmap, setRoadmap]         = useState(null)
  const [loading, setLoading]         = useState(false)
  const [saving, setSaving]           = useState(false)
  const [error, setError]             = useState('')
  const [toast, setToast]             = useState('')
  const [learnedSkills, setLearned]   = useState(new Set())
  const [markingSkill, setMarking]    = useState(null)

  /* Load saved roadmap by ID */
  useEffect(() => {
    if (!savedId) return
    setLoading(true)
    Promise.all([
      api.get(`/api/dashboard/roadmaps/${savedId}`),
      api.get('/api/dashboard/progress'),
    ])
      .then(([rmRes, prRes]) => {
        setRoadmap(rmRes.data.data)
        const learned = new Set(
          (prRes.data.data.progress ?? [])
            .filter((p) => p.status === 'learned')
            .map((p) => p.skill)
        )
        setLearned(learned)
      })
      .catch((e) => setError(e.response?.data?.message || 'Failed to load roadmap.'))
      .finally(() => setLoading(false))
  }, [savedId])

  /* Generate new roadmap from flow context */
  useEffect(() => {
    if (savedId) return                          // handled above
    if (!targetRole || missingSkills.length === 0) return
    setLoading(true)
    api.post('/api/roadmap/generate', {
      target_role: targetRole,
      missing_skills: missingSkills,
      max_skills: 8,
      include_resources: true,
    })
      .then((res) => setRoadmap(res.data.data))
      .catch((e) => setError(e.response?.data?.message || 'Failed to generate roadmap.'))
      .finally(() => setLoading(false))
  }, [savedId, targetRole, missingSkills])

  const handleSave = async () => {
    if (!roadmap) return
    setSaving(true)
    try {
      await api.post('/api/dashboard/roadmaps', roadmap)
      setToast('Roadmap saved to dashboard!')
    } catch (e) {
      setError(e.response?.data?.message || 'Save failed.')
    } finally {
      setSaving(false)
    }
  }

  const markLearned = async (skill) => {
    setMarking(skill)
    try {
      const res = await api.post('/api/dashboard/progress', { skill, status: 'learned' })
      setLearned((prev) => new Set([...prev, skill]))
      setToast(
        res.data.data?.added_to_active_skills
          ? `"${skill}" learned & added to active skills!`
          : `"${skill}" marked as learned!`
      )
    } catch (e) {
      setError(e.response?.data?.message || 'Could not mark skill.')
    } finally {
      setMarking(null)
    }
  }

  /* ── Empty states (only for new-generation flow, not saved roadmaps) ── */
  if (!savedId && !targetRole) {
    return (
      <div className="flex flex-col items-center gap-5 py-20 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl text-3xl neu-raised"
             style={{ backgroundColor: 'var(--c-surface)' }}>🗺️</div>
        <h2 className="text-lg font-bold" style={{ color: 'var(--c-text)' }}>No role selected</h2>
        <p className="text-xs" style={{ color: 'var(--c-muted)' }}>
          Go to Skill Gap and pick a role to generate a roadmap.
        </p>
        <Button onClick={() => navigate('/gap')}>Analyse skill gap</Button>
      </div>
    )
  }

  if (!savedId && missingSkills.length === 0) {
    return (
      <div className="flex flex-col items-center gap-5 py-20 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl text-3xl neu-raised"
             style={{ backgroundColor: 'var(--c-surface)' }}>✅</div>
        <h2 className="text-lg font-bold" style={{ color: 'var(--c-text)' }}>No missing skills!</h2>
        <p className="text-xs" style={{ color: 'var(--c-muted)' }}>
          You already match all critical skills for <strong>{targetRole}</strong>.
        </p>
        <Button onClick={() => navigate('/gap')}>Back to gap analysis</Button>
      </div>
    )
  }

  /* ── Main view ── */
  const totalLearned = learnedSkills.size

  return (
    <div className="flex flex-col gap-8">
      {toast && <Toast message={toast} onClose={() => setToast('')} />}

      {/* ── Page header ── */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
            Learning Roadmap
          </p>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>
            {targetRole}
          </h1>
        </div>
        <div className="flex gap-2">
          {roadmap && (
            <Button loading={saving} onClick={handleSave} variant="secondary">
              Save to dashboard
            </Button>
          )}
          <Button variant="outline" onClick={() => navigate(savedId ? '/my-learning/roadmaps' : '/gap')}>← Back</Button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
             style={{ color: 'var(--c-danger)', backgroundColor: 'var(--c-surface)' }}>
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-3" style={{ color: 'var(--c-muted)' }}>
          <Spinner />
          <span className="text-xs font-bold uppercase tracking-widest">Generating roadmap…</span>
        </div>
      )}

      {roadmap && (
        <>
          {/* ── Stats bar ── */}
          <div
            className="grid grid-cols-2 gap-3 rounded-2xl p-5 sm:grid-cols-4 animate-neu-rise neu-raised"
            style={{ backgroundColor: 'var(--c-surface)' }}
          >
            {[
              { label: 'Total skills',   value: roadmap.skill_count,             accent: 'var(--c-primary)' },
              { label: 'Phases',         value: roadmap.phase_count,             accent: 'var(--c-primary)' },
              { label: 'Duration',       value: `${roadmap.total_weeks}w`,       accent: 'var(--c-warning)' },
              { label: 'Skills learned', value: `${totalLearned}/${roadmap.skill_count}`, accent: 'var(--c-success)' },
            ].map((s) => (
              <div key={s.label} className="text-center">
                <p className="text-xl font-bold" style={{ color: s.accent }}>{s.value}</p>
                <p className="mt-0.5 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
                  {s.label}
                </p>
              </div>
            ))}
          </div>

          {/* ── Phases ── */}
          <div className="flex flex-col gap-10">
            {roadmap.phases?.map((phase, pi) => {
              const accent = PHASE_ACCENT[phase.phase] ?? PHASE_ACCENT[3]
              const doneCount = phase.skills?.filter((s) => learnedSkills.has(s.skill)).length ?? 0
              let skillIndex = 0
              return (
                <div
                  key={phase.phase}
                  className="animate-neu-rise"
                  style={{ animationDelay: `${0.1 + pi * 0.12}s` }}
                >
                  {/* Phase divider */}
                  <PhaseHeader phase={phase} accent={accent} doneCount={doneCount} />

                  {/* Skill grid */}
                  <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {phase.skills?.map((skill) => {
                      const idx = skillIndex++
                      return (
                        <SkillCard
                          key={skill.skill}
                          skill={skill}
                          learned={learnedSkills.has(skill.skill)}
                          marking={markingSkill === skill.skill}
                          onMark={markLearned}
                          phaseColor={accent.color}
                          index={idx}
                        />
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
