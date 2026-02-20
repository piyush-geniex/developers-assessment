import { createContext, useContext } from "react"

interface TaskSelectionContextType {
  selectedTasks: Record<string, boolean>
  toggleTask: (taskId: string, value?: boolean) => void
  selectedWorklogs: Record<string, boolean>
  toggleWorklog: (worklogId: string, value?: boolean) => void
  selectAllMode: boolean
  setSelectAllMode: (value: boolean) => void
}

export const TaskSelectionContext = createContext<TaskSelectionContextType | null>(null)

export const useTaskSelection = () => {
  const ctx = useContext(TaskSelectionContext)
  if (!ctx) {
    throw new Error("useTaskSelection must be used within TaskSelectionProvider")
  }
  return ctx
}
