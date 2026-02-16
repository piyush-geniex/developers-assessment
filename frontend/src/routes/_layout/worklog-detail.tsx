import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { ArrowLeft, Clock } from "lucide-react"
import { Suspense } from "react"

import { WorklogsService } from "@/components/Worklogs/service"
import PendingItems from "@/components/Pending/PendingItems"
import { Button } from "@/components/ui/button"

function getWorklogDetailQueryOptions(id: number) {
    return {
        queryFn: () => WorklogsService.readWorklog(id),
        queryKey: ["worklog", id],
    }
}

export const Route = createFileRoute("/_layout/worklog-detail")({
    component: WorklogDetail,
    head: () => ({
        meta: [
            {
                title: "Worklog Details - FastAPI Cloud",
            },
        ],
    }),
})

function WorklogDetailContent() {
    const searchParams = Route.useSearch() as { id: string }
    const worklogId = parseInt(searchParams.id)
    const { data: worklog } = useSuspenseQuery(getWorklogDetailQueryOptions(worklogId))

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => window.history.back()}
                >
                    <ArrowLeft className="h-4 w-4" />
                </Button>
                <div className="flex-1">
                    <h1 className="text-2xl font-bold tracking-tight">{worklog.task_name}</h1>
                    <p className="text-muted-foreground">Freelancer ID: {worklog.freelancer_id}</p>
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-lg border bg-card p-4">
                    <div className="text-sm font-medium text-muted-foreground">Total Hours</div>
                    <div className="text-2xl font-bold">{worklog.total_hours.toFixed(2)}</div>
                </div>
                <div className="rounded-lg border bg-card p-4">
                    <div className="text-sm font-medium text-muted-foreground">Hourly Rate</div>
                    <div className="text-2xl font-bold">${worklog.hourly_rate.toFixed(2)}</div>
                </div>
                <div className="rounded-lg border bg-card p-4">
                    <div className="text-sm font-medium text-muted-foreground">Total Earned</div>
                    <div className="text-2xl font-bold">${worklog.total_earned.toFixed(2)}</div>
                </div>
            </div>

            {/* Time Entries */}
            <div className="rounded-lg border">
                <div className="border-b bg-muted/50 px-6 py-4">
                    <h2 className="text-lg font-semibold">Time Entries</h2>
                </div>
                <div className="p-6">
                    {worklog.time_entries && worklog.time_entries.length > 0 ? (
                        <div className="space-y-4">
                            {worklog.time_entries.map((entry: any, index: number) => (
                                <div
                                    key={index}
                                    className="flex items-start gap-4 rounded-lg border p-4"
                                >
                                    <div className="rounded-full bg-muted p-2">
                                        <Clock className="h-4 w-4" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between">
                                            <div className="font-medium">{entry.date}</div>
                                            <div className="font-semibold">{entry.hours} hrs</div>
                                        </div>
                                        {entry.description && (
                                            <p className="mt-1 text-sm text-muted-foreground">
                                                {entry.description}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-muted-foreground">
                            No time entries recorded
                        </div>
                    )}
                </div>
            </div>

            {/* Status Badge */}
            <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Status:</span>
                <span
                    className={`px-3 py-1 rounded-full text-sm ${worklog.status === "PAID"
                        ? "bg-green-100 text-green-800"
                        : worklog.status === "EXCLUDED"
                            ? "bg-gray-100 text-gray-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                >
                    {worklog.status}
                </span>
            </div>
        </div>
    )
}

function WorklogDetailTable() {
    return (
        <Suspense fallback={<PendingItems />}>
            <WorklogDetailContent />
        </Suspense>
    )
}

function WorklogDetail() {
    return <WorklogDetailTable />
}
