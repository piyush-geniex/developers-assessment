import { ArrowLeft, Clock, DollarSign } from "lucide-react"
import { Link } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"
import { AddTimeEntry } from "./AddTimeEntry"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

interface TimeEntry {
  id: string
  worklog_id: string
  hours: number
  rate: number
  description: string | null
  entry_date: string
  created_at: string
  earnings: number | null
}

interface WorklogDetail {
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
    description: string | null
    created_at: string
  } | null
  freelancer: {
    id: string
    email: string
    full_name: string | null
  } | null
  time_entries: TimeEntry[]
}

interface WorklogDetailProps {
  worklog: WorklogDetail
  isLoading?: boolean
}

export function WorklogDetail({ worklog, isLoading }: WorklogDetailProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-muted-foreground">Loading worklog details...</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link to="/worklogs">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Worklog Details</h1>
          <p className="text-muted-foreground">
            View time entries and earnings for this worklog
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Task Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <span className="text-sm font-medium text-muted-foreground">Task:</span>
                <p className="text-lg font-semibold">{worklog.task?.title || "Unknown"}</p>
              </div>
              {worklog.task?.description && (
                <div>
                  <span className="text-sm font-medium text-muted-foreground">Description:</span>
                  <p className="text-sm">{worklog.task.description}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Freelancer Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <span className="text-sm font-medium text-muted-foreground">Freelancer:</span>
                <p className="text-lg font-semibold">
                  {worklog.freelancer?.full_name || worklog.freelancer?.email || "Unknown"}
                </p>
              </div>
              <div>
                <span className="text-sm font-medium text-muted-foreground">Status:</span>
                <span
                  className={`ml-2 inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                    worklog.status === "PENDING"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-green-100 text-green-800"
                  }`}
                >
                  {worklog.status}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Time Entries</CardTitle>
              <CardDescription>
                Individual time entries recorded for this worklog
              </CardDescription>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-lg font-semibold">
                <DollarSign className="h-5 w-5" />
                Total: {worklog.total_earnings?.toFixed(2) || "0.00"}
              </div>
              <AddTimeEntry worklogId={worklog.id} onSuccess={() => window.location.reload()} />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {worklog.time_entries.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No time entries found for this worklog
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Hours</TableHead>
                  <TableHead>Rate</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Earnings</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {worklog.time_entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>{entry.entry_date}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        {entry.hours.toFixed(2)}
                      </div>
                    </TableCell>
                    <TableCell>
                      <DollarSign className="h-4 w-4 inline mr-1" />
                      {entry.rate.toFixed(2)}/hr
                    </TableCell>
                    <TableCell className="max-w-md truncate">
                      {entry.description || "No description"}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      ${entry.earnings?.toFixed(2) || (entry.hours * entry.rate).toFixed(2)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

