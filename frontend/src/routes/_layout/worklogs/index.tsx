import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ChevronRight, Loader2 } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import useAuth from "@/hooks/useAuth"
import { toast } from "sonner"

const API_URL = import.meta.env.VITE_API_URL

async function fetchWorklogs(params: {
  start_date?: string
  end_date?: string
}): Promise<any> {
  const token = localStorage.getItem("access_token")
  const url = new URL(`${API_URL}/api/v1/worklogs/`)
  if (params.start_date) url.searchParams.set("start_date", params.start_date)
  if (params.end_date) url.searchParams.set("end_date", params.end_date)
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to load worklogs")
  return res.json()
}

async function createPaymentBatch(worklogIds: string[]): Promise<any> {
  const token = localStorage.getItem("access_token")
  const res = await fetch(`${API_URL}/api/v1/worklogs/payment-batch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ worklog_ids: worklogIds }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || "Failed to create payment")
  }
  return res.json()
}

export const Route = createFileRoute("/_layout/worklogs/")({
  component: WorklogsPage,
  head: () => ({
    meta: [{ title: "Worklogs - Payment Dashboard" }],
  }),
})

function WorklogsPage() {
  const { user } = useAuth()
  const [activeFilter, setActiveFilter] = useState<"all" | "date">("all")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [reviewOpen, setReviewOpen] = useState(false)
  const [paying, setPaying] = useState(false)

  const params: Record<string, string> = {}
  if (activeFilter === "date" && startDate) params.start_date = startDate
  if (activeFilter === "date" && endDate) params.end_date = endDate

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["worklogs", params],
    queryFn: () => fetchWorklogs(params),
  })

  const worklogs = data?.data ?? []
  const [page, setPage] = useState(1)
  const pageSize = 10
  const displayed = worklogs.slice((page - 1) * pageSize, page * pageSize)
  const totalPages = Math.ceil(worklogs.length / pageSize) || 1

  const selectedWorklogs = worklogs.filter((w: any) =>
    selectedIds.has(w.id)
  )
  const totalAmount = selectedWorklogs.reduce(
    (sum: number, w: any) => sum + (w.total_amount ?? 0),
    0
  )

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === displayed.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(displayed.map((w: any) => w.id)))
    }
  }

  const handleConfirmPayment = async () => {
    if (selectedIds.size === 0) return
    setPaying(true)
    try {
      await createPaymentBatch(Array.from(selectedIds))
      toast.success("Payment completed successfully")
      setReviewOpen(false)
      setSelectedIds(new Set())
      refetch()
    } catch (e: any) {
      toast.error("Payment failed", {
        description: e?.message ?? "Unknown error",
      })
    } finally {
      setPaying(false)
    }
  }

  const isAdmin = user?.is_superuser ?? false

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Worklogs</h1>
          <p className="text-muted-foreground">
            Review work and process payments
          </p>
        </div>
      </div>

      <Tabs
        value={activeFilter}
        onValueChange={(v) => setActiveFilter(v as "all" | "date")}
      >
        <TabsList>
          <TabsTrigger value="all">All worklogs</TabsTrigger>
          <TabsTrigger value="date">
            Date range
            {activeFilter === "date" && (
              <div className="ml-4 flex gap-2 items-center">
                <input
                  type="date"
                  className="rounded border px-2 py-1 text-sm"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  aria-label="Start date"
                />
                <span className="text-muted-foreground">to</span>
                <input
                  type="date"
                  className="rounded border px-2 py-1 text-sm"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  aria-label="End date"
                />
              </div>
            )}
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <p className="text-destructive">Failed to load worklogs. Please try again.</p>
      ) : (
        <>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  {isAdmin && (
                    <TableHead className="w-12">
                      <Checkbox
                        checked={
                          displayed.length > 0 &&
                          displayed.every((w: any) => selectedIds.has(w.id))
                        }
                        onCheckedChange={toggleSelectAll}
                        aria-label="Select all"
                      />
                    </TableHead>
                  )}
                  <TableHead>Task</TableHead>
                  <TableHead>Freelancer</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-12" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayed.map((w: any) => (
                  <TableRow key={w.id}>
                    {isAdmin && (
                      <TableCell>
                        {w.payment_batch_id ? null : (
                          <Checkbox
                            checked={selectedIds.has(w.id)}
                            onCheckedChange={() => toggleSelect(w.id)}
                            aria-label={`Select worklog ${w.id}`}
                          />
                        )}
                      </TableCell>
                    )}
                    <TableCell className="font-medium">{w.task_title}</TableCell>
                    <TableCell>{w.freelancer_email}</TableCell>
                    <TableCell>
                      ${Number(w.total_amount ?? 0).toFixed(2)}
                    </TableCell>
                    <TableCell>{w.status}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {w.created_at}
                    </TableCell>
                    <TableCell>
                      <Link
                        to="/worklogs/$worklogId"
                        params={{ worklogId: w.id }}
                        className="inline-flex items-center text-sm text-primary hover:underline"
                      >
                        View
                        <ChevronRight className="h-4 w-4" />
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
              >
                Next
              </Button>
            </div>
          )}

          {isAdmin && selectedIds.size > 0 && (
            <Button onClick={() => setReviewOpen(true)}>
              Review payment ({selectedIds.size} worklogs)
            </Button>
          )}
        </>
      )}

      <Dialog open={reviewOpen} onOpenChange={setReviewOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review payment</DialogTitle>
            <DialogDescription>
              Confirm payment for {selectedWorklogs.length} worklog(s). Total: $
              {totalAmount.toFixed(2)}
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-48 overflow-y-auto rounded border p-2 text-sm">
            {selectedWorklogs.map((w: any) => (
              <div
                key={w.id}
                className="flex justify-between py-1"
              >
                <span>
                  {w.task_title} – {w.freelancer_email}
                </span>
                <span>${Number(w.total_amount).toFixed(2)}</span>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setReviewOpen(false)}
              disabled={paying}
            >
              Cancel
            </Button>
            <Button onClick={handleConfirmPayment} disabled={paying}>
              {paying ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                "Confirm payment"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
