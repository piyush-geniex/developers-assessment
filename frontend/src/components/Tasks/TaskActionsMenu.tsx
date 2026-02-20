import { EllipsisVertical, Eye } from "lucide-react"
import { useState } from "react"

import type { TaskItem } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useTaskExpansion } from "./TaskExpansionContext"
import AddWorkLog from "./AddWorkLog"
import DeleteTask from "./DeleteTask"
import EditTask from "./EditTask"

interface TaskActionsMenuProps {
  task: TaskItem
}

export const TaskActionsMenu = ({ task }: TaskActionsMenuProps) => {
  const [open, setOpen] = useState(false)
  const { expandedRows, onToggleRow } = useTaskExpansion()

  return (
    <div className="flex flex-col gap-2">
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon">
            <EllipsisVertical />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onClick={() => {
              onToggleRow(task.id)
              setOpen(false)
            }}
          >
            <Eye className="mr-2 h-4 w-4" />
            {expandedRows.has(task.id) ? "Hide" : "View"} Work Logs
          </DropdownMenuItem>
          <AddWorkLog
            taskId={task.id}
            onSuccess={() => setOpen(false)}
          />
          <EditTask task={task} onSuccess={() => setOpen(false)} />
          <DeleteTask taskId={task.id} onSuccess={() => setOpen(false)} />
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
