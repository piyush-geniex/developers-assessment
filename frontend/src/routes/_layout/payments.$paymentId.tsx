import { createFileRoute, Link } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import axios from "axios"

import { Button } from "@/components/ui/button"
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
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export const Route = createFileRoute("/_layout/payments/$paymentId")({
  component: PaymentDetailPage,
  head: () => ({
    meta: [{ title: "Payment Detail - WorkLog Dashboard" }],
  }),
})

function timeAgo(dateStr: string): string {
  const secs = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (secs < 60) return "just now"
  const mins = Math.floor(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days === 1) return "yesterday"
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  if (days < 365) return `${Math.floor(days / 30)}mo ago`
  return `${Math.floor(days / 365)}y ago`
}

function fmtDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "numeric", minute: "2-digit",
  })
}

function fmtShortDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  })
}

function PaymentDetailPage() {
  const { paymentId } = Route.useParams()
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConfirming, setIsConfirming] = useState(false)

  const fetchPayment = () => {
    setIsLoading(true)
    setError(null)

    const ax = axios.create()
    ax.defaults.baseURL = "http://localhost:8000"

    ax.get(`/api/v1/payments/${paymentId}`)
      .then((res: any) => {
        setData(res.data)
        setIsLoading(false)
      })
      .catch((err: any) => {
        setError("Failed to load payment details. Please try again.")
        console.error(err)
        setIsLoading(false)
      })
  }

  useEffect(() => {
    fetchPayment()
  }, [paymentId])

  const handleConfirm = () => {
    setIsConfirming(true)

    const ax = axios.create()
    ax.defaults.baseURL = "http://localhost:8000"

    ax.post(`/api/v1/payments/${paymentId}/confirm`)
      .then((res: any) => {
        setData(res.data)
        setIsConfirming(false)
      })
      .catch((err: any) => {
        setError("Failed to confirm payment. Please try again.")
        console.error(err)
        setIsConfirming(false)
      })
  }

  const handleExcludeWorklog = (wlId: number) => {
    const ax = axios.create()
    ax.defaults.baseURL = "http://localhost:8000"

    ax.delete(`/api/v1/payments/${paymentId}/worklogs/${wlId}`)
      .then(() => {
        fetchPayment()
      })
      .catch((err: any) => {
        setError("Failed to exclude worklog. Please try again.")
        console.error(err)
      })
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="text-destructive text-center py-8">{error}</div>
    )
  }

  if (!data) return null

  const totalHours = data.worklogs.reduce(
    (sum: number, wl: any) => sum + wl.total_hours,
    0,
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <Link to="/payments">
          <Button variant="outline" size="sm" aria-label="Back to payments">
            Back
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold tracking-tight">
            Payment #{data.id}
          </h1>
          <p className="text-muted-foreground">
            {fmtShortDate(data.date_range_start)} – {fmtShortDate(data.date_range_end)}
          </p>
        </div>
        <Badge
          variant={data.status === "confirmed" ? "default" : "secondary"}
          className="text-sm"
        >
          {data.status}
        </Badge>
      </div>

      {error && (
        <div className="text-destructive text-sm">{error}</div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Amount</CardDescription>
            <CardTitle className="text-2xl">
              ${data.total_amount.toFixed(2)}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Worklogs</CardDescription>
            <CardTitle className="text-2xl">
              {data.worklogs.length}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Hours</CardDescription>
            <CardTitle className="text-2xl">
              {totalHours.toFixed(1)}h
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-4">Included Worklogs</h2>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Task</TableHead>
                <TableHead>Freelancer</TableHead>
                <TableHead className="text-right">Hours</TableHead>
                <TableHead className="text-right">Amount ($)</TableHead>
                {data.status === "draft" && <TableHead></TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.worklogs.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={data.status === "draft" ? 5 : 4}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No worklogs in this payment
                  </TableCell>
                </TableRow>
              ) : (
                data.worklogs.map((wl: any) => (
                  <TableRow key={wl.id}>
                    <TableCell className="font-medium">
                      {wl.task_name}
                    </TableCell>
                    <TableCell>{wl.freelancer_name || "Unknown"}</TableCell>
                    <TableCell className="text-right">
                      {wl.total_hours.toFixed(1)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      ${wl.earned_amount.toFixed(2)}
                    </TableCell>
                    {data.status === "draft" && (
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleExcludeWorklog(wl.id)}
                          aria-label={`Remove worklog ${wl.task_name} from payment`}
                        >
                          Remove
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {data.status === "draft" && (
        <div className="flex gap-2">
          <Button
            onClick={handleConfirm}
            disabled={isConfirming || data.worklogs.length === 0}
            aria-label="Confirm payment"
          >
            {isConfirming ? "Confirming..." : "Confirm Payment"}
          </Button>
        </div>
      )}

      <p className="text-sm text-muted-foreground">
        Created: <span title={fmtDate(data.created_at)} className="cursor-default">{timeAgo(data.created_at)}</span>
      </p>
    </div>
  )
}
