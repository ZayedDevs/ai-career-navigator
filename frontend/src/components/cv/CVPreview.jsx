const DOC_FONT = "'Georgia', 'Times New Roman', serif"

function SectionHeader({ children }) {
  return (
    <h2
      style={{
        fontSize: '12px',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        borderBottom: '1.5px solid #1a1a1a',
        paddingBottom: '2px',
        marginBottom: '8px',
      }}
    >
      {children}
    </h2>
  )
}

function GridList({ items }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        columnGap: '12px',
        rowGap: '4px',
        fontSize: '11px',
      }}
    >
      {items.map((item, i) => (
        <div key={i}>{item}</div>
      ))}
    </div>
  )
}

function EntryRow({ left, right }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', fontSize: '11.5px' }}>
      <span style={{ fontWeight: 700 }}>{left}</span>
      {right && <span style={{ fontWeight: 700, whiteSpace: 'nowrap' }}>{right}</span>}
    </div>
  )
}

function Bullets({ items }) {
  if (!items?.length) return null
  return (
    <ul style={{ margin: '4px 0 0', padding: 0, listStyle: 'none', fontSize: '11px' }}>
      {items.map((b, i) => (
        <li key={i} style={{ marginBottom: '1px' }}>• {b}</li>
      ))}
    </ul>
  )
}

export default function CVPreview({ profile }) {
  if (!profile) return null

  const { personal = {}, summary, skills = [], expertise = [], education = [],
    experience = [], projects = [], certifications = [] } = profile

  const contactParts = [personal.email, personal.phone, personal.github, personal.linkedin].filter(Boolean)

  return (
    <div
      id="cv-preview-content"
      style={{
        width: '210mm',
        minHeight: '297mm',
        padding: '18mm 16mm',
        backgroundColor: '#ffffff',
        color: '#1a1a1a',
        fontFamily: DOC_FONT,
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
    >
      {personal.name && (
        <div style={{ textAlign: 'center' }}>
          <h1 style={{ fontSize: '24px', fontWeight: 700, textTransform: 'uppercase', margin: 0 }}>
            {personal.name}
          </h1>
          {personal.title && (
            <p
              style={{
                fontSize: '12px',
                fontWeight: 600,
                letterSpacing: '2px',
                textTransform: 'uppercase',
                margin: '4px 0 0',
              }}
            >
              {personal.title}
            </p>
          )}
        </div>
      )}

      {contactParts.length > 0 && (
        <div
          style={{
            borderTop: '1.5px solid #1a1a1a',
            borderBottom: '1.5px solid #1a1a1a',
            padding: '6px 0',
            textAlign: 'center',
            fontSize: '10.5px',
          }}
        >
          {contactParts.join('  |  ')}
        </div>
      )}

      {summary && (
        <p style={{ textAlign: 'justify', fontSize: '11.5px', lineHeight: 1.5, margin: 0 }}>
          {summary}
        </p>
      )}

      {expertise.length > 0 && (
        <section>
          <SectionHeader>Area of Expertise</SectionHeader>
          <GridList items={expertise} />
        </section>
      )}

      {experience.length > 0 && (
        <section>
          <SectionHeader>Experience</SectionHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {experience.map((exp, i) => (
              <div key={i}>
                <EntryRow left={exp.title} right={exp.period} />
                {exp.company && (
                  <p style={{ fontSize: '11px', fontStyle: 'italic', margin: '1px 0 0' }}>{exp.company}</p>
                )}
                <Bullets items={exp.bullets} />
              </div>
            ))}
          </div>
        </section>
      )}

      {projects.length > 0 && (
        <section>
          <SectionHeader>Projects Experience</SectionHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {projects.map((p, i) => (
              <div key={i}>
                <EntryRow left={p.name} right={p.period} />
                {p.role && (
                  <p style={{ fontSize: '11px', fontStyle: 'italic', margin: '1px 0 0' }}>{p.role}</p>
                )}
                <Bullets items={p.bullets} />
              </div>
            ))}
          </div>
        </section>
      )}

      {education.length > 0 && (
        <section>
          <SectionHeader>Education</SectionHeader>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {education.map((edu, i) => (
              <div key={i}>
                <EntryRow left={edu.institution} right={edu.period} />
                {edu.degree && (
                  <p style={{ fontSize: '11px', margin: '1px 0 0' }}>{edu.degree}</p>
                )}
                {edu.cgpa !== '' && edu.cgpa != null && (
                  <p style={{ fontSize: '11px', margin: '2px 0 0' }}>• CGPA {edu.cgpa} / 4.00</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {skills.length > 0 && (
        <section>
          <SectionHeader>Skills</SectionHeader>
          <p style={{ fontSize: '11px', margin: 0, lineHeight: 1.6 }}>{skills.join(' · ')}</p>
        </section>
      )}

      {certifications.length > 0 && (
        <section>
          <SectionHeader>Certificates</SectionHeader>
          <GridList items={certifications} />
        </section>
      )}
    </div>
  )
}
