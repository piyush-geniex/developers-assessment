import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Banknote, Calendar } from "lucide-react"
import { useEffect, useState } from "react"

import {
  type WorkLogListItem,
  PaymentsService,
  type ConfirmPaymentRequest,
} from "@/api/worklogs"
import { ApiError } from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const Route = createFileRoute("/_layout/payments")({
  component: PaymentsPage,
  head: () => ({
    meta: [{ title: "Process payment - Payment Dashboard" }],
  }),
})

function PaymentsPage() {
  const queryClient = useQueryClient()
  const navigate = Route.useNavigate()
  const { showErrorToast, showSuccessToast } = useCustomToast()
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [previewKey, setPreviewKey] = useState<string | null>(null)
  const [excludedWorkLogIds, setExcludedWorkLogIds] = useState<Set<string>>(
    new Set(),
  )
  const [excludedFreelancerIds, setExcludedFreelancerIds] = useState<
    Set<string>
  >(new Set())

  const { data: preview, isFetching: loadingPreview, isError: previewError, error: previewErrorObj } = useQuery({
    queryKey: ["payment-preview", previewKey],
    queryFn: () =>
      PaymentsService.getPreview({
        date_from: dateFrom,
        date_to: dateTo,
      }),
    enabled: !!previewKey && !!dateFrom && !!dateTo,
  })

  // On 401/403, redirect to dashboard instead of showing error (user stays logged in)
  useEffect(() => {
    if (
      previewError &&
      previewErrorObj instanceof ApiError &&
      (previewErrorObj.status === 401 || previewErrorObj.status === 403)
    ) {
      navigate({ to: "/" })
    }
  }, [previewError, previewErrorObj, navigate])

  const confirmMutation = useMutation({
    mutationFn: (body: ConfirmPaymentRequest) => PaymentsService.confirm(body),
    onSuccess: (remittances) => {
      showSuccessToast(
        `Payment batch created: ${remittances.length} remittance(s) issued.`,
      )
      setPreviewKey(null)
      setExcludedWorkLogIds(new Set())
      setExcludedFreelancerIds(new Set())
      queryClient.invalidateQueries({ queryKey: ["worklogs"] })
    },
    onError: (err) => {
      if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
        navigate({ to: "/" })
      } else if (err instanceof ApiError) {
        handleError.call(showErrorToast, err)
      } else {
        showErrorToast(err instanceof Error ? err.message : "Something went wrong.")
      }
    },
  })

  const loadPreview = () => {
    if (!dateFrom || !dateTo) {
      showErrorToast("Please select both date from and date to.")
      return
    }
    if (dateFrom > dateTo) {
      showErrorToast("From date must be before to date.")
      return
    }
    setPreviewKey(`${dateFrom}-${dateTo}`)
  }

  const workLogs = preview?.work_logs ?? []
  const includedWorkLogs = workLogs.filter(
    (wl) =>
      !excludedWorkLogIds.has(wl.id) && !excludedFreelancerIds.has(wl.user_id),
  )
  const totalIncludedCents = includedWorkLogs.reduce(
    (sum, wl) => sum + wl.amount_cents,
    0,
  )

  const toggleWorkLog = (id: string) => {
    setExcludedWorkLogIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleFreelancer = (userId: string) => {
    setExcludedFreelancerIds((prev) => {
      const next = new Set(prev)
      if (next.has(userId)) next.delete(userId)
      else next.add(userId)
      return next
    })
  }

  const handleConfirm = () => {
    if (!preview || includedWorkLogs.length === 0) {
      showErrorToast("No worklogs selected for payment.")
      return
    }
    confirmMutation.mutate({
      period_start: preview.period_start,
      period_end: preview.period_end,
      include_work_log_ids: includedWorkLogs.map((wl) => wl.id),
      exclude_freelancer_ids: [...excludedFreelancerIds],
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Process payment</h1>
        <p className="text-muted-foreground">
          Select a date range to see eligible worklogs, review the selection,
          exclude any worklogs or freelancers, then confirm payment.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4 rounded-lg border p-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="pay_date_from">From date</Label>
          <div className="relative">
            <Calendar className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="pay_date_from"
              type="date"
              className="pl-8"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="pay_date_to">To date</Label>
          <Input
            id="pay_date_to"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
        <Button onClick={loadPreview} disabled={loadingPreview}>
          {loadingPreview ? "Loading…" : "Load eligible worklogs"}
        </Button>
      </div>

      {preview && (
        <div className="space-y-4 rounded-lg border p-4">
          <h2 className="flex items-center gap-2 font-semibold">
            <Banknote className="h-4 w-4" />
            Review selection
          </h2>
          <p className="text-sm text-muted-foreground">
            Uncheck worklogs or freelancers to exclude them from this payment
            batch.
          </p>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">Include</TableHead>
                <TableHead>Task</TableHead>
                <TableHead>Freelancer</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="w-32">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {workLogs.map((wl: WorkLogListItem) => {
                const excluded =
                  excludedWorkLogIds.has(wl.id) ||
                  excludedFreelancerIds.has(wl.user_id)
                return (
                  <TableRow
                    key={wl.id}
                    className={excluded ? "opacity-50" : undefined}
                  >
                    <TableCell>
                      <Checkbox
                        checked={!excluded}
                        onCheckedChange={() => toggleWorkLog(wl.id)}
                        title="Include this worklog in payment"
                      />
                    </TableCell>
                    <TableCell>{wl.task_title}</TableCell>
                    <TableCell>
                      {wl.user_full_name || wl.user_email}
                    </TableCell>
                    <TableCell className="text-right">
                      ${(wl.amount_cents / 100).toFixed(2)}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-muted-foreground"
                        onClick={() => toggleFreelancer(wl.user_id)}
                        title={
                          excludedFreelancerIds.has(wl.user_id)
                            ? "Include this freelancer again"
                            : "Exclude all worklogs from this freelancer"
                        }
                      >
                        {excludedFreelancerIds.has(wl.user_id)
                          ? "Include freelancer"
                          : "Exclude freelancer"}
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
          <div className="flex items-center justify-between border-t pt-4">
            <p className="font-medium">
              Total to pay: ${(totalIncludedCents / 100).toFixed(2)} (
              {includedWorkLogs.length} worklog
              {includedWorkLogs.length !== 1 ? "s" : ""})
            </p>
            <Button
              onClick={handleConfirm}
              disabled={
                includedWorkLogs.length === 0 || confirmMutation.isPending
              }
            >
              {confirmMutation.isPending ? "Processing…" : "Confirm payment"}
            </Button>
          </div>
        </div>
      )}

      {previewKey && !preview && loadingPreview && (
        <p className="text-muted-foreground">Loading eligible worklogs…</p>
      )}
      {previewKey && preview && preview.work_logs.length === 0 && (
        <p className="text-muted-foreground">
          No unremitted worklogs in this date range.
        </p>
      )}
    </div>
  )
}
