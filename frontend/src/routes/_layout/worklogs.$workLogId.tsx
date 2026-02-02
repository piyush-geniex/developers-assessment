import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft, Clock } from "lucide-react"
import { useEffect } from "react"

import {
  type TimeEntryPublic,
  type WorkLogDetail,
  WorklogsService,
} from "@/api/worklogs"
import { ApiError } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import PendingItems from "@/components/Pending/PendingItems"

function getWorklogQueryOptions(workLogId: string) {
  return {
    queryKey: ["worklog", workLogId],
    queryFn: () => WorklogsService.getWorklog(workLogId),
  }
}

function WorklogDetailContent({ workLogId }: { workLogId: string }) {
  const navigate = Route.useNavigate()
  const { data: worklog, isPending, isError, error } = useQuery(
    getWorklogQueryOptions(workLogId),
  )
  const entries =
    worklog != null
      ? (worklog as WorkLogDetail).time_entries ?? []
      : []

  // On 401/403, redirect to dashboard instead of showing error (user stays logged in)
  useEffect(() => {
    if (
      isError &&
      error instanceof ApiError &&
      (error.status === 401 || error.status === 403)
    ) {
      navigate({ to: "/" })
    }
  }, [isError, error, navigate])

  if (isPending) {
    return <PendingItems />
  }

  if (isError) {
    const isAuthError =
      error instanceof ApiError && (error.status === 401 || error.status === 403)
    if (isAuthError) {
      return <PendingItems />
    }
    const message =
      error instanceof ApiError && error.status === 404
        ? "Worklog not found."
        : error instanceof Error
          ? error.message
          : "Failed to load worklog."
    return (
      <div className="space-y-6">
        <Button variant="ghost" size="icon" asChild>
          <Link
            to="/worklogs"
            search={{ date_from: "", date_to: "", remittance_status: "" }}
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="sr-only">Back</span>
          </Link>
        </Button>
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="font-medium text-destructive">Error loading worklog</p>
          <p className="mt-2 text-sm text-muted-foreground">{message}</p>
        </div>
      </div>
    )
  }

  if (!worklog) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" asChild>
            <Link
              to="/worklogs"
              search={{ date_from: "", date_to: "", remittance_status: "" }}
            >
              <ArrowLeft className="h-4 w-4" />
              <span className="sr-only">Back</span>
            </Link>
          </Button>
          <h2 className="text-lg font-semibold">{worklog.task_title}</h2>
        </div>
        <p className="text-muted-foreground">
          Freelancer: {worklog.user_full_name || worklog.user_email}
        </p>
        <p className="text-sm font-medium">
          Total earned: ${((worklog.amount_cents ?? 0) / 100).toFixed(2)}
        </p>
        {worklog.remittance_id && (
          <p className="text-sm text-muted-foreground">Status: Paid</p>
        )}
      </div>

      <div>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-medium">
          <Clock className="h-4 w-4" />
          Time entries
        </h3>
        {entries.length === 0 ? (
          <p className="text-muted-foreground">No time entries</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Description</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((entry: TimeEntryPublic) => (
                <TableRow key={entry.id}>
                  <TableCell>{entry.entry_date}</TableCell>
                  <TableCell>{entry.duration_minutes} min</TableCell>
                  <TableCell>
                    ${(entry.amount_cents / 100).toFixed(2)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {entry.description || "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  )
}

export const Route = createFileRoute("/_layout/worklogs/$workLogId")({
  component: WorklogDetailPage,
  head: () => ({
    meta: [{ title: "WorkLog detail - Payment Dashboard" }],
  }),
})

function WorklogDetailPage() {
  const { workLogId } = Route.useParams()

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold tracking-tight">WorkLog detail</h1>
      <WorklogDetailContent workLogId={workLogId} />
    </div>
  )
}
