import type { ColumnDef } from "@tanstack/react-table"

import type { TaskPublic } from "@/client"
import { cn } from "@/lib/utils"
import { TaskActionsMenu } from "./TaskActionsMenu"

export const columns: ColumnDef<TaskPublic>[] = [
  {
    accessorKey: "title",
    header: "Title",
    cell: ({ row }) => (
      <span className="font-medium">{row.original.title}</span>
    ),
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => {
      const description = row.original.description
      return (
        <span
          className={cn(
            "max-w-xs truncate block text-muted-foreground",
            !description && "italic",
          )}
        >
          {description || "No description"}
        </span>
      )
    },
  },
  {
    accessorKey: "created_at",
    header: "Created At",
    cell: ({ row }) => {
      const date = new Date(row.original.created_at)
      return (
        <span className="text-sm text-muted-foreground">
          {date.toLocaleDateString()}
        </span>
      )
    },
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <TaskActionsMenu task={row.original} />
      </div>
    ),
  },
]
