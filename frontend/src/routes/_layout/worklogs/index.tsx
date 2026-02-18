import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react"
import { useCallback, useMemo, useState } from "react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { MOCK_WORKLOGS_LIST } from "@/lib/worklog-mock"
import { cn } from "@/lib/utils"

const PAGE_SIZES = [5, 10, 25, 50]

const filterByDateRange = (data: any[], dateFrom: string | null, dateTo: string | null): any[] => {
  if (!dateFrom && !dateTo) return data
  const parse = (s: string) => new Date(s).getTime()
  return data.filter((row) => {
    const t = parse(row.created_at)
    if (dateFrom && t < parse(dateFrom)) return false
    if (dateTo && t > parse(dateTo + "T23:59:59.999Z")) return false
    return true
  })
}

const WorklogsListSkeleton = () => (
  <div className="flex flex-col gap-6">
    <div>
      <Skeleton className="h-8 w-48 mb-2" />
      <Skeleton className="h-4 w-72" />
    </div>
    <div className="flex flex-col gap-2">
      <div className="inline-flex h-9 w-fit items-center justify-center rounded-lg bg-muted/50 p-[3px] gap-1">
        <Skeleton className="h-[26px] w-24 rounded-md" />
        <Skeleton className="h-[26px] w-28 rounded-md" />
        <Skeleton className="h-[26px] w-32 rounded-md" />
      </div>
      <div className="rounded-md border p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div className="space-y-2">
            <Skeleton className="h-4 w-8" />
            <Skeleton className="h-9 w-36" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-4 w-6" />
            <Skeleton className="h-9 w-36" />
          </div>
        </div>
      </div>
    </div>
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-10" />
            <TableHead>Task</TableHead>
            <TableHead>Freelancer</TableHead>
            <TableHead className="text-right">Amount earned</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created (UTC)</TableHead>
            <TableHead className="w-20" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {Array.from({ length: 5 }).map((_, i) => (
            <TableRow key={i}>
              <TableCell><Skeleton className="h-4 w-4" /></TableCell>
              <TableCell><Skeleton className="h-4 w-32" /></TableCell>
              <TableCell><Skeleton className="h-4 w-28" /></TableCell>
              <TableCell><Skeleton className="h-4 w-20 ml-auto" /></TableCell>
              <TableCell><Skeleton className="h-4 w-14" /></TableCell>
              <TableCell><Skeleton className="h-4 w-40" /></TableCell>
              <TableCell><Skeleton className="h-8 w-24" /></TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
    <div className="flex flex-wrap items-center gap-4">
      <Skeleton className="h-9 w-36" />
      <Skeleton className="h-9 w-32" />
      <Skeleton className="h-9 w-56" />
    </div>
  </div>
)

const WorklogsListPage = () => {
  const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"
  const queryClient = useQueryClient()
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [activeFilter, setActiveFilter] = useState<"date" | "exclude_worklog" | "exclude_freelancer">("date")
  const [excludeWorklogIds, setExcludeWorklogIds] = useState<Set<string>>(new Set())
  const [excludeFreelancerIds, setExcludeFreelancerIds] = useState<Set<string>>(new Set())
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [reviewOpen, setReviewOpen] = useState(false)
  const [confirmLoading, setConfirmLoading] = useState(false)
  const [confirmError, setConfirmError] = useState("")
  const [confirmSuccess, setConfirmSuccess] = useState(false)

  const queryParams = useMemo(() => {
    const p: { date_from?: string; date_to?: string } = {}
    if (dateFrom) p.date_from = dateFrom
    if (dateTo) p.date_to = dateTo
    return p
  }, [dateFrom, dateTo])

  const { data, isLoading, error } = useQuery({
    queryKey: ["worklogs", queryParams],
    queryFn: async (): Promise<any> => {
      const q = new URLSearchParams()
      if (queryParams.date_from) q.set("date_from", queryParams.date_from)
      if (queryParams.date_to) q.set("date_to", queryParams.date_to)
      const url = `${API_BASE}/api/v1/worklogs?${q.toString()}`
      try {
        const token = localStorage.getItem("access_token")
        const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
        if (res.ok) return await res.json()
        throw new Error(String(res.status))
      } catch {
        const filtered = filterByDateRange(MOCK_WORKLOGS_LIST, queryParams.date_from ?? null, queryParams.date_to ?? null)
        return { data: filtered, count: filtered.length }
      }
    },
  })

  const worklogs: any[] = data?.data ?? []
  const allWorklogs = worklogs

  const toggleExcludeWorklog = useCallback((id: string) => {
    setExcludeWorklogIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const toggleExcludeFreelancer = useCallback((id: string) => {
    setExcludeFreelancerIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const toggleSelected = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const selectAll = useCallback(() => {
    const isPending = (w: { status?: string }) => (w.status || "").toLowerCase() !== "paid"
    const eligible = allWorklogs.filter(
      (w) =>
        isPending(w) &&
        !excludeWorklogIds.has(w.id) &&
        !excludeFreelancerIds.has(w.freelancer_id)
    )
    setSelectedIds(new Set(eligible.map((w) => w.id)))
  }, [allWorklogs, excludeWorklogIds, excludeFreelancerIds])

  const clearSelection = useCallback(() => setSelectedIds(new Set()), [])

  const eligibleAfterExclusions = useMemo(() => {
    return allWorklogs.filter(
      (w) => !excludeWorklogIds.has(w.id) && !excludeFreelancerIds.has(w.freelancer_id)
    )
  }, [allWorklogs, excludeWorklogIds, excludeFreelancerIds])

  const selectedWorklogs = useMemo(() => {
    return eligibleAfterExclusions.filter((w) => selectedIds.has(w.id))
  }, [eligibleAfterExclusions, selectedIds])

  const totalAmount = useMemo(() => {
    return selectedWorklogs.reduce((sum, w) => sum + (Number(w.amount_earned) || 0), 0)
  }, [selectedWorklogs])

  const paginatedRows = useMemo(() => {
    const start = (page - 1) * pageSize
    return eligibleAfterExclusions.slice(start, start + pageSize)
  }, [eligibleAfterExclusions, page, pageSize])

  const totalPages = Math.max(1, Math.ceil(eligibleAfterExclusions.length / pageSize))
  const uniqueFreelancers = useMemo(() => {
    const seen = new Map<string, any>()
    allWorklogs.forEach((w) => {
      if (!seen.has(w.freelancer_id)) seen.set(w.freelancer_id, { id: w.freelancer_id, name: w.freelancer_name })
    })
    return Array.from(seen.values())
  }, [allWorklogs])

  const handleConfirmPayment = useCallback(async () => {
    setConfirmError("")
    setConfirmLoading(true)
    const url = `${API_BASE}/api/v1/payment-batches`
    const payload = {
      worklog_ids: Array.from(selectedIds),
      exclude_worklog_ids: Array.from(excludeWorklogIds),
      exclude_freelancer_ids: Array.from(excludeFreelancerIds),
    }
    try {
      const token = localStorage.getItem("access_token")
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        await res.json()
        setConfirmSuccess(true)
        setSelectedIds(new Set())
        setReviewOpen(false)
        await queryClient.invalidateQueries({ queryKey: ["worklogs"] })
      } else {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || String(res.status))
      }
    } catch (e) {
      setConfirmError(e instanceof Error ? e.message : "Failed to create payment batch")
    } finally {
      setConfirmLoading(false)
    }
  }, [API_BASE, queryClient, selectedIds, excludeWorklogIds, excludeFreelancerIds])

  if (isLoading) {
    return <WorklogsListSkeleton />
  }

  if (error) {
    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-2xl font-bold tracking-tight">Worklogs</h1>
        <p className="text-destructive">Failed to load worklogs. Please try again.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Worklogs</h1>
          <p className="text-muted-foreground">Review worklogs and prepare payment batches</p>
        </div>
      </div>

      <Tabs value={activeFilter} onValueChange={(v) => setActiveFilter(v as typeof activeFilter)}>
        <TabsList>
          <TabsTrigger value="date">Date range</TabsTrigger>
          <TabsTrigger value="exclude_worklog">Exclude worklog</TabsTrigger>
          <TabsTrigger value="exclude_freelancer">Exclude freelancer</TabsTrigger>
        </TabsList>
        <div className="mt-3 rounded-md border p-4">
          {activeFilter === "date" && (
            <div className="flex flex-wrap items-end gap-4">
              <div className="space-y-2">
                <Label htmlFor="date_from">From</Label>
                <Input
                  id="date_from"
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  aria-label="Filter worklogs from date"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="date_to">To</Label>
                <Input
                  id="date_to"
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  aria-label="Filter worklogs to date"
                />
              </div>
            </div>
          )}
          {activeFilter === "exclude_worklog" && (
            <div className="space-y-2">
              <Label>Exclude worklogs from batch</Label>
              <div className="flex flex-wrap gap-3">
                {allWorklogs.map((w) => (
                  <label key={w.id} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={excludeWorklogIds.has(w.id)}
                      onCheckedChange={() => toggleExcludeWorklog(w.id)}
                      aria-label={`Exclude worklog ${w.id} from payment`}
                    />
                    <span className="text-sm">{w.task_name} – {w.freelancer_name} ({w.id})</span>
                  </label>
                ))}
              </div>
            </div>
          )}
          {activeFilter === "exclude_freelancer" && (
            <div className="space-y-2">
              <Label>Exclude freelancers from batch</Label>
              <div className="flex flex-wrap gap-3">
                {uniqueFreelancers.map((f) => (
                  <label key={f.id} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={excludeFreelancerIds.has(f.id)}
                      onCheckedChange={() => toggleExcludeFreelancer(f.id)}
                      aria-label={`Exclude freelancer ${f.name} from payment`}
                    />
                    <span className="text-sm">{f.name}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </Tabs>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="w-10">
                <Checkbox
                  checked={(() => {
                    const pendingOnPage = paginatedRows.filter(
                      (w) => (w.status || "").toLowerCase() !== "paid"
                    )
                    return (
                      pendingOnPage.length > 0 &&
                      pendingOnPage.every((w) => selectedIds.has(w.id))
                    )
                  })()}
                  onCheckedChange={(checked) => {
                    const pendingOnPage = paginatedRows.filter(
                      (w) => (w.status || "").toLowerCase() !== "paid"
                    )
                    if (checked) {
                      setSelectedIds((s) => {
                        const next = new Set(s)
                        pendingOnPage.forEach((w) => next.add(w.id))
                        return next
                      })
                    } else {
                      setSelectedIds((s) => {
                        const next = new Set(s)
                        pendingOnPage.forEach((w) => next.delete(w.id))
                        return next
                      })
                    }
                  }}
                  aria-label="Select all on page"
                />
              </TableHead>
              <TableHead>Task</TableHead>
              <TableHead>Freelancer</TableHead>
              <TableHead className="text-right">Amount earned</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created (UTC)</TableHead>
              <TableHead className="w-20"><span className="sr-only">Actions</span></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedRows.map((w) => {
              const excluded = excludeWorklogIds.has(w.id) || excludeFreelancerIds.has(w.freelancer_id)
              const isPaid = (w.status || "").toLowerCase() === "paid"
              return (
                <TableRow
                  key={w.id}
                  className={cn(excluded && "opacity-50 bg-muted/30")}
                >
                  <TableCell>
                    {!excluded && !isPaid && (
                      <Checkbox
                        checked={selectedIds.has(w.id)}
                        onCheckedChange={() => toggleSelected(w.id)}
                        aria-label={`Select worklog ${w.id}`}
                      />
                    )}
                  </TableCell>
                  <TableCell>{w.task_name}</TableCell>
                  <TableCell>{w.freelancer_name}</TableCell>
                  <TableCell className="text-right font-medium">
                    ${Number(w.amount_earned).toFixed(2)}
                  </TableCell>
                  <TableCell>
                    <span
                      className={cn(
                        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
                        isPaid
                          ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                          : "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400"
                      )}
                    >
                      {isPaid ? "Paid" : "Pending"}
                    </span>
                  </TableCell>
                  <TableCell>{w.created_at}</TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" asChild>
                      <Link to="/worklogs/$worklogId" params={{ worklogId: w.id }}>
                        View entries
                      </Link>
                    </Button>
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>

        {eligibleAfterExclusions.length > pageSize && (
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 border-t bg-muted/20">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <span className="text-sm text-muted-foreground">
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, eligibleAfterExclusions.length)} of {eligibleAfterExclusions.length} entries
              </span>
              <div className="flex items-center gap-2">
                <p className="text-sm text-muted-foreground">Rows per page</p>
                <Select value={`${pageSize}`} onValueChange={(v) => { setPageSize(Number(v)); setPage(1) }}>
                  <SelectTrigger className="h-8 w-[70px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent side="top">
                    {PAGE_SIZES.map((n) => (
                      <SelectItem key={n} value={`${n}`}>{n}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button variant="outline" size="sm" className="h-8 w-8 p-0" onClick={() => setPage(1)} disabled={page <= 1} aria-label="First page">
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" className="h-8 w-8 p-0" onClick={() => setPage((p) => p - 1)} disabled={page <= 1} aria-label="Previous page">
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground px-2">Page {page} of {totalPages}</span>
              <Button variant="outline" size="sm" className="h-8 w-8 p-0" onClick={() => setPage((p) => p + 1)} disabled={page >= totalPages} aria-label="Next page">
                <ChevronRight className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm" className="h-8 w-8 p-0" onClick={() => setPage(totalPages)} disabled={page >= totalPages} aria-label="Last page">
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <Button variant="outline" size="sm" onClick={selectAll}>Select all eligible</Button>
        <Button variant="outline" size="sm" onClick={clearSelection}>Clear selection</Button>
        <Button onClick={() => setReviewOpen(true)} disabled={selectedWorklogs.length === 0}>
          Review & pay ({selectedWorklogs.length} worklogs, ${totalAmount.toFixed(2)})
        </Button>
      </div>

      {confirmSuccess && (
        <p className="text-sm text-green-600 dark:text-green-400">Payment batch created successfully.</p>
      )}

      {reviewOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-labelledby="review-title">
          <div className="bg-background border rounded-lg shadow-lg p-6 max-w-lg w-full mx-4">
            <h2 id="review-title" className="text-lg font-semibold mb-4">Review payment</h2>
            <p className="text-muted-foreground mb-2">
              {selectedWorklogs.length} worklog(s) selected. Total: ${totalAmount.toFixed(2)}
            </p>
            <ul className="list-disc list-inside text-sm text-muted-foreground mb-4 max-h-40 overflow-y-auto">
              {selectedWorklogs.slice(0, 10).map((w) => (
                <li key={w.id}>{w.task_name} – {w.freelancer_name}: ${Number(w.amount_earned).toFixed(2)}</li>
              ))}
              {selectedWorklogs.length > 10 && <li>… and {selectedWorklogs.length - 10} more</li>}
            </ul>
            {confirmError && <p className="text-sm text-destructive mb-2">{confirmError}</p>}
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => { setReviewOpen(false); setConfirmError("") }} disabled={confirmLoading}>
                Cancel
              </Button>
              <Button onClick={handleConfirmPayment} disabled={confirmLoading}>
                {confirmLoading ? "Processing…" : "Confirm payment"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
};

export const Route = createFileRoute("/_layout/worklogs/")({
  component: WorklogsListPage,
  head: () => ({
    meta: [{ title: "Worklogs - Payment Dashboard" }],
  }),
});
