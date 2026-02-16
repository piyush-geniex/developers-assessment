import { useSuspenseQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { ArrowLeft, DollarSign } from "lucide-react"
import { Suspense, useState } from "react"

import { WorklogsService } from "@/components/Worklogs/service"
import PendingItems from "@/components/Pending/PendingItems"
import { Button } from "@/components/ui/button"
import useCustomToast from "@/hooks/useCustomToast"

function getWorklogsQueryOptions() {
    return {
        queryFn: () => WorklogsService.readWorklogs({ skip: 0, limit: 1000 }),
        queryKey: ["worklogs-payment"],
    }
}

export const Route = createFileRoute("/_layout/payment-review")({
    component: PaymentReview,
    head: () => ({
        meta: [
            {
                title: "Payment Review - FastAPI Cloud",
            },
        ],
    }),
})

function PaymentReviewContent() {
    const searchParams = Route.useSearch() as { ids: string }
    const selectedIds = searchParams.ids.split(",").map((id) => parseInt(id))

    const { data: allWorklogs } = useSuspenseQuery(getWorklogsQueryOptions())
    const navigate = useNavigate()
    const { showSuccessToast, showErrorToast } = useCustomToast()
    const queryClient = useQueryClient()

    const [excludedIds, setExcludedIds] = useState<Set<number>>(new Set())

    const selectedWorklogs = allWorklogs.data.filter((w: any) =>
        selectedIds.includes(w.id) && !excludedIds.has(w.id)
    )

    const totalAmount = selectedWorklogs.reduce(
        (sum: number, w: any) => sum + w.total_earned,
        0
    )

    const excludeMutation = useMutation({
        mutationFn: async (id: number) => {
            await WorklogsService.updateWorklog(id, { status: "EXCLUDED" })
            return id
        },
        onSuccess: (id) => {
            setExcludedIds((prev) => new Set([...prev, id]))
            showSuccessToast("Worklog excluded from payment batch")
        },
        onError: () => {
            showErrorToast("Failed to exclude worklog. Please try again.")
        },
    })

    const processPaymentMutation = useMutation({
        mutationFn: async () => {
            const worklogIds = selectedWorklogs.map((w: any) => w.id)
            return await WorklogsService.createPaymentBatch(worklogIds)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["worklogs"] })
            showSuccessToast(`Successfully processed payment for ${selectedWorklogs.length} worklogs`)
            navigate({ to: "/worklogs" })
        },
        onError: () => {
            showErrorToast("Failed to process payment. Please try again.")
        },
    })

    const handleConfirmPayment = () => {
        if (selectedWorklogs.length === 0) {
            showErrorToast("No worklogs to process - all have been excluded")
            return
        }
        processPaymentMutation.mutate()
    }

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => navigate({ to: "/worklogs" })}
                >
                    <ArrowLeft className="h-4 w-4" />
                </Button>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold tracking-tight">Review Payment</h1>
                    <p className="text-muted-foreground">
                        Review and confirm payment for selected worklogs
                    </p>
                </div>
            </div>

            {/* Summary Card */}
            <div className="rounded-lg border bg-card p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <div className="text-sm font-medium text-muted-foreground">
                            Total Payment Amount
                        </div>
                        <div className="text-3xl font-bold mt-1">${totalAmount.toFixed(2)}</div>
                        <div className="text-sm text-muted-foreground mt-1">
                            {selectedWorklogs.length} worklog{selectedWorklogs.length !== 1 ? "s" : ""}
                        </div>
                    </div>
                    <div className="rounded-full bg-primary/10 p-4">
                        <DollarSign className="h-8 w-8 text-primary" />
                    </div>
                </div>
            </div>

            {/* Freelancer Grouped Worklogs */}
            <div className="rounded-lg border">
                <div className="border-b bg-muted/50 px-6 py-4">
                    <h2 className="text-lg font-semibold">Worklogs grouped by freelancer</h2>
                </div>
                <div className="divide-y">
                    {(() => {
                        // Group worklogs by freelancer_id
                        const groupedByFreelancer = selectedWorklogs.reduce((acc: any, worklog: any) => {
                            const freelancerId = worklog.freelancer_id
                            if (!acc[freelancerId]) {
                                acc[freelancerId] = []
                            }
                            acc[freelancerId].push(worklog)
                            return acc
                        }, {})

                        const freelancerIds = Object.keys(groupedByFreelancer).sort((a, b) => parseInt(a) - parseInt(b))

                        return freelancerIds.map((freelancerId) => {
                            const freelancerWorklogs = groupedByFreelancer[freelancerId]
                            const freelancerTotal = freelancerWorklogs.reduce(
                                (sum: number, w: any) => sum + w.total_earned,
                                0
                            )

                            return (
                                <div key={freelancerId} className="p-6">
                                    {/* Freelancer Header */}
                                    <div className="flex items-center justify-between mb-4">
                                        <div>
                                            <div className="font-semibold text-lg">
                                                Freelancer ID: {freelancerId}
                                            </div>
                                            <div className="text-sm text-muted-foreground">
                                                {freelancerWorklogs.length} worklog{freelancerWorklogs.length !== 1 ? "s" : ""} • $
                                                {freelancerTotal.toFixed(2)}
                                            </div>
                                        </div>
                                        <Button
                                            variant="destructive"
                                            size="sm"
                                            onClick={() => {
                                                // Exclude all worklogs for this freelancer
                                                freelancerWorklogs.forEach((worklog: any) => {
                                                    excludeMutation.mutate(worklog.id)
                                                })
                                                showSuccessToast(`Excluded all worklogs from Freelancer ${freelancerId}`)
                                            }}
                                            disabled={excludeMutation.isPending}
                                        >
                                            Exclude Freelancer
                                        </Button>
                                    </div>

                                    {/* Freelancer's Worklogs */}
                                    <div className="space-y-2 ml-4">
                                        {freelancerWorklogs.map((worklog: any) => (
                                            <div
                                                key={worklog.id}
                                                className="flex items-center justify-between p-3 rounded-md bg-muted/30"
                                            >
                                                <div className="flex-1">
                                                    <div className="font-medium text-sm">{worklog.task_name}</div>
                                                    <div className="text-xs text-muted-foreground mt-0.5">
                                                        {worklog.total_hours.toFixed(2)} hrs @ ${worklog.hourly_rate.toFixed(2)}/hr
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <div className="font-semibold text-sm">
                                                        ${worklog.total_earned.toFixed(2)}
                                                    </div>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => excludeMutation.mutate(worklog.id)}
                                                        disabled={excludeMutation.isPending}
                                                    >
                                                        Exclude
                                                    </Button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )
                        })
                    })()}

                    {excludedIds.size > 0 && (
                        <div className="p-6 bg-muted/30">
                            <div className="text-sm font-medium text-muted-foreground">
                                {excludedIds.size} worklog{excludedIds.size !== 1 ? "s" : ""} excluded from this batch
                            </div>
                        </div>
                    )}

                    {selectedWorklogs.length === 0 && excludedIds.size > 0 && (
                        <div className="p-6 text-center text-muted-foreground">
                            All worklogs have been excluded. Go back to select different worklogs.
                        </div>
                    )}
                </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between">
                <Button variant="outline" onClick={() => navigate({ to: "/worklogs" })}>
                    Cancel
                </Button>
                <Button
                    onClick={handleConfirmPayment}
                    disabled={processPaymentMutation.isPending || selectedWorklogs.length === 0}
                >
                    {processPaymentMutation.isPending ? "Processing..." : "Confirm Payment"}
                </Button>
            </div>
        </div>
    )
}

function PaymentReviewTable() {
    return (
        <Suspense fallback={<PendingItems />}>
            <PaymentReviewContent />
        </Suspense>
    )
}

function PaymentReview() {
    return <PaymentReviewTable />
}
