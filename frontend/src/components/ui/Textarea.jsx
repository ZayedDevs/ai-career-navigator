export default function Textarea({ label, error, className = '', onBlur, ...props }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          className="text-xs font-bold uppercase tracking-widest"
          style={{ color: 'var(--c-muted)' }}
        >
          {label}
        </label>
      )}
      <textarea
        className={`rounded-xl border-0 px-4 py-3 text-sm outline-none transition-all neu-pressed ${className}`}
        style={{
          backgroundColor: 'var(--c-surface)',
          color: 'var(--c-text)',
          resize: 'vertical',
          ...(error
            ? { boxShadow: 'inset 4px 4px 9px #C8C6C5, inset -4px -4px 9px #FFFFFF, 0 0 0 2px var(--c-danger)' }
            : {}),
        }}
        onFocus={(e) => {
          e.target.style.boxShadow = 'inset 4px 4px 9px #C8C6C5, inset -4px -4px 9px #FFFFFF, 0 0 0 2px var(--c-primary)'
        }}
        onBlur={(e) => {
          e.target.style.boxShadow = error
            ? 'inset 4px 4px 9px #C8C6C5, inset -4px -4px 9px #FFFFFF, 0 0 0 2px var(--c-danger)'
            : 'inset 4px 4px 9px #C8C6C5, inset -4px -4px 9px #FFFFFF'
          onBlur?.(e)
        }}
        {...props}
      />
      {error && (
        <p className="text-xs font-bold" style={{ color: 'var(--c-danger)' }}>
          {error}
        </p>
      )}
    </div>
  )
}
