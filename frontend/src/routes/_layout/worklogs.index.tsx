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
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"

export const Route = createFileRoute("/_layout/worklogs/")({
  component: WorklogsPage,
  head: () => ({
    meta: [{ title: "Worklogs - WorkLog Dashboard" }],
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

function WorklogsPage() {
  const [allData, setAllData] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const pageSize = 10

  // Exclusive filter tabs per AGENTS.md
  const [activeFilter, setActiveFilter] = useState<string | null>(null)
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [freelancers, setFreelancers] = useState<any[]>([])
  const [selectedFreelancer, setSelectedFreelancer] = useState<number | null>(null)

  useEffect(() => {
    const ax = axios.create()
    ax.defaults.baseURL = "http://localhost:8000"

    ax.get("/api/v1/freelancers/")
      .then((res: any) => {
        setFreelancers(res.data.data || [])
      })
      .catch((err: any) => {
        console.error(err)
      })
  }, [])

  useEffect(() => {
    setIsLoading(true)
    setError(null)

    const ax = axios.create()
    ax.defaults.baseURL = "http://localhost:8000"

    const params: any = {}
    if (activeFilter === "date" && dateFrom) params.date_from = dateFrom
    if (activeFilter === "date" && dateTo) params.date_to = dateTo
    if (activeFilter === "freelancer" && selectedFreelancer)
      params.freelancer_id = selectedFreelancer

    ax.get("/api/v1/worklogs/", { params })
      .then((res: any) => {
        setAllData(res.data.data || [])
        setIsLoading(false)
      })
      .catch((err: any) => {
        setError("Failed to load worklogs. Please try again.")
        console.error(err)
        setIsLoading(false)
      })
  }, [activeFilter, dateFrom, dateTo, selectedFreelancer])

  const displayed = allData.slice((page - 1) * pageSize, page * pageSize)
  const totalPages = Math.ceil(allData.length / pageSize)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Worklogs</h1>
          <p className="text-muted-foreground">
            View all worklogs and earnings per task
          </p>
        </div>
        <Link to="/payments/new">
          <Button>Create Payment</Button>
        </Link>
      </div>

      {/* Exclusive filter tabs per AGENTS.md */}
      <div className="flex gap-2">
        <Button
          variant={activeFilter === "date" ? "default" : "outline"}
          size="sm"
          onClick={() =>
            setActiveFilter(activeFilter === "date" ? null : "date")
          }
          aria-label="Filter by date range"
        >
          Date Range
        </Button>
        <Button
          variant={activeFilter === "freelancer" ? "default" : "outline"}
          size="sm"
          onClick={() =>
            setActiveFilter(
              activeFilter === "freelancer" ? null : "freelancer",
            )
          }
          aria-label="Filter by freelancer"
        >
          Freelancer
        </Button>
      </div>

      {activeFilter === "date" && (
        <div className="flex gap-4 items-center">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">From:</label>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value)
                setPage(1)
              }}
              className="w-auto"
              aria-label="Start date filter"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">To:</label>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value)
                setPage(1)
              }}
              className="w-auto"
              aria-label="End date filter"
            />
          </div>
        </div>
      )}

      {activeFilter === "freelancer" && (
        <div className="flex gap-2 flex-wrap">
          {freelancers.map((f: any) => (
            <Button
              key={f.id}
              variant={selectedFreelancer === f.id ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setSelectedFreelancer(
                  selectedFreelancer === f.id ? null : f.id,
                )
                setPage(1)
              }}
              aria-label={`Filter by freelancer ${f.name}`}
            >
              {f.name}
            </Button>
          ))}
        </div>
      )}

      {isLoading && (
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
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
                  <TableHead>Task</TableHead>
                  <TableHead>Freelancer</TableHead>
                  <TableHead className="text-right">Hours</TableHead>
                  <TableHead className="text-right">Rate ($/hr)</TableHead>
                  <TableHead className="text-right">Earned ($)</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayed.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="text-center py-8 text-muted-foreground"
                    >
                      No worklogs found
                    </TableCell>
                  </TableRow>
                ) : (
                  displayed.map((wl: any) => (
                    <TableRow key={wl.id} className="cursor-pointer hover:bg-muted/50">
                      <TableCell>
                        <Link
                          to={`/worklogs/${wl.id}` as any}
                          className="font-medium hover:underline text-primary"
                        >
                          {wl.task_name}
                        </Link>
                      </TableCell>
                      <TableCell>{wl.freelancer_name || "Unknown"}</TableCell>
                      <TableCell className="text-right">
                        {wl.total_hours.toFixed(1)}
                      </TableCell>
                      <TableCell className="text-right">
                        {wl.hourly_rate?.toFixed(2) || "0.00"}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        ${wl.earned_amount.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            wl.status === "paid" ? "default" : "secondary"
                          }
                        >
                          {wl.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        <span title={fmtDate(wl.created_at)} className="cursor-default">
                          {timeAgo(wl.created_at)}
                        </span>
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
                worklogs
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
