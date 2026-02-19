import type { ColumnDef } from "@tanstack/react-table"

import type { PaymentBatchPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { BatchDetailSheet } from "./BatchDetailSheet"

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
}

export const columns: ColumnDef<PaymentBatchPublic>[] = [
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.original.status
      return (
        <Badge variant={status === "confirmed" ? "default" : "secondary"}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </Badge>
      )
    },
  },
  {
    id: "date_range",
    header: "Date Range",
    cell: ({ row }) => (
      <span className="text-sm whitespace-nowrap">
        {formatDate(row.original.date_from)} – {formatDate(row.original.date_to)}
      </span>
    ),
  },
  {
    accessorKey: "total_amount",
    header: "Total Paid",
    cell: ({ row }) => {
      const amount = row.original.total_amount
      return (
        <span className="font-mono text-sm font-medium">
          {amount != null ? `$${amount.toFixed(2)}` : "—"}
        </span>
      )
    },
  },
  {
    accessorKey: "created_at",
    header: "Created",
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground">
        {formatDate(row.original.created_at)}
      </span>
    ),
  },
  {
    accessorKey: "confirmed_at",
    header: "Confirmed",
    cell: ({ row }) => {
      const dt = row.original.confirmed_at
      return (
        <span className="text-sm text-muted-foreground">
          {dt ? formatDate(dt) : "—"}
        </span>
      )
    },
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <BatchDetailSheet batch={row.original} />
      </div>
    ),
  },
]
