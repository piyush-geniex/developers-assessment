import { useState } from "react"
import { DollarSign, Calendar, User } from "lucide-react"
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Clock } from "lucide-react"

interface Worklog {
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
}

interface WorklogListProps {
  worklogs: Worklog[]
  isLoading?: boolean
}

export function WorklogList({ worklogs, isLoading }: WorklogListProps) {
  const [selectedWorklog, setSelectedWorklog] = useState<any>(null)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const axiosInstance = axios.create({
    baseURL: "http://localhost:8000",
  })

  const handleViewDetails = async (worklogId: string) => {
    setIsDialogOpen(true)
    setIsDetailLoading(true)
    try {
      const token = localStorage.getItem("access_token")
      const response = await axiosInstance.get(
        `http://localhost:8000/api/v1/worklogs/${worklogId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      setSelectedWorklog(response.data)
    } catch (error: any) {
      console.error("Failed to fetch worklog details:", error)
      setSelectedWorklog(null)
    } finally {
      setIsDetailLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-muted-foreground">Loading worklogs...</div>
      </div>
    )
  }

  if (worklogs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <Calendar className="h-8 w-8 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold">No worklogs found</h3>
        <p className="text-muted-foreground">No worklogs match your criteria</p>
      </div>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Task</TableHead>
            <TableHead>Freelancer</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Earnings</TableHead>
            <TableHead>Date</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {worklogs.map((worklog) => (
            <TableRow key={worklog.id}>
              <TableCell className="font-medium">
                {worklog.task?.title || "Unknown Task"}
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span>
                    {worklog.freelancer?.full_name || worklog.freelancer?.email || "Unknown"}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <span
                  className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                    worklog.status === "PENDING"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-green-100 text-green-800"
                  }`}
                >
                  {worklog.status}
                </span>
              </TableCell>
              <TableCell className="text-right font-medium">
                <div className="flex items-center justify-end gap-1">
                  <DollarSign className="h-4 w-4" />
                  {worklog.total_earnings?.toFixed(2) || "0.00"}
                </div>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {worklog.created_at}
              </TableCell>
              <TableCell className="text-right">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleViewDetails(worklog.id)}
                >
                  View Details
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-[95vw] w-fit min-w-[600px] max-h-[90vh] overflow-y-auto sm:max-w-[95vw]">
          <DialogHeader>
            <DialogTitle>Worklog Details</DialogTitle>
            <DialogDescription>
              View time entries and earnings for this worklog
            </DialogDescription>
          </DialogHeader>
          {isDetailLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-muted-foreground">Loading worklog details...</div>
            </div>
          ) : selectedWorklog ? (
            <div className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Task Information</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div>
                        <span className="text-sm font-medium text-muted-foreground">Task:</span>
                        <p className="text-lg font-semibold">
                          {selectedWorklog.task?.title || "Unknown"}
                        </p>
                      </div>
                      {selectedWorklog.task?.description && (
                        <div>
                          <span className="text-sm font-medium text-muted-foreground">
                            Description:
                          </span>
                          <p className="text-sm">{selectedWorklog.task.description}</p>
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
                        <span className="text-sm font-medium text-muted-foreground">
                          Freelancer:
                        </span>
                        <p className="text-lg font-semibold">
                          {selectedWorklog.freelancer?.full_name ||
                            selectedWorklog.freelancer?.email ||
                            "Unknown"}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-muted-foreground">Status:</span>
                        <span
                          className={`ml-2 inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                            selectedWorklog.status === "PENDING"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-green-100 text-green-800"
                          }`}
                        >
                          {selectedWorklog.status}
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
                    <div className="flex items-center gap-2 text-lg font-semibold">
                      <DollarSign className="h-5 w-5" />
                      Total: {selectedWorklog.total_earnings?.toFixed(2) || "0.00"}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {selectedWorklog.time_entries?.length === 0 ? (
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
                        {selectedWorklog.time_entries?.map((entry: any) => (
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
                              $
                              {entry.earnings?.toFixed(2) ||
                                (entry.hours * entry.rate).toFixed(2)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="flex items-center justify-center py-12">
              <div className="text-muted-foreground">Failed to load worklog details</div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

