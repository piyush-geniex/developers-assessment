import type { ColumnDef } from "@tanstack/react-table"

import type { TimeEntryPublic } from "@/client"
import { TimeEntryActionsMenu } from "./TimeEntryActionsMenu"

export function getColumns(isSuperuser: boolean): ColumnDef<TimeEntryPublic>[] {
  return [
  {
    accessorKey: "task_title",
    header: "Task",
    cell: ({ row }) => {
      const taskTitle = row.original.task_title
      const taskId = row.original.task_id
      return (
        <div className="flex flex-col">
          <span className="font-medium">{taskTitle}</span>
          <span className="text-xs text-muted-foreground font-mono">
            {taskId.slice(0, 8)}...
          </span>
        </div>
      )
    },
  },
  {
    accessorKey: "start_time",
    header: "Start Time",
    cell: ({ row }) => {
      const date = new Date(row.original.start_time)
      return (
        <span className="text-sm">
          {date.toLocaleString()}
        </span>
      )
    },
  },
  {
    accessorKey: "end_time",
    header: "End Time",
    cell: ({ row }) => {
      const date = new Date(row.original.end_time)
      return (
        <span className="text-sm">
          {date.toLocaleString()}
        </span>
      )
    },
  },
  {
    accessorKey: "duration",
    header: "Duration",
    cell: ({ row }) => {
      const start = new Date(row.original.start_time)
      const end = new Date(row.original.end_time)
      const hours = ((end.getTime() - start.getTime()) / (1000 * 60 * 60)).toFixed(2)
      return (
        <span className="font-medium">{hours}h</span>
      )
    },
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => {
      const description = row.original.description
      return (
        <span className="text-muted-foreground max-w-xs truncate block">
          {description || "No description"}
        </span>
      )
    },
  },
    ...(isSuperuser
      ? [{
          accessorKey: "freelancer_name" as const,
          header: "Freelancer",
          cell: ({ row }: { row: { original: TimeEntryPublic } }) => (
            <span className="text-sm">{row.original.freelancer_name}</span>
          ),
        }]
      : []),
    {
      id: "actions",
      header: () => <span className="sr-only">Actions</span>,
      cell: ({ row }) => (
        <div className="flex justify-end">
          <TimeEntryActionsMenu timeEntry={row.original} />
        </div>
      ),
    },
  ]
}
