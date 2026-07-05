import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    setLoading(true)
    try {
      await register(form.email, form.password, form.name)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.message || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-[70vh] items-center justify-center py-8">
      <div
        className="w-full max-w-md rounded-3xl p-10 neu-raised-lg"
        style={{ backgroundColor: 'var(--c-surface)' }}
      >
        <p
          className="mb-1 text-xs font-bold uppercase tracking-widest"
          style={{ color: 'var(--c-muted)' }}
        >
          Get started free
        </p>
        <h1 className="mb-8 text-2xl font-bold" style={{ color: 'var(--c-text)' }}>
          Create account
        </h1>

        {error && (
          <div
            className="mb-6 rounded-xl px-4 py-3 text-xs font-bold uppercase tracking-wide neu-pressed-sm"
            style={{ color: 'var(--c-danger)', backgroundColor: 'var(--c-surface)' }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <Input
            label="Full name"
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            autoComplete="name"
            placeholder="Jane Smith"
          />
          <Input
            label="Email"
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            required
            autoComplete="email"
            placeholder="you@example.com"
          />
          <Input
            label="Password"
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
            required
            autoComplete="new-password"
            placeholder="Min 6 characters"
          />
          <Button type="submit" loading={loading} className="mt-2 w-full py-3">
            Create account →
          </Button>
        </form>

        <p className="mt-6 text-center text-xs" style={{ color: 'var(--c-muted)' }}>
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-bold transition-colors"
            style={{ color: 'var(--c-primary)' }}
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
