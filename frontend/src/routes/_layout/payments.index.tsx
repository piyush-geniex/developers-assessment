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

export const Route = createFileRoute("/_layout/payments/")({
  component: PaymentsPage,
  head: () => ({
    meta: [{ title: "Payments - WorkLog Dashboard" }],
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

function PaymentsPage() {
  const [allData, setAllData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const pageSize = 10

  useEffect(() => {
    setIsLoading(true)
    setError(null)

    const ax = axios.create()
    ax.defaults.baseURL = "http://localhost:8000"

    ax.get("/api/v1/payments/")
      .then((res: any) => {
        setAllData(res.data.data || [])
        setIsLoading(false)
      })
      .catch((err: any) => {
        setError("Failed to load payments. Please try again.")
        console.error(err)
        setIsLoading(false)
      })
  }, [])

  const displayed = allData.slice((page - 1) * pageSize, page * pageSize)
  const totalPages = Math.ceil(allData.length / pageSize)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Payments</h1>
          <p className="text-muted-foreground">
            View and manage payment batches
          </p>
        </div>
        <Link to="/payments/new">
          <Button>New Payment</Button>
        </Link>
      </div>

      {isLoading && (
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      )}

      {error && (
        <div className="text-destructive text-center py-8">{error}</div>
      )}

      {!isLoading && !error && (
        <>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Date Range</TableHead>
                  <TableHead className="text-right">Worklogs</TableHead>
                  <TableHead className="text-right">Total ($)</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayed.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="text-center py-8 text-muted-foreground"
                    >
                      No payments found. Create one to get started.
                    </TableCell>
                  </TableRow>
                ) : (
                  displayed.map((pmt: any) => (
                    <TableRow key={pmt.id}>
                      <TableCell className="font-mono text-sm">
                        #{pmt.id}
                      </TableCell>
                      <TableCell>
                        {fmtShortDate(pmt.date_range_start)} – {fmtShortDate(pmt.date_range_end)}
                      </TableCell>
                      <TableCell className="text-right">
                        {pmt.wl_count}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        ${pmt.total_amount.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            pmt.status === "confirmed"
                              ? "default"
                              : "secondary"
                          }
                        >
                          {pmt.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        <span title={fmtDate(pmt.created_at)} className="cursor-default">
                          {timeAgo(pmt.created_at)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Link to={`/payments/${pmt.id}` as any}>
                          <Button variant="outline" size="sm" aria-label={`View payment ${pmt.id}`}>
                            View
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} to{" "}
                {Math.min(page * pageSize, allData.length)} of {allData.length}{" "}
                payments
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  aria-label="Previous page"
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                  aria-label="Next page"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
