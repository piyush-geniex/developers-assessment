import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import {
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  FileText,
  Search,
} from "lucide-react"
import { Suspense } from "react"

import { PaymentsService } from "@/client/worklogService"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

export const Route = (createFileRoute as any)("/_layout/payment-history")({
  component: PaymentHistory,
  head: () => ({
    meta: [
      {
        title: "Payment History - Dashboard",
      },
    ],
  }),
})

// Format helpers
function formatCurrency(amount: string | number) {
  const num = typeof amount === "string" ? Number.parseFloat(amount) : amount
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num)
}

function formatDateTime(dateString: string) {
  return new Date(dateString).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

// Status badge
function StatusBadge({ status }: { status: string }) {
  const variants: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    completed: { label: "Completed", variant: "default" },
    processing: { label: "Processing", variant: "secondary" },
    failed: { label: "Failed", variant: "destructive" },
    draft: { label: "Draft", variant: "outline" },
  }

  const config = variants[status] || { label: status, variant: "outline" as const }

  return (
    <Badge variant={config.variant} className="gap-1">
      {status === "completed" && <CheckCircle2 className="h-3 w-3" />}
      {config.label}
    </Badge>
  )
}

// Stats Card
function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="rounded-lg bg-primary/10 p-2">
          <Icon className="h-4 w-4 text-primary" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  )
}

// Loading skeleton
function HistorySkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-24" />
        ))}
      </div>
      <Skeleton className="h-12 w-full" />
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    </div>
  )
}

function HistoryContent() {
  const { data: batches, isLoading } = useQuery({
    queryKey: ["payment", "batches"],
    queryFn: () => PaymentsService.getPaymentBatches({ limit: 100 }),
  })

  if (isLoading) {
    return <HistorySkeleton />
  }

  const totalPaid = batches?.data.reduce(
    (sum, b) => sum + Number.parseFloat(b.total_amount),
    0
  ) || 0

  const totalWorklogs = batches?.data.reduce(
    (sum, b) => sum + (b.worklog_count || 0),
    0
  ) || 0

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatsCard
          title="Total Batches"
          value={batches?.count || 0}
          subtitle="Payment batches processed"
          icon={FileText}
        />
        <StatsCard
          title="WorkLogs Paid"
          value={totalWorklogs}
          subtitle="Across all batches"
          icon={Calendar}
        />
        <StatsCard
          title="Total Paid"
          value={formatCurrency(totalPaid)}
          subtitle="All time"
          icon={DollarSign}
        />
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Batch ID</TableHead>
                <TableHead>Processed At</TableHead>
                <TableHead className="text-center">WorkLogs</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-center">Status</TableHead>
                <TableHead>Notes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!batches?.data.length ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-32 text-center">
                    <div className="flex flex-col items-center justify-center text-muted-foreground">
                      <Search className="h-8 w-8 mb-2" />
                      <p>No payment batches found</p>
                      <p className="text-sm">
                        Process your first payment to see history here
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                batches.data.map((batch) => (
                  <TableRow key={batch.id}>
                    <TableCell>
                      <span className="font-mono text-xs text-muted-foreground">
                        {batch.id.slice(0, 8)}...
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        {formatDateTime(batch.processed_at)}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="inline-flex items-center justify-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                        {batch.worklog_count || 0}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-semibold">
                        {formatCurrency(batch.total_amount)}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <StatusBadge status={batch.status} />
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground truncate max-w-[200px] block">
                        {batch.notes || "-"}
                      </span>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}

function PaymentHistory() {
  const navigate = useNavigate()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate({ to: "/worklogs" } as any)}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Payment History</h1>
          <p className="text-muted-foreground">
            View all processed payment batches
          </p>
        </div>
      </div>

      <Suspense fallback={<HistorySkeleton />}>
        <HistoryContent />
      </Suspense>
    </div>
  )
}
