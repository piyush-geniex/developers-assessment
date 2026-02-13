import type { ColumnDef } from "@tanstack/react-table"

import type { WorklogSummary } from "@/client"

export const columns: ColumnDef<WorklogSummary>[] = [
  {
    accessorKey: "task_title",
    header: "Task",
    cell: ({ row }) => (
      <div className="flex flex-col">
        <span className="font-medium">{row.original.task_title}</span>
        <span className="text-xs text-muted-foreground font-mono">
          {row.original.task_id.slice(0, 8)}...
        </span>
      </div>
    ),
  },
  {
    accessorKey: "freelancer_name",
    header: "Freelancer",
    cell: ({ row }) => (
      <div className="flex flex-col">
        <span className="font-medium">{row.original.freelancer_name}</span>
        <span className="text-xs text-muted-foreground font-mono">
          {row.original.freelancer_id.slice(0, 8)}...
        </span>
      </div>
    ),
  },
  {
    accessorKey: "entry_count",
    header: "Entries",
    cell: ({ row }) => (
      <span className="tabular-nums">{row.original.entry_count}</span>
    ),
  },
  {
    accessorKey: "total_hours",
    header: "Total Hours",
    cell: ({ row }) => (
      <span className="tabular-nums font-medium">{row.original.total_hours.toFixed(2)}h</span>
    ),
  },
  {
    accessorKey: "total_amount",
    header: "Amount",
    cell: ({ row }) => {
      const amount = row.original.total_amount
      return (
        <span className="tabular-nums font-medium">
          {amount > 0
            ? `$${amount.toFixed(2)}`
            : <span className="text-muted-foreground">—</span>
          }
        </span>
      )
    },
  },
]
