import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
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
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"

export const Route = createFileRoute("/_layout/payments/new")({
  component: NewPaymentPage,
  head: () => ({
    meta: [{ title: "New Payment - WorkLog Dashboard" }],
  }),
})

function NewPaymentPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")

  // Step 2: review worklogs
  const [worklogs, setWorklogs] = useState<any[]>([])
  const [freelancers, setFreelancers] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Exclusions
  const [excludedWlIds, setExcludedWlIds] = useState<Set<number>>(new Set())
  const [excludedFreelancerIds, setExcludedFreelancerIds] = useState<Set<number>>(new Set())

  // Step 3: submitting
  const [isSubmitting, setIsSubmitting] = useState(false)

  const fetchWorklogs = () => {
    setIsLoading(true)
    setError(null)

    const ax = axios.create()
    ax.defaults.baseURL = "http://localhost:8000"

    const params: any = {
      date_from: dateFrom,
      date_to: dateTo,
      status: "pending",
    }

    Promise.all([
      ax.get("/api/v1/worklogs/", { params }),
      ax.get("/api/v1/freelancers/"),
    ])
      .then(([wlRes, frRes]: any[]) => {
        setWorklogs(wlRes.data.data || [])
        setFreelancers(frRes.data.data || [])
        setIsLoading(false)
      })
      .catch((err: any) => {
        setError("Failed to load worklogs. Please try again.")
        console.error(err)
        setIsLoading(false)
      })
  }

  const toggleWlExclusion = (wlId: number) => {
    setExcludedWlIds((prev) => {
      const next = new Set(prev)
      if (next.has(wlId)) {
        next.delete(wlId)
      } else {
        next.add(wlId)
      }
      return next
    })
  }

  const toggleFreelancerExclusion = (fId: number) => {
    setExcludedFreelancerIds((prev) => {
      const next = new Set(prev)
      if (next.has(fId)) {
        next.delete(fId)
      } else {
        next.add(fId)
      }
      return next
    })
  }

  const includedWorklogs = worklogs.filter(
    (wl: any) =>
      !excludedWlIds.has(wl.id) &&
      !excludedFreelancerIds.has(wl.freelancer_id),
  )

  const totalAmount = includedWorklogs.reduce(
    (sum: number, wl: any) => sum + wl.earned_amount,
    0,
  )

  const totalHours = includedWorklogs.reduce(
    (sum: number, wl: any) => sum + wl.total_hours,
    0,
  )

  const handleSubmit = () => {
    setIsSubmitting(true)

    const ax = axios.create()
    ax.defaults.baseURL = "http://localhost:8000"

    ax.post("/api/v1/payments/", {
      date_range_start: dateFrom,
      date_range_end: dateTo,
      excluded_wl_ids: Array.from(excludedWlIds),
      excluded_freelancer_ids: Array.from(excludedFreelancerIds),
    })
      .then((res: any) => {
        navigate({ to: `/payments/${res.data.id}` })
      })
      .catch((err: any) => {
        setError("Failed to create payment. Please try again.")
        console.error(err)
        setIsSubmitting(false)
      })
  }

  // Get unique freelancers from the loaded worklogs
  const uniqueFreelancers = freelancers.filter((f: any) =>
    worklogs.some((wl: any) => wl.freelancer_id === f.id),
  )

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Create Payment Batch
        </h1>
        <p className="text-muted-foreground">
          Step {step} of 3:{" "}
          {step === 1
            ? "Select Date Range"
            : step === 2
              ? "Review & Exclude"
              : "Confirm Payment"}
        </p>
      </div>

      {/* Step indicators */}
      <div className="flex gap-2">
        <Badge variant={step >= 1 ? "default" : "secondary"}>
          1. Date Range
        </Badge>
        <Badge variant={step >= 2 ? "default" : "secondary"}>
          2. Review
        </Badge>
        <Badge variant={step >= 3 ? "default" : "secondary"}>
          3. Confirm
        </Badge>
      </div>

      {/* Step 1: Date Range Selection */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Select Date Range</CardTitle>
            <CardDescription>
              Choose the date range for worklogs eligible for payment
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex gap-4 items-center">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">From</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-auto"
                  aria-label="Payment start date"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium">To</label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-auto"
                  aria-label="Payment end date"
                />
              </div>
            </div>
            <Button
              onClick={() => {
                fetchWorklogs()
                setStep(2)
              }}
              disabled={!dateFrom || !dateTo}
              className="w-fit"
              aria-label="Continue to review"
            >
              Continue
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Review and Exclude */}
      {step === 2 && (
        <>
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
              {/* Freelancer exclusion */}
              {uniqueFreelancers.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">
                      Exclude Freelancers
                    </CardTitle>
                    <CardDescription>
                      Uncheck to exclude all worklogs from a freelancer
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-4 flex-wrap">
                      {uniqueFreelancers.map((f: any) => (
                        <label
                          key={f.id}
                          className="flex items-center gap-2 cursor-pointer"
                        >
                          <Checkbox
                            checked={!excludedFreelancerIds.has(f.id)}
                            onCheckedChange={() =>
                              toggleFreelancerExclusion(f.id)
                            }
                            aria-label={`Include freelancer ${f.name}`}
                          />
                          <span className="text-sm">{f.name}</span>
                        </label>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Worklogs table with exclusion checkboxes */}
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">Include</TableHead>
                      <TableHead>Task</TableHead>
                      <TableHead>Freelancer</TableHead>
                      <TableHead className="text-right">Hours</TableHead>
                      <TableHead className="text-right">Amount ($)</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {worklogs.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={5}
                          className="text-center py-8 text-muted-foreground"
                        >
                          No pending worklogs found in this date range
                        </TableCell>
                      </TableRow>
                    ) : (
                      worklogs.map((wl: any) => {
                        const isFreelancerExcluded =
                          excludedFreelancerIds.has(wl.freelancer_id)
                        const isExcluded =
                          excludedWlIds.has(wl.id) || isFreelancerExcluded

                        return (
                          <TableRow
                            key={wl.id}
                            className={isExcluded ? "opacity-50" : ""}
                          >
                            <TableCell>
                              <Checkbox
                                checked={!isExcluded}
                                onCheckedChange={() =>
                                  toggleWlExclusion(wl.id)
                                }
                                disabled={isFreelancerExcluded}
                                aria-label={`Include worklog ${wl.task_name}`}
                              />
                            </TableCell>
                            <TableCell>{wl.task_name}</TableCell>
                            <TableCell>{wl.freelancer_name}</TableCell>
                            <TableCell className="text-right">
                              {wl.total_hours.toFixed(1)}
                            </TableCell>
                            <TableCell className="text-right font-medium">
                              ${wl.earned_amount.toFixed(2)}
                            </TableCell>
                          </TableRow>
                        )
                      })
                    )}
                  </TableBody>
                </Table>
              </div>

              {/* Summary */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-muted-foreground">
                        {includedWorklogs.length} of {worklogs.length} worklogs
                        selected
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Total hours: {totalHours.toFixed(1)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">
                        Total Amount
                      </p>
                      <p className="text-2xl font-bold">
                        ${totalAmount.toFixed(2)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setStep(1)}
                  aria-label="Go back to date selection"
                >
                  Back
                </Button>
                <Button
                  onClick={() => setStep(3)}
                  disabled={includedWorklogs.length === 0}
                  aria-label="Continue to confirmation"
                >
                  Continue to Confirm
                </Button>
              </div>
            </>
          )}
        </>
      )}

      {/* Step 3: Confirmation */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle>Confirm Payment</CardTitle>
            <CardDescription>
              Review the summary below and confirm the payment batch
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid gap-2 md:grid-cols-2">
              <div>
                <p className="text-sm text-muted-foreground">Date Range</p>
                <p className="font-medium">
                  {dateFrom} to {dateTo}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">
                  Worklogs Included
                </p>
                <p className="font-medium">{includedWorklogs.length}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Hours</p>
                <p className="font-medium">{totalHours.toFixed(1)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Amount</p>
                <p className="text-2xl font-bold">${totalAmount.toFixed(2)}</p>
              </div>
            </div>

            {excludedWlIds.size > 0 && (
              <p className="text-sm text-muted-foreground">
                {excludedWlIds.size} worklog(s) manually excluded
              </p>
            )}
            {excludedFreelancerIds.size > 0 && (
              <p className="text-sm text-muted-foreground">
                {excludedFreelancerIds.size} freelancer(s) excluded
              </p>
            )}

            {error && (
              <div className="text-destructive text-sm">{error}</div>
            )}

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setStep(2)}
                aria-label="Go back to review"
              >
                Back
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting}
                aria-label="Create payment batch"
              >
                {isSubmitting ? "Creating..." : "Create Payment Batch"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
