import Spinner from './Spinner'

const variants = {
  primary: {
    className: 'text-white font-bold uppercase tracking-widest',
    style: {
      backgroundColor: 'var(--c-primary)',
      boxShadow: '3px 3px 7px #004747, -3px -3px 7px #339999',
    },
    hoverStyle: { backgroundColor: 'var(--c-primary-dark)' },
  },
  secondary: {
    className: 'font-bold uppercase tracking-widest neu-raised-sm',
    style: {
      backgroundColor: 'var(--c-surface)',
      color: 'var(--c-text)',
    },
  },
  danger: {
    className: 'text-white font-bold uppercase tracking-widest',
    style: {
      backgroundColor: 'var(--c-danger)',
      boxShadow: '3px 3px 7px #b30039, -3px -3px 7px #ff5c88',
    },
  },
  outline: {
    className: 'font-bold uppercase tracking-widest',
    style: {
      backgroundColor: 'var(--c-surface)',
      color: 'var(--c-primary)',
      border: '1.5px solid var(--c-primary)',
      boxShadow: '3px 3px 7px #C8C6C5, -3px -3px 7px #FFFFFF',
    },
  },
}

export default function Button({ children, variant = 'primary', loading = false, className = '', style: styleProp = {}, ...props }) {
  const v = variants[variant]

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-xs transition-all disabled:cursor-not-allowed disabled:opacity-50 ${v.className} ${className}`}
      style={{ ...v.style, ...styleProp }}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  )
}
