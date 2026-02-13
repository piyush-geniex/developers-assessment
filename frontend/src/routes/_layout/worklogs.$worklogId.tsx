import { createFileRoute, Link } from "@tanstack/react-router"
import { useEffect, useMemo, useState } from "react"
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
import { Skeleton } from "@/components/ui/skeleton"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

export const Route = createFileRoute("/_layout/worklogs/$worklogId")({
  component: WorklogDetailPage,
  head: () => ({
    meta: [{ title: "Worklog Detail - WorkLog Dashboard" }],
  }),
})

function fmtDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "numeric", minute: "2-digit",
  })
}

function WorklogDetailPage() {
  const { worklogId } = Route.useParams()
  const [data, setData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setIsLoading(true)
    setError(null)

    const ax = axios.create()
    ax.defaults.baseURL = "http://localhost:8000"

    ax.get(`/api/v1/worklogs/${worklogId}`)
      .then((res: any) => {
        setData(res.data)
        setIsLoading(false)
      })
      .catch((err: any) => {
        setError("Failed to load worklog details. Please try again.")
        console.error(err)
        setIsLoading(false)
      })
  }, [worklogId])

  // Group time entries by date for the work diary (must be before early returns)
  const diary = useMemo(() => {
    if (!data?.time_entries?.length) return null

    const byDate: Record<string, number> = {}
    for (const te of data.time_entries) {
      const key = te.start_time.slice(0, 10)
      byDate[key] = (byDate[key] || 0) + (te.hours || 0)
    }

    const dates = Object.keys(byDate).sort()
    const first = new Date(dates[0])
    const dayOfWeek = first.getUTCDay()
    const mon = new Date(first)
    mon.setUTCDate(mon.getUTCDate() - ((dayOfWeek + 6) % 7))
    const sun = new Date(mon)
    sun.setUTCDate(sun.getUTCDate() + 6)

    const dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    const days: { date: Date; label: string; hours: number }[] = []
    for (let i = 0; i < 7; i++) {
      const d = new Date(mon)
      d.setUTCDate(d.getUTCDate() + i)
      const key = d.toISOString().slice(0, 10)
      days.push({
        date: d,
        label: `${d.getUTCDate()} ${dayNames[i]}`,
        hours: byDate[key] || 0,
      })
    }

    const maxH = Math.max(...days.map((d) => d.hours), 8)
    const totalWeek = days.reduce((s, d) => s + d.hours, 0)

    const fmtRange = (d: Date) =>
      d.toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" })

    return { days, maxH, totalWeek, rangeLabel: `${fmtRange(mon)} - ${fmtRange(sun)}` }
  }, [data])

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-destructive text-center py-8">{error}</div>
    )
  }

  if (!data) return null

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <Link to="/worklogs">
          <Button variant="outline" size="sm" aria-label="Back to worklogs">
            Back
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {data.task_name}
          </h1>
          <p className="text-muted-foreground">{data.description}</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Freelancer</CardDescription>
            <CardTitle className="text-lg">{data.freelancer_name || "Unknown"}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {data.freelancer_email}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Hours</CardDescription>
            <CardTitle className="text-lg">
              {data.total_hours.toFixed(1)}h
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Hourly Rate</CardDescription>
            <CardTitle className="text-lg">
              ${data.hourly_rate?.toFixed(2) || "0.00"}/hr
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Earned</CardDescription>
            <CardTitle className="text-lg">
              ${data.earned_amount.toFixed(2)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={data.status === "paid" ? "default" : "secondary"}>
              {data.status}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Work Diary - Weekly Timesheet */}
      {diary && (
        <div className="rounded-md border p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold">Work Diary</h2>
            <span className="text-sm text-muted-foreground">
              {diary.rangeLabel}
            </span>
          </div>
          <div className="flex flex-col gap-3">
            {diary.days.map((day) => {
              const pct = diary.maxH > 0 ? (day.hours / diary.maxH) * 100 : 0
              const hrs = Math.floor(day.hours)
              const mins = Math.round((day.hours - hrs) * 60)
              return (
                <div key={day.label} className="flex items-center gap-4">
                  <span
                    className={`text-sm w-28 shrink-0 ${day.hours > 0 ? "font-medium" : "text-muted-foreground"}`}
                  >
                    {day.label}
                  </span>
                  <div className="flex-1 h-6 rounded bg-muted relative">
                    {pct > 0 && (
                      <div
                        className="h-full rounded bg-emerald-500"
                        style={{ width: `${pct}%` }}
                      />
                    )}
                  </div>
                  <span
                    className={`text-sm w-16 text-right tabular-nums ${day.hours > 0 ? "font-medium" : "text-muted-foreground"}`}
                  >
                    {hrs}:{mins.toString().padStart(2, "0")} hrs
                  </span>
                </div>
              )
            })}
          </div>
          <div className="mt-4 pt-4 border-t flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Weekly total</span>
            <span className="font-semibold">
              {Math.floor(diary.totalWeek)}:{Math.round((diary.totalWeek - Math.floor(diary.totalWeek)) * 60).toString().padStart(2, "0")} hrs
            </span>
          </div>
        </div>
      )}

      <div>
        <h2 className="text-lg font-semibold mb-4">Time Entries</h2>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Start Time</TableHead>
                <TableHead>End Time</TableHead>
                <TableHead className="text-right">Hours</TableHead>
                <TableHead className="text-right">Amount ($)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.time_entries.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={4}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No time entries found
                  </TableCell>
                </TableRow>
              ) : (
                data.time_entries.map((te: any) => (
                  <TableRow key={te.id}>
                    <TableCell className="text-sm">
                      <span title={te.start_time} className="cursor-default">
                        {fmtDate(te.start_time)}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm">
                      <span title={te.end_time} className="cursor-default">
                        {fmtDate(te.end_time)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      {te.hours?.toFixed(1) || "0.0"}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      ${((te.hours || 0) * (data.hourly_rate || 0)).toFixed(2)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}
