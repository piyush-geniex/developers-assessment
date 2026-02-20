import { createContext, useContext } from "react"

interface TaskExpansionContextType {
  expandedRows: Set<string>
  onToggleRow: (rowId: string) => void
}

export const TaskExpansionContext = createContext<TaskExpansionContextType | undefined>(undefined)

export function useTaskExpansion() {
  const context = useContext(TaskExpansionContext)
  if (!context) {
    throw new Error("useTaskExpansion must be used within TaskExpansionProvider")
  }
  return context
}
