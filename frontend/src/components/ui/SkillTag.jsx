export default function SkillTag({ skill, removable = false, onRemove, className = '', style: styleProp = {} }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wide neu-raised-sm ${className}`}
      style={{
        backgroundColor: 'var(--c-surface)',
        color: 'var(--c-primary)',
        ...styleProp,
      }}
    >
      {skill}
      {removable && (
        <button
          onClick={() => onRemove?.(skill)}
          className="ml-1 flex h-3.5 w-3.5 items-center justify-center rounded-full text-xs transition-all"
          style={{ color: 'var(--c-muted)' }}
          onMouseEnter={(e) => (e.target.style.color = 'var(--c-danger)')}
          onMouseLeave={(e) => (e.target.style.color = 'var(--c-muted)')}
          aria-label={`Remove ${skill}`}
        >
          ×
        </button>
      )}
    </span>
  )
}
