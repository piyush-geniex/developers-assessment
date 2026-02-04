
import { createFileRoute, Link } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft } from "lucide-react"

import { WorkLogService } from "@/client/WorkLogService"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"

export const Route = createFileRoute("/_layout/worklogs/$workLogId")({
    component: WorkLogDetail,
})

function WorkLogDetail() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { workLogId } = Route.useParams() as any

    const { data: worklog, isLoading, error } = useQuery({
        queryKey: ["worklog", workLogId],
        queryFn: () => WorkLogService.readWorkLog(workLogId),
    })

    if (isLoading) return <div>Loading...</div>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (error) return <div>Error loading worklog: {(error as any).message || "Unknown error"}</div>
    if (!worklog) return <div>Worklog not found</div>

    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center gap-4">
                <Button variant="outline" size="icon" asChild>
                    <Link to="/worklogs">
                        <ArrowLeft className="h-4 w-4" />
                    </Link>
                </Button>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">{worklog.task_name}</h1>
                    <p className="text-muted-foreground">
                        ID: {worklog.id} | Status: <span className="capitalize font-medium">{worklog.status}</span>
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-4 border rounded-md">
                    <h3 className="font-semibold text-sm text-muted-foreground uppercase">Total Hours</h3>
                    <p className="text-2xl font-bold">{worklog.total_duration_hours}</p>
                </div>
                <div className="p-4 border rounded-md">
                    <h3 className="font-semibold text-sm text-muted-foreground uppercase">Total Amount</h3>
                    <p className="text-2xl font-bold">${worklog.total_amount}</p>
                </div>
                <div className="p-4 border rounded-md">
                    <h3 className="font-semibold text-sm text-muted-foreground uppercase">Freelancer ID</h3>
                    <p className="text-sm truncate" title={worklog.freelancer_id}>{worklog.freelancer_id}</p>
                </div>
            </div>

            <div>
                <h2 className="text-lg font-semibold mb-4">Time Entries</h2>
                <div className="rounded-md border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Description</TableHead>
                                <TableHead>Start Time</TableHead>
                                <TableHead>End Time</TableHead>
                                <TableHead>Rate ($/hr)</TableHead>
                                <TableHead>Duration (hrs)</TableHead>
                                <TableHead>Amount ($)</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {worklog.time_entries?.map((entry) => {
                                const start = new Date(entry.start_time)
                                const end = new Date(entry.end_time)
                                const duration = (end.getTime() - start.getTime()) / (1000 * 60 * 60)
                                const amount = duration * entry.rate

                                return (
                                    <TableRow key={entry.id}>
                                        <TableCell>{entry.description}</TableCell>
                                        <TableCell>{start.toLocaleString()}</TableCell>
                                        <TableCell>{end.toLocaleString()}</TableCell>
                                        <TableCell>{entry.rate}</TableCell>
                                        <TableCell>{duration.toFixed(2)}</TableCell>
                                        <TableCell>{amount.toFixed(2)}</TableCell>
                                    </TableRow>
                                )
                            })}
                            {!worklog.time_entries?.length && (
                                <TableRow>
                                    <TableCell colSpan={6} className="text-center h-24">No time entries found</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </div>
            </div>
        </div>
    )
}
