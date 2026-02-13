import { EllipsisVertical } from "lucide-react"
import { useState } from "react"

import type { TaskPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DeleteTask from "./DeleteTask"
import EditTask from "./EditTask"

interface TaskActionsMenuProps {
  task: TaskPublic
}

export const TaskActionsMenu = ({ task }: TaskActionsMenuProps) => {
  const [open, setOpen] = useState(false)

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <EditTask task={task} onSuccess={() => setOpen(false)} />
        <DeleteTask id={task.id} onSuccess={() => setOpen(false)} />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
