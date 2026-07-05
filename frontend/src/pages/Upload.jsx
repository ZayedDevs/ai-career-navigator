import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import { useFlow } from '../context/FlowContext'
import Button from '../components/ui/Button'
import SkillTag from '../components/ui/SkillTag'
import Spinner from '../components/ui/Spinner'

const MAX_SIZE = 10 * 1024 * 1024

export default function Upload() {
  const { setSkills } = useFlow()
  const navigate = useNavigate()
  const inputRef = useRef(null)

  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [editedSkills, setEditedSkills] = useState([])
  const [newSkill, setNewSkill] = useState('')
  const [continuing, setContinuing] = useState(false)

  const validateFile = (file) => {
    if (!file) return 'No file selected.'
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx'].includes(ext)) return 'Only PDF and DOCX files are accepted.'
    if (file.size > MAX_SIZE) return 'File must be under 10 MB.'
    return null
  }

  const uploadFile = async (file) => {
    const err = validateFile(file)
    if (err) { setError(err); return }
    setError('')
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('resume', file)
      const [res] = await Promise.all([
        api.post('/api/resume/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        }),
        new Promise((resolve) => setTimeout(resolve, 10000)),
      ])
      const data = res.data.data
      setResult({ filename: data.filename, skillCount: data.skill_count })
      setEditedSkills(data.skills)
    } catch (e) {
      setError(e.response?.data?.message || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleFileInput = (e) => {
    const file = e.target.files?.[0]
    if (file) uploadFile(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) uploadFile(file)
  }

  const removeSkill = (skill) => setEditedSkills((s) => s.filter((x) => x !== skill))

  const addSkill = () => {
    const s = newSkill.trim().toLowerCase()
    if (s && !editedSkills.includes(s)) setEditedSkills((prev) => [...prev, s])
    setNewSkill('')
  }

  const handleContinue = async () => {
    setContinuing(true)
    setSkills(editedSkills)
    try {
      await api.post('/api/dashboard/analyses', {
        filename: result.filename,
        extracted_skills: editedSkills,
        overall_readiness: null,
        predicted_career: null,
        target_role: null,
        top_matches: [],
      })
    } catch { /* non-critical */ }
    navigate('/gap')
  }

  if (result) {
    return (
      <div className="flex flex-col gap-6">
        <div className="animate-neu-rise" style={{ animationDelay: '0s' }}>
          <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
            Step 1 complete
          </p>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>
            Skills extracted
          </h1>
          <p className="mt-1 text-xs" style={{ color: 'var(--c-muted)' }}>
            Found <strong style={{ color: 'var(--c-primary)' }}>{result.skillCount}</strong> skills in{' '}
            <em>{result.filename}</em>. Edit the list before continuing.
          </p>
        </div>

        <div
          className="rounded-2xl p-6 neu-raised animate-neu-rise"
          style={{ backgroundColor: 'var(--c-surface)', animationDelay: '0.1s' }}
        >
          <div className="mb-5 flex flex-wrap gap-2">
            {editedSkills.map((skill, i) => (
              <span
                key={skill}
                className="animate-neu-extrude"
                style={{ animationDelay: `${0.05 * i}s` }}
              >
                <SkillTag skill={skill} removable onRemove={removeSkill} />
              </span>
            ))}
            {editedSkills.length === 0 && (
              <p className="text-xs" style={{ color: 'var(--c-muted)' }}>No skills yet. Add some below.</p>
            )}
          </div>
          <div className="flex gap-2">
            <input
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addSkill()}
              placeholder="Add a skill…"
              className="flex-1 rounded-xl border-0 px-4 py-2.5 text-xs font-bold uppercase tracking-wide outline-none neu-pressed"
              style={{
                backgroundColor: 'var(--c-surface)',
                color: 'var(--c-text)',
              }}
            />
            <Button variant="secondary" onClick={addSkill}>Add</Button>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button onClick={handleContinue} loading={continuing} disabled={editedSkills.length === 0 || continuing}>
            Analyse skill gap →
          </Button>
          <Button variant="outline" onClick={() => navigate('/predict')}>
            Predict career →
          </Button>
          <Button variant="secondary" onClick={() => { setResult(null); setEditedSkills([]) }}>
            Upload another
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="mb-1 text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
          Step 1
        </p>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--c-text)' }}>
          Upload your resume
        </h1>
        <p className="mt-1 text-xs" style={{ color: 'var(--c-muted)' }}>
          PDF or DOCX · max 10 MB · skills extracted automatically
        </p>
      </div>

      {error && (
        <div
          className="rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
          style={{ color: 'var(--c-danger)', backgroundColor: 'var(--c-surface)' }}
        >
          {error}
        </div>
      )}

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        className="flex min-h-64 cursor-pointer flex-col items-center justify-center gap-5 rounded-2xl transition-all"
        style={{
          backgroundColor: 'var(--c-surface)',
          boxShadow: dragging
            ? 'inset 4px 4px 9px #C8C6C5, inset -4px -4px 9px #FFFFFF, 0 0 0 2px var(--c-primary)'
            : 'inset 4px 4px 9px #C8C6C5, inset -4px -4px 9px #FFFFFF',
        }}
      >
        {uploading ? (
          <>
            <Spinner size="lg" />
            <div className="text-center">
              <p className="text-sm font-bold" style={{ color: 'var(--c-text)' }}>
                Extracting skills…
              </p>
              <p className="mt-1 text-xs" style={{ color: 'var(--c-muted)' }}>
                Analysing your resume, please wait
              </p>
            </div>
          </>
        ) : (
          <>
            <div
              className="flex h-16 w-16 items-center justify-center rounded-2xl text-2xl neu-raised"
              style={{ backgroundColor: 'var(--c-surface)' }}
            >
              📄
            </div>
            <div className="text-center">
              <p className="text-sm font-bold" style={{ color: 'var(--c-text)' }}>
                Drop your resume here
              </p>
              <p className="mt-1 text-xs" style={{ color: 'var(--c-muted)' }}>
                or click to browse
              </p>
            </div>
            <p
              className="rounded-full px-3 py-1 text-xs font-bold uppercase tracking-widest neu-raised-sm"
              style={{ color: 'var(--c-muted)', backgroundColor: 'var(--c-surface)' }}
            >
              PDF · DOCX · max 10 MB
            </p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileInput}
          className="hidden"
        />
      </div>
    </div>
  )
}
