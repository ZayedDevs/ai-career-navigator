import { useState, useEffect, useRef } from 'react'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import api from '../lib/api'
import { useAuth } from '../context/AuthContext'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Textarea from '../components/ui/Textarea'
import SkillTag from '../components/ui/SkillTag'
import Spinner from '../components/ui/Spinner'
import CVPreview from '../components/cv/CVPreview'

const emptyProfile = () => ({
  personal: { name: '', title: '', email: '', phone: '', location: '', linkedin: '', github: '' },
  summary: '',
  skills: [],
  expertise: [],
  education: [],
  experience: [],
  projects: [],
  certifications: [],
})

function Section({ title, children }) {
  return (
    <div className="rounded-2xl p-6 neu-raised flex flex-col gap-4" style={{ backgroundColor: 'var(--c-surface)' }}>
      <h3 className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
        {title}
      </h3>
      {children}
    </div>
  )
}

function TagField({ items, onAdd, onRemove }) {
  const [value, setValue] = useState('')

  const add = () => {
    const v = value.trim()
    if (v && !items.includes(v)) onAdd(v)
    setValue('')
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <SkillTag key={item} skill={item} removable onRemove={onRemove} />
        ))}
        {items.length === 0 && (
          <p className="text-xs" style={{ color: 'var(--c-muted)' }}>None yet.</p>
        )}
      </div>
      <div className="flex gap-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), add())}
          placeholder="Add…"
          className="flex-1 rounded-xl border-0 px-4 py-2.5 text-xs font-bold uppercase tracking-wide outline-none neu-pressed"
          style={{ backgroundColor: 'var(--c-surface)', color: 'var(--c-text)' }}
        />
        <Button variant="secondary" type="button" onClick={add}>Add</Button>
      </div>
    </div>
  )
}

function SuggestedSkills({ suggestions, onAdd }) {
  if (suggestions.length === 0) return null
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
        Suggested from your learning
      </p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((skill) => (
          <button
            key={skill}
            type="button"
            onClick={() => onAdd(skill)}
            className="inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wide neu-raised-sm transition-all"
            style={{ backgroundColor: 'var(--c-surface)', color: 'var(--c-primary)' }}
          >
            <span>✨</span>{skill}
          </button>
        ))}
      </div>
    </div>
  )
}

export default function CVBuilder() {
  const { user } = useAuth()

  const [profile, setProfile] = useState(null)
  const [activeSkills, setActiveSkills] = useState([])
  const [autofillDraft, setAutofillDraft] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saveStatus, setSaveStatus] = useState('idle') // idle | saving | saved
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState('')

  const dirty = useRef(false)
  const saveTimer = useRef(null)
  const previewScaleRef = useRef(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const [skillsRes, draftRes, profileRes] = await Promise.all([
          api.get('/api/cv/skills').catch(() => null),
          api.get('/api/cv/autofill-draft').catch(() => null),
          api.get('/api/cv/profile'),
        ])

        setActiveSkills(skillsRes?.data.data.active_skills ?? [])
        setAutofillDraft(draftRes?.data.data ?? null)

        const fetched = profileRes.data.data

        if (fetched) {
          setProfile(fetched)
        } else {
          const blank = emptyProfile()
          blank.personal.name = user?.name ?? ''
          blank.personal.email = user?.email ?? ''
          setProfile(blank)
        }
      } catch (e) {
        setError(e.response?.data?.message || 'Failed to load CV profile.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [user])

  useEffect(() => {
    if (!dirty.current || !profile) return

    setSaveStatus('saving')
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(async () => {
      try {
        const res = await api.post('/api/cv/profile', profile)
        setProfile(res.data.data)
        setSaveStatus('saved')
      } catch {
        setSaveStatus('idle')
      }
    }, 2000)

    return () => clearTimeout(saveTimer.current)
  }, [profile])

  const mutate = (updater) => {
    dirty.current = true
    setProfile((prev) => updater(prev))
  }

  const handleAutofill = () => {
    if (!autofillDraft) return
    mutate((prev) => {
      const mergedPersonal = { ...prev.personal }
      for (const [key, value] of Object.entries(autofillDraft.personal || {})) {
        if (mergedPersonal[key] === '' && value) mergedPersonal[key] = value
      }
      return {
        ...prev,
        personal: mergedPersonal,
        skills: Array.from(new Set([...prev.skills, ...(autofillDraft.skills || [])])),
      }
    })
  }

  const updatePersonal = (field, value) =>
    mutate((prev) => ({ ...prev, personal: { ...prev.personal, [field]: value } }))

  const updateField = (field, value) => mutate((prev) => ({ ...prev, [field]: value }))

  const addTag = (field, value) => mutate((prev) => ({ ...prev, [field]: [...prev[field], value] }))
  const removeTag = (field, value) =>
    mutate((prev) => ({ ...prev, [field]: prev[field].filter((v) => v !== value) }))

  const updateListItem = (field, index, patch) =>
    mutate((prev) => ({
      ...prev,
      [field]: prev[field].map((item, i) => (i === index ? { ...item, ...patch } : item)),
    }))

  const addListItem = (field, item) => mutate((prev) => ({ ...prev, [field]: [...prev[field], item] }))
  const removeListItem = (field, index) =>
    mutate((prev) => ({ ...prev, [field]: prev[field].filter((_, i) => i !== index) }))

  const bulletsToLines = (bullets) => (bullets ?? []).join('\n')
  const linesToBullets = (text) => text.split('\n')
  const cleanBullets = (text) => text.split('\n').map((l) => l.trim()).filter(Boolean)

  const handleDownloadPdf = async () => {
    setExporting(true)
    const scaleWrapper = previewScaleRef.current
    const prevTransform = scaleWrapper?.style.transform
    const prevMarginBottom = scaleWrapper?.style.marginBottom
    try {
      if (scaleWrapper) {
        scaleWrapper.style.transform = 'none'
        scaleWrapper.style.marginBottom = '0'
      }
      const node = document.getElementById('cv-preview-content')
      const canvas = await html2canvas(node, { scale: 2, backgroundColor: '#ffffff', useCORS: true })
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait' })
      const pdfWidth = 210
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
      const safeName = (profile?.personal?.name || 'CV').trim().replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_-]/g, '')
      pdf.save(`CV_${safeName || 'Untitled'}.pdf`)
    } catch {
      setError('Failed to generate PDF.')
    } finally {
      if (scaleWrapper) {
        scaleWrapper.style.transform = prevTransform ?? ''
        scaleWrapper.style.marginBottom = prevMarginBottom ?? ''
      }
      setExporting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Spinner size="lg" />
      </div>
    )
  }

  const suggestions = activeSkills.filter((s) => !profile.skills.includes(s))

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
            CV Builder
          </p>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>
            Build your CV
          </h1>
        </div>
        <div className="flex items-center gap-4">
          {saveStatus !== 'idle' && (
            <span
              className="text-xs font-bold uppercase tracking-widest"
              style={{ color: saveStatus === 'saving' ? 'var(--c-muted)' : 'var(--c-success)' }}
            >
              {saveStatus === 'saving' ? 'Saving…' : 'Saved ✓'}
            </span>
          )}
          {autofillDraft && (
            <Button variant="secondary" onClick={handleAutofill}>
              Autofill from previous CV
            </Button>
          )}
          <Button onClick={handleDownloadPdf} loading={exporting}>
            Download PDF
          </Button>
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* LEFT: editor */}
        <div className="flex flex-col gap-5">
          <Section title="Personal Info">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input label="Name" value={profile.personal.name} onChange={(e) => updatePersonal('name', e.target.value)} />
              <Input label="Title" value={profile.personal.title} onChange={(e) => updatePersonal('title', e.target.value)} />
              <Input label="Email" value={profile.personal.email} onChange={(e) => updatePersonal('email', e.target.value)} />
              <Input label="Phone" value={profile.personal.phone} onChange={(e) => updatePersonal('phone', e.target.value)} />
              <Input label="Location" value={profile.personal.location} onChange={(e) => updatePersonal('location', e.target.value)} />
              <Input label="LinkedIn" value={profile.personal.linkedin} onChange={(e) => updatePersonal('linkedin', e.target.value)} />
              <Input label="GitHub" value={profile.personal.github} onChange={(e) => updatePersonal('github', e.target.value)} />
            </div>
          </Section>

          <Section title="Professional Summary">
            <Textarea rows={5} value={profile.summary} onChange={(e) => updateField('summary', e.target.value)} />
          </Section>

          <Section title="Skills">
            <SuggestedSkills suggestions={suggestions} onAdd={(v) => addTag('skills', v)} />
            <TagField
              items={profile.skills}
              onAdd={(v) => addTag('skills', v)}
              onRemove={(v) => removeTag('skills', v)}
            />
          </Section>

          <Section title="Area of Expertise">
            <TagField
              items={profile.expertise}
              onAdd={(v) => addTag('expertise', v)}
              onRemove={(v) => removeTag('expertise', v)}
            />
          </Section>

          <Section title="Experience">
            <div className="flex flex-col gap-4">
              {profile.experience.map((exp, i) => (
                <div key={i} className="rounded-xl p-4 neu-pressed-sm flex flex-col gap-2">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <Input label="Title" value={exp.title} onChange={(e) => updateListItem('experience', i, { title: e.target.value })} />
                    <Input label="Company" value={exp.company} onChange={(e) => updateListItem('experience', i, { company: e.target.value })} />
                    <Input label="Period" value={exp.period} onChange={(e) => updateListItem('experience', i, { period: e.target.value })} />
                  </div>
                  <Textarea
                    label="Bullets (one per line)"
                    rows={3}
                    value={bulletsToLines(exp.bullets)}
                    onChange={(e) => updateListItem('experience', i, { bullets: linesToBullets(e.target.value) })}
                    onBlur={(e) => updateListItem('experience', i, { bullets: cleanBullets(e.target.value) })}
                  />
                  <Button variant="danger" type="button" className="self-start text-xs py-1.5 px-3" onClick={() => removeListItem('experience', i)}>
                    Remove
                  </Button>
                </div>
              ))}
              <Button
                variant="secondary"
                type="button"
                className="self-start"
                onClick={() => addListItem('experience', { title: '', company: '', period: '', bullets: [] })}
              >
                + Add Experience
              </Button>
            </div>
          </Section>

          <Section title="Projects">
            <div className="flex flex-col gap-4">
              {profile.projects.map((p, i) => (
                <div key={i} className="rounded-xl p-4 neu-pressed-sm flex flex-col gap-2">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <Input label="Name" value={p.name} onChange={(e) => updateListItem('projects', i, { name: e.target.value })} />
                    <Input label="Role" value={p.role} onChange={(e) => updateListItem('projects', i, { role: e.target.value })} />
                    <Input label="Period" value={p.period} onChange={(e) => updateListItem('projects', i, { period: e.target.value })} />
                  </div>
                  <Textarea
                    label="Bullets (one per line)"
                    rows={3}
                    value={bulletsToLines(p.bullets)}
                    onChange={(e) => updateListItem('projects', i, { bullets: linesToBullets(e.target.value) })}
                    onBlur={(e) => updateListItem('projects', i, { bullets: cleanBullets(e.target.value) })}
                  />
                  <Button variant="danger" type="button" className="self-start text-xs py-1.5 px-3" onClick={() => removeListItem('projects', i)}>
                    Remove
                  </Button>
                </div>
              ))}
              <Button
                variant="secondary"
                type="button"
                className="self-start"
                onClick={() => addListItem('projects', { name: '', period: '', role: '', bullets: [] })}
              >
                + Add Project
              </Button>
            </div>
          </Section>

          <Section title="Education">
            <div className="flex flex-col gap-4">
              {profile.education.map((edu, i) => (
                <div key={i} className="rounded-xl p-4 neu-pressed-sm flex flex-col gap-2">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <Input label="Degree" value={edu.degree} onChange={(e) => updateListItem('education', i, { degree: e.target.value })} />
                    <Input label="Institution" value={edu.institution} onChange={(e) => updateListItem('education', i, { institution: e.target.value })} />
                    <Input label="Period" value={edu.period} onChange={(e) => updateListItem('education', i, { period: e.target.value })} />
                    <Input label="CGPA" value={edu.cgpa} onChange={(e) => updateListItem('education', i, { cgpa: e.target.value })} />
                  </div>
                  <Button variant="danger" type="button" className="self-start text-xs py-1.5 px-3" onClick={() => removeListItem('education', i)}>
                    Remove
                  </Button>
                </div>
              ))}
              <Button
                variant="secondary"
                type="button"
                className="self-start"
                onClick={() => addListItem('education', { degree: '', institution: '', period: '', cgpa: '' })}
              >
                + Add Education
              </Button>
            </div>
          </Section>

          <Section title="Certifications">
            <TagField
              items={profile.certifications}
              onAdd={(v) => addTag('certifications', v)}
              onRemove={(v) => removeTag('certifications', v)}
            />
          </Section>
        </div>

        {/* RIGHT: live preview */}
        <div className="sticky top-6">
          <div
            className="rounded-2xl p-4 neu-raised overflow-auto"
            style={{ backgroundColor: 'var(--c-surface)', maxHeight: 'calc(100vh - 3rem)' }}
          >
            <div
              ref={previewScaleRef}
              style={{
                transform: 'scale(0.62)',
                transformOrigin: 'top left',
                width: '210mm',
                marginBottom: '-113mm',
              }}
            >
              <CVPreview profile={profile} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
