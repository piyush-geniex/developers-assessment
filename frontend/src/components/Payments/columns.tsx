import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { PaymentBatchPublic } from "@/client"
import { Trash2 } from "lucide-react"

interface ColumnsOptions {
  onDelete: (batch: PaymentBatchPublic) => void
  onView: (batch: PaymentBatchPublic) => void
}

export function getColumns({ onDelete, onView }: ColumnsOptions): ColumnDef<PaymentBatchPublic>[] {
  return [
    {
      accessorKey: "date_from",
      header: "Date Range",
      cell: ({ row }) => (
        <span className="tabular-nums text-sm">
          {row.original.date_from} — {row.original.date_to}
        </span>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => (
        <Badge variant={row.original.status === "CONFIRMED" ? "default" : "secondary"}>
          {row.original.status === "CONFIRMED" ? "Confirmed" : "Draft"}
        </Badge>
      ),
    },
    {
      accessorKey: "total_amount",
      header: "Total Amount",
      cell: ({ row }) => (
        <span className="tabular-nums font-medium">
          {row.original.total_amount > 0
            ? `$${row.original.total_amount.toFixed(2)}`
            : <span className="text-muted-foreground">—</span>
          }
        </span>
      ),
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground tabular-nums">
          {new Date(row.original.created_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      id: "actions",
      header: "Actions",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => onView(row.original)}>
            View
          </Button>
          {row.original.status !== "CONFIRMED" && (
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
              onClick={() => onDelete(row.original)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      ),
    },
  ]
}
