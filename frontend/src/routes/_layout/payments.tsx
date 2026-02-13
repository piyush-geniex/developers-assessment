import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { CreditCard } from "lucide-react"
import { useState } from "react"

import type {
  EligibleTimeEntry,
  PaymentBatchDetail,
  PaymentBatchPublic,
} from "@/client"
import { PaymentsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import PendingItems from "@/components/Pending/PendingItems"
import { getColumns } from "@/components/Payments/columns"
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import useCustomToast from "@/hooks/useCustomToast"

export const Route = createFileRoute("/_layout/payments")({
  component: Payments,
  head: () => ({
    meta: [{ title: "Payments - FastAPI Cloud" }],
  }),
})

// ─── Create Batch Dialog ─────────────────────────────────────────────────────

interface CreateBatchDialogProps {
  open: boolean
  onClose: () => void
}

function CreateBatchDialog({ open, onClose }: CreateBatchDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const [step, setStep] = useState<"dates" | "review">("dates")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [batchDetail, setBatchDetail] = useState<PaymentBatchDetail | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const createMutation = useMutation({
    mutationFn: () =>
      PaymentsService.createBatch({
        requestBody: { date_from: dateFrom, date_to: dateTo },
      }),
    onSuccess: (data) => {
      setBatchDetail(data)
      const allIds = new Set(data.eligible_entries.map((e) => e.time_entry_id))
      setSelectedIds(allIds)
      setStep("review")
    },
    onError: () => {
      showErrorToast("Failed to create payment batch")
    },
  })

  const confirmMutation = useMutation({
    mutationFn: () =>
      PaymentsService.confirmBatch({
        batchId: batchDetail!.batch.id,
        requestBody: Array.from(selectedIds),
      }),
    onSuccess: () => {
      showSuccessToast("Payment batch confirmed")
      queryClient.invalidateQueries({ queryKey: ["payment-batches"] })
      handleClose()
    },
    onError: () => {
      showErrorToast("Failed to confirm payment batch")
    },
  })

  const handleClose = () => {
    setStep("dates")
    setDateFrom("")
    setDateTo("")
    setBatchDetail(null)
    setSelectedIds(new Set())
    onClose()
  }

  const toggleEntry = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = () => {
    if (!batchDetail) return
    const allIds = batchDetail.eligible_entries.map((e) => e.time_entry_id)
    if (selectedIds.size === allIds.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(allIds))
    }
  }

  const selectedEntries: EligibleTimeEntry[] =
    batchDetail?.eligible_entries.filter((e) => selectedIds.has(e.time_entry_id)) ?? []

  const totalHours = selectedEntries.reduce((sum, e) => sum + e.hours, 0)
  const totalAmount = selectedEntries.reduce((sum, e) => sum + e.amount, 0)

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className={step === "review" ? "max-w-4xl" : "max-w-md"}>
        {step === "dates" && (
          <>
            <DialogHeader>
              <DialogTitle>Create Payment Batch</DialogTitle>
              <DialogDescription>
                Select a date range to find eligible time entries.
              </DialogDescription>
            </DialogHeader>
            <div className="flex flex-col gap-4 py-2">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="cb-date-from">From</Label>
                <Input
                  id="cb-date-from"
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="cb-date-to">To</Label>
                <Input
                  id="cb-date-to"
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={() => createMutation.mutate()}
                disabled={!dateFrom || !dateTo || createMutation.isPending}
              >
                {createMutation.isPending ? "Loading..." : "Find Entries"}
              </Button>
            </DialogFooter>
          </>
        )}

        {step === "review" && batchDetail && (
          <>
            <DialogHeader>
              <DialogTitle>Review Eligible Entries</DialogTitle>
              <DialogDescription>
                Select which time entries to include in this payment batch. Uncheck entries to exclude them.
              </DialogDescription>
            </DialogHeader>

            <div className="overflow-auto max-h-[50vh]">
              {batchDetail.eligible_entries.length === 0 ? (
                <p className="text-center py-8 text-muted-foreground">
                  No unpaid time entries found for the selected date range.
                </p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="py-2 pr-3 text-left w-8">
                        <Checkbox
                          checked={selectedIds.size === batchDetail.eligible_entries.length}
                          onCheckedChange={toggleAll}
                        />
                      </th>
                      <th className="py-2 pr-3 text-left font-medium text-muted-foreground">Freelancer</th>
                      <th className="py-2 pr-3 text-left font-medium text-muted-foreground">Task</th>
                      <th className="py-2 pr-3 text-right font-medium text-muted-foreground">Hours</th>
                      <th className="py-2 pr-3 text-right font-medium text-muted-foreground">Rate</th>
                      <th className="py-2 text-right font-medium text-muted-foreground">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batchDetail.eligible_entries.map((entry) => (
                      <tr key={entry.time_entry_id} className="border-b last:border-0 hover:bg-muted/50">
                        <td className="py-2 pr-3">
                          <Checkbox
                            checked={selectedIds.has(entry.time_entry_id)}
                            onCheckedChange={() => toggleEntry(entry.time_entry_id)}
                          />
                        </td>
                        <td className="py-2 pr-3 font-medium">{entry.freelancer_name}</td>
                        <td className="py-2 pr-3 text-muted-foreground">{entry.task_title}</td>
                        <td className="py-2 pr-3 text-right tabular-nums">{entry.hours.toFixed(2)}h</td>
                        <td className="py-2 pr-3 text-right tabular-nums">${entry.hourly_rate}/h</td>
                        <td className="py-2 text-right tabular-nums font-medium">${entry.amount.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {batchDetail.eligible_entries.length > 0 && (
              <div className="flex justify-between rounded-lg border bg-muted/50 px-4 py-3 text-sm">
                <span className="text-muted-foreground">
                  {selectedIds.size} of {batchDetail.eligible_entries.length} entries selected
                </span>
                <div className="flex gap-6">
                  <span>
                    <span className="text-muted-foreground">Hours: </span>
                    <span className="font-medium tabular-nums">{totalHours.toFixed(2)}h</span>
                  </span>
                  <span>
                    <span className="text-muted-foreground">Total: </span>
                    <span className="font-bold tabular-nums">${totalAmount.toFixed(2)}</span>
                  </span>
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={() => confirmMutation.mutate()}
                disabled={selectedIds.size === 0 || confirmMutation.isPending}
              >
                {confirmMutation.isPending
                  ? "Processing..."
                  : `Confirm ${selectedIds.size > 0 ? `(${selectedIds.size})` : ""}`}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ─── View Batch Dialog ────────────────────────────────────────────────────────

interface ViewBatchDialogProps {
  batch: PaymentBatchPublic | null
  onClose: () => void
}

function ViewBatchDialog({ batch, onClose }: ViewBatchDialogProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["batch-payments", batch?.id],
    queryFn: () => PaymentsService.readBatchPayments({ batchId: batch!.id }),
    enabled: !!batch,
  })

  return (
    <Dialog open={!!batch} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Batch Payments</DialogTitle>
          <DialogDescription>
            {batch && `${batch.date_from} — ${batch.date_to}`}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <PendingItems />
        ) : !data || data.data.length === 0 ? (
          <p className="text-center py-8 text-muted-foreground">No payments recorded for this batch.</p>
        ) : (
          <div className="overflow-auto max-h-[60vh]">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 pr-3 text-left font-medium text-muted-foreground">Freelancer</th>
                  <th className="py-2 pr-3 text-left font-medium text-muted-foreground">Task</th>
                  <th className="py-2 pr-3 text-right font-medium text-muted-foreground">Hours</th>
                  <th className="py-2 pr-3 text-right font-medium text-muted-foreground">Rate</th>
                  <th className="py-2 text-right font-medium text-muted-foreground">Amount</th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((p) => (
                  <tr key={p.id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="py-2 pr-3 font-medium">{p.freelancer_name}</td>
                    <td className="py-2 pr-3 text-muted-foreground">{p.task_title}</td>
                    <td className="py-2 pr-3 text-right tabular-nums">{p.hours.toFixed(2)}h</td>
                    <td className="py-2 pr-3 text-right tabular-nums">${p.hourly_rate}/h</td>
                    <td className="py-2 text-right tabular-nums font-medium">${p.amount.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {batch && batch.total_amount > 0 && (
          <div className="flex justify-end rounded-lg border bg-muted/50 px-4 py-3 text-sm">
            <span>
              <span className="text-muted-foreground">Total Paid: </span>
              <span className="font-bold tabular-nums">${batch.total_amount.toFixed(2)}</span>
            </span>
          </div>
        )}

        <DialogFooter>
          <Button onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Delete Batch Dialog ──────────────────────────────────────────────────────

interface DeleteBatchDialogProps {
  batch: PaymentBatchPublic | null
  onClose: () => void
}

function DeleteBatchDialog({ batch, onClose }: DeleteBatchDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteMutation = useMutation({
    mutationFn: () => PaymentsService.deleteBatch({ batchId: batch!.id }),
    onSuccess: () => {
      showSuccessToast("Payment batch deleted")
      queryClient.invalidateQueries({ queryKey: ["payment-batches"] })
      onClose()
    },
    onError: () => {
      showErrorToast("Failed to delete batch")
    },
  })

  return (
    <Dialog open={!!batch} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Payment Batch</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete this draft batch? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

function Payments() {
  const [showCreate, setShowCreate] = useState(false)
  const [viewBatch, setViewBatch] = useState<PaymentBatchPublic | null>(null)
  const [deleteBatch, setDeleteBatch] = useState<PaymentBatchPublic | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ["payment-batches"],
    queryFn: () => PaymentsService.readBatches({ skip: 0, limit: 100 }),
  })

  const columns = getColumns({
    onView: setViewBatch,
    onDelete: setDeleteBatch,
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Payment Batches</h1>
          <p className="text-muted-foreground">Process freelancer payments in batches</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>Create Payment Batch</Button>
      </div>

      {isLoading ? (
        <PendingItems />
      ) : !data || data.data.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center py-12">
          <div className="rounded-full bg-muted p-4 mb-4">
            <CreditCard className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">No payment batches yet</h3>
          <p className="text-muted-foreground">Create a batch to process freelancer payments</p>
        </div>
      ) : (
        <DataTable columns={columns} data={data.data} />
      )}

      <CreateBatchDialog open={showCreate} onClose={() => setShowCreate(false)} />
      <ViewBatchDialog batch={viewBatch} onClose={() => setViewBatch(null)} />
      <DeleteBatchDialog batch={deleteBatch} onClose={() => setDeleteBatch(null)} />
    </div>
  )
}
