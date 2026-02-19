import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { CreditCard } from "lucide-react"
import { Suspense } from "react"

import { PaymentsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { CreateBatchDialog } from "@/components/Payments/CreateBatchDialog"
import { columns } from "@/components/Payments/columns"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

function getBatchesQueryOptions() {
  return {
    queryKey: ["payment-batches"],
    queryFn: () => PaymentsService.readBatches({ limit: 100 }),
  }
}

export const Route = createFileRoute("/_layout/payments")({
  component: Payments,
  head: () => ({
    meta: [{ title: "Payments - WorkLog Dashboard" }],
  }),
})

function BatchesTableSkeleton() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Status</TableHead>
          <TableHead>Date Range</TableHead>
          <TableHead>Total Paid</TableHead>
          <TableHead>Created</TableHead>
          <TableHead>Confirmed</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {Array.from({ length: 4 }).map((_, i) => (
          <TableRow key={i}>
            <TableCell><Skeleton className="h-5 w-20 rounded-full" /></TableCell>
            <TableCell><Skeleton className="h-4 w-44" /></TableCell>
            <TableCell><Skeleton className="h-4 w-24" /></TableCell>
            <TableCell><Skeleton className="h-4 w-28" /></TableCell>
            <TableCell><Skeleton className="h-4 w-28" /></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

function BatchesTableContent() {
  const { data } = useSuspenseQuery(getBatchesQueryOptions())

  if (data.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-16">
        <div className="rounded-full bg-muted p-4 mb-4">
          <CreditCard className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No payment batches yet</h3>
        <p className="text-muted-foreground text-sm mt-1">
          Create a new batch to start processing freelancer payments.
        </p>
      </div>
    )
  }

  return <DataTable columns={columns} data={data.data} />
}

function BatchesTable() {
  return (
    <Suspense fallback={<BatchesTableSkeleton />}>
      <BatchesTableContent />
    </Suspense>
  )
}

function Payments() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Payments</h1>
          <p className="text-muted-foreground text-sm mt-0.5">
            Manage payment batches for freelancer compensation.
          </p>
        </div>
        <CreateBatchDialog />
      </div>
      <BatchesTable />
    </div>
  )
}
