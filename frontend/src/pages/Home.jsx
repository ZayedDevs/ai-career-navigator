import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../lib/api'
import Button from '../components/ui/Button'

const steps = [
  { num: '01', title: 'Upload Resume', desc: 'Extract your skills automatically from PDF or DOCX.' },
  { num: '02', title: 'Analyse Gap', desc: 'See how you match 11 tech roles and spot missing skills.' },
  { num: '03', title: 'Predict Career', desc: 'AI predicts your best-fit role from your current skill set.' },
  { num: '04', title: 'Get a Roadmap', desc: 'Phase-by-phase learning plan with curated resources.' },
]


export default function Home() {
  const { user } = useAuth()
  const [apiOk, setApiOk] = useState(null)

  useEffect(() => {
    api.get('/api/health')
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false))
  }, [])

  return (
    <div className="flex flex-col items-center gap-20 py-10">

      {/* Hero */}
      <section className="w-full text-center">
        <div className="mb-6 flex items-center justify-center gap-2">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{
              backgroundColor:
                apiOk === true ? 'var(--c-success)'
                : apiOk === false ? 'var(--c-danger)'
                : '#aaa',
              boxShadow: apiOk === true ? '0 0 6px var(--c-success)' : 'none',
            }}
          />
          <span className="text-xs uppercase tracking-widest" style={{ color: 'var(--c-muted)' }}>
            {apiOk === true ? 'System online' : apiOk === false ? 'API offline' : 'Checking…'}
          </span>
        </div>

        <h1
          className="mb-5 text-4xl font-bold leading-tight sm:text-5xl"
          style={{ color: 'var(--c-text)' }}
        >
          Navigate your{' '}
          <span style={{ color: 'var(--c-primary)' }}>tech career</span>
          <br />
          with AI-powered insights
        </h1>

        <p
          className="mx-auto mb-10 max-w-lg text-sm leading-relaxed"
          style={{ color: 'var(--c-muted)' }}
        >
          Upload your resume, discover skill gaps, predict your best-fit role,
          and get a personalised learning roadmap — all in one place.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          {user ? (
            <Link to="/upload">
              <Button className="px-8 py-3 text-xs">Upload Resume →</Button>
            </Link>
          ) : (
            <>
              <Link to="/register">
                <Button className="px-8 py-3 text-xs">Get started free</Button>
              </Link>
              <Link to="/login">
                <Button variant="outline" className="px-8 py-3 text-xs">Sign in</Button>
              </Link>
            </>
          )}
        </div>
      </section>

      {/* How it works */}
      <section className="w-full">
        <p
          className="mb-8 text-center text-xs font-bold uppercase tracking-widest"
          style={{ color: 'var(--c-muted)' }}
        >
          How it works
        </p>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step) => (
            <div
              key={step.num}
              className="rounded-2xl p-6 transition-all hover:-translate-y-0.5 neu-raised"
              style={{ backgroundColor: 'var(--c-surface)' }}
            >
              <p
                className="mb-3 text-2xl font-bold"
                style={{ color: 'var(--c-primary)', opacity: 0.4 }}
              >
                {step.num}
              </p>
              <h3
                className="mb-2 text-sm font-bold"
                style={{ color: 'var(--c-text)' }}
              >
                {step.title}
              </h3>
              <p className="text-xs leading-relaxed" style={{ color: 'var(--c-muted)' }}>
                {step.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

    </div>
  )
}
