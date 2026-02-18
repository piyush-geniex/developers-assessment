import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useParams } from "@tanstack/react-router"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { MOCK_WORKLOG_DETAIL } from "@/lib/worklog-mock"

const WorklogDetailSkeleton = () => (
    <div className="flex flex-col gap-6">
      <Skeleton className="h-8 w-32" />
      <div>
        <Skeleton className="h-8 w-64 mb-2" />
        <Skeleton className="h-4 w-48 mb-1" />
        <Skeleton className="h-4 w-40" />
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Hours</TableHead>
              <TableHead className="text-right">Rate</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead>Logged (UTC)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 3 }).map((_, i) => (
              <TableRow key={i}>
                <TableCell><Skeleton className="h-4 w-40" /></TableCell>
                <TableCell><Skeleton className="h-4 w-12 ml-auto" /></TableCell>
                <TableCell><Skeleton className="h-4 w-16 ml-auto" /></TableCell>
                <TableCell><Skeleton className="h-4 w-16 ml-auto" /></TableCell>
                <TableCell><Skeleton className="h-4 w-36" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
)

const WorklogDetailPage = () => {
  const { worklogId } = useParams({ from: "/_layout/worklogs/$worklogId" })
  const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

  const { data, isLoading, error } = useQuery({
    queryKey: ["worklog", worklogId],
    queryFn: async (): Promise<any> => {
      const url = `${API_BASE}/api/v1/worklogs/${worklogId}`
      try {
        const token = localStorage.getItem("access_token")
        const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
        if (res.ok) return await res.json()
        throw new Error(String(res.status))
      } catch {
        return MOCK_WORKLOG_DETAIL[worklogId] ?? null
      }
    },
  })

  if (isLoading) {
    return <WorklogDetailSkeleton />
  }

  if (error || !data) {
    return (
      <div className="flex flex-col gap-6">
        <p className="text-destructive">Failed to load worklog. Please try again.</p>
        <Button variant="outline" asChild>
          <Link to="/worklogs">Back to worklogs</Link>
        </Button>
      </div>
    )
  }

  const worklog = data as any
  const entries: any[] = worklog.time_entries ?? []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/worklogs">← Back to worklogs</Link>
        </Button>
      </div>
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Worklog: {worklog.task_name}</h1>
        <p className="text-muted-foreground">
          {worklog.freelancer_name} · Total earned: ${Number(worklog.amount_earned).toFixed(2)}
        </p>
        <p className="text-sm text-muted-foreground mt-1">Created: {worklog.created_at}</p>
      </div>
      <div className="rounded-md border">
        <h2 className="sr-only">Time entries</h2>
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Hours</TableHead>
              <TableHead className="text-right">Rate</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead>Logged (UTC)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground">
                  No time entries
                </TableCell>
              </TableRow>
            ) : (
              entries.map((entry: any) => (
                <TableRow key={entry.id}>
                  <TableCell>{entry.description ?? "—"}</TableCell>
                  <TableCell className="text-right">{entry.hours}</TableCell>
                  <TableCell className="text-right">${Number(entry.rate).toFixed(2)}</TableCell>
                  <TableCell className="text-right font-medium">${Number(entry.amount).toFixed(2)}</TableCell>
                  <TableCell>{entry.logged_at}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
};

export const Route = createFileRoute("/_layout/worklogs/$worklogId")({
  component: WorklogDetailPage,
  head: () => ({ meta: [{ title: "Worklog detail - Payment Dashboard" }] }),
});
