export default function Card({ children, className = '' }) {
  return (
    <div
      className={`rounded-2xl p-6 neu-raised ${className}`}
      style={{ backgroundColor: 'var(--c-surface)' }}
    >
      {children}
    </div>
  )
}
