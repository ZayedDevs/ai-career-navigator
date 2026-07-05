import { createContext, useContext, useState } from 'react'

const FlowContext = createContext(null)

export function FlowProvider({ children }) {
  const [skills, setSkills] = useState([])
  const [targetRole, setTargetRole] = useState(null)
  const [missingSkills, setMissingSkills] = useState([])

  return (
    <FlowContext.Provider value={{ skills, setSkills, targetRole, setTargetRole, missingSkills, setMissingSkills }}>
      {children}
    </FlowContext.Provider>
  )
}

export function useFlow() {
  return useContext(FlowContext)
}
