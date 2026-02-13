import { EllipsisVertical } from "lucide-react"
import { useState } from "react"

import type { TimeEntryPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DeleteTimeEntry from "./DeleteTimeEntry"
import EditTimeEntry from "./EditTimeEntry"

interface TimeEntryActionsMenuProps {
  timeEntry: TimeEntryPublic
}

export const TimeEntryActionsMenu = ({ timeEntry }: TimeEntryActionsMenuProps) => {
  const [open, setOpen] = useState(false)

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <EditTimeEntry timeEntry={timeEntry} onSuccess={() => setOpen(false)} />
        <DeleteTimeEntry id={timeEntry.id} onSuccess={() => setOpen(false)} />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
