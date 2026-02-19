import type { ColumnDef } from "@tanstack/react-table"

import type { WorklogPublic } from "@/client"
import { WorklogEntriesSheet } from "./WorklogEntriesSheet"

export const columns: ColumnDef<WorklogPublic>[] = [
  {
    accessorKey: "title",
    header: "Worklog",
    cell: ({ row }) => (
      <div>
        <p className="font-medium leading-none">{row.original.title}</p>
        {row.original.description && (
          <p className="text-xs text-muted-foreground mt-0.5 max-w-xs truncate">
            {row.original.description}
          </p>
        )}
      </div>
    ),
  },
  {
    accessorKey: "freelancer_name",
    header: "Freelancer",
    cell: ({ row }) => (
      <span className="text-sm">
        {row.original.freelancer_name || "—"}
      </span>
    ),
  },
  {
    accessorKey: "hourly_rate",
    header: "Rate",
    cell: ({ row }) => (
      <span className="font-mono text-sm text-muted-foreground">
        ${row.original.hourly_rate.toFixed(0)}/hr
      </span>
    ),
  },
  {
    accessorKey: "total_hours",
    header: "Hours",
    cell: ({ row }) => (
      <span className="font-mono text-sm">
        {row.original.total_hours.toFixed(2)}h
      </span>
    ),
  },
  {
    accessorKey: "total_earned",
    header: "Earned",
    cell: ({ row }) => (
      <span className="font-mono text-sm font-medium">
        ${row.original.total_earned.toFixed(2)}
      </span>
    ),
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <WorklogEntriesSheet worklog={row.original} />
      </div>
    ),
  },
]
