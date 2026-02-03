import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  Edit2,
  Plus,
  Save,
  Trash2,
  XCircle,
} from "lucide-react"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  FreelancerPortalService,
  type TimeEntryPublic,
  type WorkLogStatus,
} from "@/client/freelancerPortalService"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import useCustomToast from "@/hooks/useCustomToast"

// Status badge config
const statusConfig: Record<
  WorkLogStatus,
  {
    label: string
    variant: "default" | "secondary" | "destructive" | "outline"
    icon: React.ElementType
  }
> = {
  pending: { label: "Pending", variant: "secondary", icon: Clock },
  approved: { label: "Approved", variant: "default", icon: CheckCircle2 },
  paid: { label: "Paid", variant: "outline", icon: DollarSign },
  rejected: { label: "Rejected", variant: "destructive", icon: XCircle },
}

// Formatters
function formatCurrency(amount: string | number) {
  const num = typeof amount === "string" ? Number.parseFloat(amount) : amount
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num)
}

function formatDuration(minutes: number) {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours === 0) return `${mins}m`
  if (mins === 0) return `${hours}h`
  return `${hours}h ${mins}m`
}

function formatDateTime(dateString: string) {
  return new Date(dateString).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

function formatDateTimeLocal(isoString: string) {
  const date = new Date(isoString)
  return date.toISOString().slice(0, 16)
}

// Schemas
const taskDescriptionSchema = z.object({
  task_description: z.string().min(1, "Task description is required"),
})

const timeEntrySchema = z.object({
  start_time: z.string().min(1, "Start time is required"),
  end_time: z.string().min(1, "End time is required"),
  notes: z.string().optional(),
})

type TaskDescriptionForm = z.infer<typeof taskDescriptionSchema>
type TimeEntryForm = z.infer<typeof timeEntrySchema>

interface FreelancerWorkLogDetailSheetProps {
  worklogId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function FreelancerWorkLogDetailSheet({
  worklogId,
  open,
  onOpenChange,
}: FreelancerWorkLogDetailSheetProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const [editingTask, setEditingTask] = useState(false)
  const [editingEntryId, setEditingEntryId] = useState<string | null>(null)
  const [addingEntry, setAddingEntry] = useState(false)
  const [deleteEntryId, setDeleteEntryId] = useState<string | null>(null)

  // Query
  const { data: worklog, isLoading } = useQuery({
    queryKey: ["freelancer", "worklog", worklogId],
    queryFn: () => FreelancerPortalService.getWorklogDetail(worklogId!),
    enabled: !!worklogId && open,
  })

  const canEdit = worklog?.status === "pending"
  const config = worklog ? statusConfig[worklog.status as WorkLogStatus] : null
  const StatusIcon = config?.icon || Clock

  // Task description form
  const taskForm = useForm<TaskDescriptionForm>({
    resolver: zodResolver(taskDescriptionSchema),
    defaultValues: { task_description: "" },
  })

  // Time entry form
  const entryForm = useForm<TimeEntryForm>({
    resolver: zodResolver(timeEntrySchema),
    defaultValues: { start_time: "", end_time: "", notes: "" },
  })

  // Reset forms when worklog changes
  useEffect(() => {
    if (worklog) {
      taskForm.reset({ task_description: worklog.task_description })
    }
  }, [worklog?.id, worklog?.task_description])

  // Update task mutation
  const updateTaskMutation = useMutation({
    mutationFn: (data: TaskDescriptionForm) =>
      FreelancerPortalService.updateWorklog(worklogId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklog", worklogId] })
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklogs"] })
      showSuccessToast("Task description updated")
      setEditingTask(false)
    },
    onError: (error: any) => {
      showErrorToast(error?.body?.detail || "Failed to update task")
    },
  })

  // Add time entry mutation
  const addEntryMutation = useMutation({
    mutationFn: (data: TimeEntryForm) =>
      FreelancerPortalService.addTimeEntry(worklogId!, {
        start_time: new Date(data.start_time).toISOString(),
        end_time: new Date(data.end_time).toISOString(),
        notes: data.notes || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklog", worklogId] })
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklogs"] })
      queryClient.invalidateQueries({ queryKey: ["freelancer", "dashboard"] })
      showSuccessToast("Time entry added")
      entryForm.reset()
      setAddingEntry(false)
    },
    onError: (error: any) => {
      showErrorToast(error?.body?.detail || "Failed to add time entry")
    },
  })

  // Update time entry mutation
  const updateEntryMutation = useMutation({
    mutationFn: ({
      entryId,
      data,
    }: {
      entryId: string
      data: TimeEntryForm
    }) =>
      FreelancerPortalService.updateTimeEntry(entryId, {
        start_time: new Date(data.start_time).toISOString(),
        end_time: new Date(data.end_time).toISOString(),
        notes: data.notes || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklog", worklogId] })
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklogs"] })
      queryClient.invalidateQueries({ queryKey: ["freelancer", "dashboard"] })
      showSuccessToast("Time entry updated")
      setEditingEntryId(null)
    },
    onError: (error: any) => {
      showErrorToast(error?.body?.detail || "Failed to update time entry")
    },
  })

  // Delete time entry mutation
  const deleteEntryMutation = useMutation({
    mutationFn: (entryId: string) =>
      FreelancerPortalService.deleteTimeEntry(entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklog", worklogId] })
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklogs"] })
      queryClient.invalidateQueries({ queryKey: ["freelancer", "dashboard"] })
      showSuccessToast("Time entry deleted")
      setDeleteEntryId(null)
    },
    onError: (error: any) => {
      showErrorToast(error?.body?.detail || "Failed to delete time entry")
    },
  })

  const startEditingEntry = (entry: TimeEntryPublic) => {
    entryForm.reset({
      start_time: formatDateTimeLocal(entry.start_time),
      end_time: formatDateTimeLocal(entry.end_time),
      notes: entry.notes || "",
    })
    setEditingEntryId(entry.id)
  }

  const handleClose = () => {
    setEditingTask(false)
    setEditingEntryId(null)
    setAddingEntry(false)
    onOpenChange(false)
  }

  return (
    <>
      <Sheet open={open} onOpenChange={handleClose}>
        <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>WorkLog Details</SheetTitle>
            <SheetDescription>
              View and manage your worklog and time entries
            </SheetDescription>
          </SheetHeader>

          {isLoading ? (
            <div className="space-y-4 mt-6">
              <Skeleton className="h-24" />
              <Skeleton className="h-32" />
              <Skeleton className="h-32" />
            </div>
          ) : worklog ? (
            <div className="space-y-6 mt-6">
              {/* Status & Summary */}
              <div className="flex items-center justify-between">
                <Badge variant={config?.variant} className="gap-1">
                  <StatusIcon className="h-3 w-3" />
                  {config?.label}
                </Badge>
                <div className="text-right">
                  <div className="text-2xl font-bold">
                    {formatCurrency(worklog.total_amount)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDuration(worklog.total_duration_minutes)} logged
                  </div>
                </div>
              </div>

              <Separator />

              {/* Task Description */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Task Description</h3>
                  {canEdit && !editingTask && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="gap-1"
                      onClick={() => setEditingTask(true)}
                    >
                      <Edit2 className="h-3 w-3" />
                      Edit
                    </Button>
                  )}
                </div>

                {editingTask ? (
                  <Form {...taskForm}>
                    <form
                      onSubmit={taskForm.handleSubmit((data) =>
                        updateTaskMutation.mutate(data)
                      )}
                      className="space-y-2"
                    >
                      <FormField
                        control={taskForm.control}
                        name="task_description"
                        render={({ field }) => (
                          <FormItem>
                            <FormControl>
                              <Textarea className="min-h-[80px]" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <div className="flex gap-2">
                        <Button
                          type="submit"
                          size="sm"
                          disabled={updateTaskMutation.isPending}
                        >
                          <Save className="h-3 w-3 mr-1" />
                          Save
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            taskForm.reset({
                              task_description: worklog.task_description,
                            })
                            setEditingTask(false)
                          }}
                        >
                          Cancel
                        </Button>
                      </div>
                    </form>
                  </Form>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    {worklog.task_description}
                  </p>
                )}
              </div>

              <Separator />

              {/* Time Entries */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">
                    Time Entries ({worklog.time_entries.length})
                  </h3>
                  {canEdit && !addingEntry && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1"
                      onClick={() => {
                        entryForm.reset({
                          start_time: "",
                          end_time: "",
                          notes: "",
                        })
                        setAddingEntry(true)
                      }}
                    >
                      <Plus className="h-3 w-3" />
                      Add Entry
                    </Button>
                  )}
                </div>

                {/* Add Entry Form */}
                {addingEntry && (
                  <Form {...entryForm}>
                    <form
                      onSubmit={entryForm.handleSubmit((data) =>
                        addEntryMutation.mutate(data)
                      )}
                      className="p-4 border rounded-lg space-y-4 bg-muted/50"
                    >
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <Plus className="h-4 w-4" />
                        New Time Entry
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <FormField
                          control={entryForm.control}
                          name="start_time"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Start Time</FormLabel>
                              <FormControl>
                                <Input type="datetime-local" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                        <FormField
                          control={entryForm.control}
                          name="end_time"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>End Time</FormLabel>
                              <FormControl>
                                <Input type="datetime-local" {...field} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                      <FormField
                        control={entryForm.control}
                        name="notes"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Notes (Optional)</FormLabel>
                            <FormControl>
                              <Input placeholder="Brief notes..." {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <div className="flex gap-2">
                        <Button
                          type="submit"
                          size="sm"
                          disabled={addEntryMutation.isPending}
                        >
                          <Save className="h-3 w-3 mr-1" />
                          Add
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setAddingEntry(false)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </form>
                  </Form>
                )}

                {/* Existing Entries */}
                <div className="space-y-3">
                  {worklog.time_entries.map((entry: TimeEntryPublic) => (
                    <div
                      key={entry.id}
                      className="p-4 border rounded-lg space-y-2"
                    >
                      {editingEntryId === entry.id ? (
                        <Form {...entryForm}>
                          <form
                            onSubmit={entryForm.handleSubmit((data) =>
                              updateEntryMutation.mutate({
                                entryId: entry.id,
                                data,
                              })
                            )}
                            className="space-y-4"
                          >
                            <div className="grid grid-cols-2 gap-4">
                              <FormField
                                control={entryForm.control}
                                name="start_time"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>Start Time</FormLabel>
                                    <FormControl>
                                      <Input type="datetime-local" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                              <FormField
                                control={entryForm.control}
                                name="end_time"
                                render={({ field }) => (
                                  <FormItem>
                                    <FormLabel>End Time</FormLabel>
                                    <FormControl>
                                      <Input type="datetime-local" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                  </FormItem>
                                )}
                              />
                            </div>
                            <FormField
                              control={entryForm.control}
                              name="notes"
                              render={({ field }) => (
                                <FormItem>
                                  <FormLabel>Notes (Optional)</FormLabel>
                                  <FormControl>
                                    <Input
                                      placeholder="Brief notes..."
                                      {...field}
                                    />
                                  </FormControl>
                                  <FormMessage />
                                </FormItem>
                              )}
                            />
                            <div className="flex gap-2">
                              <Button
                                type="submit"
                                size="sm"
                                disabled={updateEntryMutation.isPending}
                              >
                                <Save className="h-3 w-3 mr-1" />
                                Save
                              </Button>
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() => setEditingEntryId(null)}
                              >
                                Cancel
                              </Button>
                            </div>
                          </form>
                        </Form>
                      ) : (
                        <>
                          <div className="flex items-start justify-between">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2 text-sm">
                                <Calendar className="h-3 w-3 text-muted-foreground" />
                                <span>{formatDateTime(entry.start_time)}</span>
                                <span className="text-muted-foreground">→</span>
                                <span>{formatDateTime(entry.end_time)}</span>
                              </div>
                              <div className="flex items-center gap-2 text-sm font-medium">
                                <Clock className="h-3 w-3 text-muted-foreground" />
                                {formatDuration(entry.duration_minutes)}
                              </div>
                              {entry.notes && (
                                <p className="text-sm text-muted-foreground">
                                  {entry.notes}
                                </p>
                              )}
                            </div>
                            {canEdit && (
                              <div className="flex gap-1">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  onClick={() => startEditingEntry(entry)}
                                >
                                  <Edit2 className="h-3 w-3" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8 text-destructive hover:text-destructive"
                                  onClick={() => setDeleteEntryId(entry.id)}
                                >
                                  <Trash2 className="h-3 w-3" />
                                </Button>
                              </div>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Meta Info */}
              <div className="text-xs text-muted-foreground space-y-1">
                <p>
                  Hourly Rate:{" "}
                  {formatCurrency(worklog.freelancer.hourly_rate)}/hr
                </p>
                <p>Created: {formatDateTime(worklog.created_at)}</p>
                <p>Last Updated: {formatDateTime(worklog.updated_at)}</p>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-32 text-muted-foreground">
              WorkLog not found
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* Delete Entry Confirmation */}
      <AlertDialog
        open={!!deleteEntryId}
        onOpenChange={(open) => !open && setDeleteEntryId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Time Entry?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete this time entry. This action cannot
              be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() =>
                deleteEntryId && deleteEntryMutation.mutate(deleteEntryId)
              }
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
