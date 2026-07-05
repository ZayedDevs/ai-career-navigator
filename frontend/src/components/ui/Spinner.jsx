export default function Spinner({ size = 'md' }) {
  const sizes = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-10 w-10' }
  return (
    <div
      className={`${sizes[size]} animate-spin rounded-full border-2`}
      style={{
        borderColor: 'var(--c-primary-light)',
        borderTopColor: 'var(--c-primary)',
      }}
      role="status"
      aria-label="Loading"
    />
  )
}
