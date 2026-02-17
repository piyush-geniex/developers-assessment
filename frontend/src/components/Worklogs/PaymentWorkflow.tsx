import { useState, useEffect } from "react"
import { Calendar, DollarSign, CheckCircle2, X } from "lucide-react"
import axios from "axios"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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
import { Checkbox } from "@/components/ui/checkbox"
import { toast } from "sonner"

interface Payment {
  id: string
  worklog_id: string
  payment_batch_id: string
  amount: number
  status: string
  created_at: string
  processed_at: string | null
  worklog: {
    id: string
    task_id: string
    freelancer_id: string
    status: string
    created_at: string
    updated_at: string
    total_earnings: number | null
    task: {
      id: string
      title: string
    } | null
    freelancer: {
      id: string
      email: string
      full_name: string | null
    } | null
  } | null
}

interface PaymentBatch {
  id: string
  status: string
  start_date: string
  end_date: string
  notes: string | null
  created_at: string
  processed_at: string | null
  total_amount: number
  payment_count: number | null
  payments: Payment[]
}

interface PaymentWorkflowProps {
  onPaymentComplete?: () => void
}

export function PaymentWorkflow({ onPaymentComplete }: PaymentWorkflowProps) {
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [excludedWorklogIds, setExcludedWorklogIds] = useState<Set<string>>(new Set())
  const [excludedFreelancerIds, setExcludedFreelancerIds] = useState<Set<string>>(new Set())
  const [batch, setBatch] = useState<PaymentBatch | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isConfirming, setIsConfirming] = useState(false)
  const [eligibleWorklogs, setEligibleWorklogs] = useState<any[]>([])
  const [isLoadingWorklogs, setIsLoadingWorklogs] = useState(false)

  const axiosInstance = axios.create({
    baseURL: "http://localhost:8000",
  })

  // Auto-load worklogs when dates are selected
  useEffect(() => {
    if (startDate && endDate && !batch) {
      loadEligibleWorklogs()
    }
  }, [startDate, endDate])

  const loadEligibleWorklogs = async () => {
    if (!startDate || !endDate) {
      return
    }

    setIsLoadingWorklogs(true)
    try {
      const token = localStorage.getItem("access_token")
      const response = await axiosInstance.get("http://localhost:8000/api/v1/worklogs", {
        params: {
          start_date: new Date(startDate).toISOString(),
          end_date: new Date(endDate).toISOString(),
          skip: 0,
          limit: 1000,
        },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setEligibleWorklogs(response.data.data || [])
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to load worklogs")
      setEligibleWorklogs([])
    } finally {
      setIsLoadingWorklogs(false)
    }
  }

  const handleCreateBatch = async () => {
    if (!startDate || !endDate) {
      toast.error("Please select both start and end dates")
      return
    }

    setIsCreating(true)
    try {
      const token = localStorage.getItem("access_token")
      const response = await axiosInstance.post(
        "http://localhost:8000/api/v1/worklogs/payment-batch",
        {
          start_date: new Date(startDate).toISOString(),
          end_date: new Date(endDate).toISOString(),
          excluded_worklog_ids: Array.from(excludedWorklogIds),
          excluded_freelancer_ids: Array.from(excludedFreelancerIds),
          notes: null,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      setBatch(response.data as any)
      toast.success("Payment batch created successfully")
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to create payment batch")
    } finally {
      setIsCreating(false)
    }
  }

  const handleRemovePayment = async (paymentId: string) => {
    if (!batch) return

    try {
      const token = localStorage.getItem("access_token")
      await axiosInstance.delete(
        `http://localhost:8000/api/v1/worklogs/payment-batch/${batch.id}/payments/${paymentId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      // Update local batch state
      const remainingPayments = batch.payments.filter((p) => p.id !== paymentId)
      const newTotal = remainingPayments.reduce((sum, p) => sum + p.amount, 0)

      setBatch({
        ...batch,
        payments: remainingPayments,
        total_amount: newTotal,
        payment_count: remainingPayments.length,
      })

      toast.success("Payment removed from batch")
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to remove payment")
    }
  }

  const handleConfirmPayment = async () => {
    if (!batch) return

    setIsConfirming(true)
    try {
      const token = localStorage.getItem("access_token")
      await axiosInstance.post(
        `http://localhost:8000/api/v1/worklogs/payment-batch/${batch.id}/confirm`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      toast.success("Payment batch confirmed and processed")
      if (onPaymentComplete) {
        onPaymentComplete()
      }
      setBatch(null)
      setStartDate("")
      setEndDate("")
      setExcludedWorklogIds(new Set())
      setExcludedFreelancerIds(new Set())
      setEligibleWorklogs([])
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to confirm payment")
    } finally {
      setIsConfirming(false)
    }
  }

  const toggleWorklogExclusion = (worklogId: string) => {
    const newSet = new Set(excludedWorklogIds)
    if (newSet.has(worklogId)) {
      newSet.delete(worklogId)
    } else {
      newSet.add(worklogId)
    }
    setExcludedWorklogIds(newSet)
  }

  const toggleFreelancerExclusion = (freelancerId: string) => {
    const newSet = new Set(excludedFreelancerIds)
    if (newSet.has(freelancerId)) {
      newSet.delete(freelancerId)
    } else {
      newSet.add(freelancerId)
    }
    setExcludedFreelancerIds(newSet)
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Process Payments</h1>
        <p className="text-muted-foreground">
          Select a date range and review worklogs before processing payments
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Date Range Selection</CardTitle>
          <CardDescription>
            Select the date range for worklogs eligible for payment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button
              onClick={handleCreateBatch}
              disabled={isCreating || !startDate || !endDate || isLoadingWorklogs}
            >
              <Calendar className="mr-2 h-4 w-4" />
              {isCreating ? "Creating..." : "Create Payment Batch"}
            </Button>
            {isLoadingWorklogs && (
              <span className="text-sm text-muted-foreground flex items-center">
                Loading eligible worklogs...
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {eligibleWorklogs.length > 0 && !batch && (
        <Card>
          <CardHeader>
            <CardTitle>Eligible Worklogs</CardTitle>
            <CardDescription>
              Uncheck worklogs or freelancers to exclude them from the payment batch
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4 p-3 bg-muted rounded-md">
              <div className="text-sm space-y-1">
                <div className="flex items-center justify-between">
                  <span>Total Eligible Worklogs:</span>
                  <span className="font-medium">{eligibleWorklogs.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Excluded Worklogs:</span>
                  <span className="font-medium text-destructive">
                    {excludedWorklogIds.size}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Excluded Freelancers:</span>
                  <span className="font-medium text-destructive">
                    {excludedFreelancerIds.size}
                  </span>
                </div>
                <div className="flex items-center justify-between pt-2 border-t">
                  <span className="font-semibold">Will be included:</span>
                  <span className="font-semibold text-green-600">
                    {eligibleWorklogs.filter(
                      (wl) =>
                        !excludedWorklogIds.has(wl.id) &&
                        !excludedFreelancerIds.has(wl.freelancer_id)
                    ).length}
                  </span>
                </div>
              </div>
            </div>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">Include</TableHead>
                    <TableHead>Task</TableHead>
                    <TableHead>Freelancer</TableHead>
                    <TableHead className="text-right">Earnings</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {eligibleWorklogs.map((worklog) => {
                    const isWorklogExcluded = excludedWorklogIds.has(worklog.id)
                    const isFreelancerExcluded = excludedFreelancerIds.has(
                      worklog.freelancer_id
                    )
                    const isExcluded = isWorklogExcluded || isFreelancerExcluded

                    return (
                      <TableRow
                        key={worklog.id}
                        className={isExcluded ? "opacity-50 bg-muted/50" : ""}
                      >
                        <TableCell>
                          <Checkbox
                            checked={!isWorklogExcluded}
                            onCheckedChange={() =>
                              toggleWorklogExclusion(worklog.id)
                            }
                          />
                        </TableCell>
                        <TableCell className="font-medium">
                          {worklog.task?.title || "Unknown"}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Checkbox
                              checked={!isFreelancerExcluded}
                              onCheckedChange={() =>
                                toggleFreelancerExclusion(worklog.freelancer_id)
                              }
                            />
                            <span>
                              {worklog.freelancer?.full_name ||
                                worklog.freelancer?.email ||
                                "Unknown"}
                            </span>
                            {isFreelancerExcluded && (
                              <span className="text-xs text-destructive">
                                (excluded)
                              </span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          ${worklog.total_earnings?.toFixed(2) || "0.00"}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {batch && (
        <>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Payment Batch Review</CardTitle>
                  <CardDescription>
                    Review the selected payments before confirming
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2 text-lg font-semibold">
                  <DollarSign className="h-5 w-5" />
                  Total: ${batch.total_amount.toFixed(2)}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Task</TableHead>
                      <TableHead>Freelancer</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {batch.payments.map((payment) => (
                      <TableRow key={payment.id}>
                        <TableCell className="font-medium">
                          {payment.worklog?.task?.title || "Unknown"}
                        </TableCell>
                        <TableCell>
                          {payment.worklog?.freelancer?.full_name ||
                            payment.worklog?.freelancer?.email ||
                            "Unknown"}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          ${payment.amount.toFixed(2)}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemovePayment(payment.id)}
                            className="h-8 w-8 p-0 hover:bg-destructive/10"
                          >
                            <X className="h-4 w-4 text-destructive" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Confirm Payment</CardTitle>
              <CardDescription>
                Review the summary and confirm to process the payment batch
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Total Amount:</span>
                  <span className="text-lg font-semibold">
                    ${batch.total_amount.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Number of Payments:</span>
                  <span className="text-lg font-semibold">
                    {batch.payment_count || batch.payments.length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Status:</span>
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                      batch.status === "PENDING"
                        ? "bg-yellow-100 text-yellow-800"
                        : "bg-green-100 text-green-800"
                    }`}
                  >
                    {batch.status}
                  </span>
                </div>
                <Button
                  onClick={handleConfirmPayment}
                  disabled={isConfirming || batch.status !== "PENDING"}
                  className="w-full"
                  size="lg"
                >
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  {isConfirming ? "Processing..." : "Confirm and Process Payment"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

