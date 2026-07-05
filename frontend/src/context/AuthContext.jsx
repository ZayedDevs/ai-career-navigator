import { createContext, useContext, useState, useEffect } from 'react'
import api from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('acn_token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    api.get('/api/auth/me')
      .then((res) => setUser(res.data.data.user))
      .catch(() => {
        localStorage.removeItem('acn_token')
        setToken(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const login = async (email, password) => {
    const res = await api.post('/api/auth/login', { email, password })
    const { token: t, user: u } = res.data.data
    localStorage.setItem('acn_token', t)
    setToken(t)
    setUser(u)
    return u
  }

  const register = async (email, password, name) => {
    const res = await api.post('/api/auth/register', { email, password, name })
    const { token: t, user: u } = res.data.data
    localStorage.setItem('acn_token', t)
    setToken(t)
    setUser(u)
    return u
  }

  const logout = () => {
    localStorage.removeItem('acn_token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
