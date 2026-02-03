import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import {
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  FileText,
  Search,
} from "lucide-react"
import { Suspense, useMemo } from "react"

import { FreelancerPortalService, type FreelancerPaymentInfo } from "@/client/freelancerPortalService"
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

export const Route = (createFileRoute as any)("/_freelancer-layout/payments")({
  component: FreelancerPayments,
  head: () => ({
    meta: [{ title: "Payment History - Freelancer Portal" }],
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
  const variants: Record<
    string,
    { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
  > = {
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

function PaymentsSkeleton() {
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

function PaymentsContent() {
  const { data: payments, isLoading } = useQuery({
    queryKey: ["freelancer", "payments"],
    queryFn: () => FreelancerPortalService.getMyPayments(),
  })

  // Calculate stats
  const stats = useMemo(() => {
    if (!payments?.length) {
      return { totalPaid: 0, totalPayments: 0, totalWorklogs: 0 }
    }

    return {
      totalPaid: payments.reduce(
        (sum: number, p: FreelancerPaymentInfo) => sum + Number.parseFloat(p.total_amount),
        0
      ),
      totalPayments: payments.length,
      totalWorklogs: payments.reduce((sum: number, p: FreelancerPaymentInfo) => sum + p.worklog_count, 0),
    }
  }, [payments])

  if (isLoading) {
    return <PaymentsSkeleton />
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatsCard
          title="Total Received"
          value={formatCurrency(stats.totalPaid)}
          subtitle="All time earnings"
          icon={DollarSign}
        />
        <StatsCard
          title="Payment Batches"
          value={stats.totalPayments}
          subtitle="Total payments received"
          icon={FileText}
        />
        <StatsCard
          title="WorkLogs Paid"
          value={stats.totalWorklogs}
          subtitle="Across all payments"
          icon={Calendar}
        />
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Payment Date</TableHead>
                <TableHead className="text-center">WorkLogs</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-center">Status</TableHead>
                <TableHead>Notes</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!payments?.length ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-32 text-center">
                    <div className="flex flex-col items-center justify-center text-muted-foreground">
                      <Search className="h-8 w-8 mb-2" />
                      <p>No payments yet</p>
                      <p className="text-sm">
                        Your payment history will appear here
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                payments.map((payment: FreelancerPaymentInfo) => (
                  <TableRow key={payment.batch_id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        {formatDateTime(payment.processed_at)}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="inline-flex items-center justify-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                        {payment.worklog_count}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-semibold text-green-600 dark:text-green-400">
                        {formatCurrency(payment.total_amount)}
                      </span>
                    </TableCell>
                    <TableCell className="text-center">
                      <StatusBadge status={payment.status} />
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground truncate max-w-[200px] block">
                        {payment.notes || "-"}
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

function FreelancerPayments() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Payment History</h1>
        <p className="text-muted-foreground">
          View your received payments and earnings
        </p>
      </div>
      <Suspense fallback={<PaymentsSkeleton />}>
        <PaymentsContent />
      </Suspense>
    </div>
  )
}
