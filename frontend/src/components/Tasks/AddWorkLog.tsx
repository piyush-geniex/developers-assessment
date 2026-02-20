import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Clock } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"

import { type WorkLogEntryCreate, WorkLogsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface FormData {
  title: string
  description?: string
  start_time: string
  end_time: string
  amount: string
}

interface AddWorkLogProps {
  taskId: string
  onSuccess: () => void
}

// Helper function to get timezone offset
const getTimezoneOffset = (): string => {
  const now = new Date()
  const offset = now.getTimezoneOffset()
  const hours = Math.floor(Math.abs(offset) / 60)
  const minutes = Math.abs(offset) % 60
  const sign = offset <= 0 ? "+" : "-"
  return `${sign}${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`
}

// Helper function to format local datetime string with timezone offset
// Takes a datetime-local string (e.g., "2025-02-11T09:02") and adds timezone offset
// Returns ISO format with timezone (e.g., "2025-02-11T09:02:00+03:00")
const formatDateWithTimezone = (dateString: string): string => {
  // dateString is already in local time from datetime-local input
  const timezoneOffset = getTimezoneOffset()
  // Add seconds and timezone offset
  return `${dateString}:00${timezoneOffset}`
}

// Helper to get browser timezone name
const getBrowserTimezone = (): string => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone
  } catch {
    return "Unknown"
  }
}

// Helper to convert date to local timezone datetime-local format
const toLocalDatetimeString = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  const hours = String(date.getHours()).padStart(2, "0")
  const minutes = String(date.getMinutes()).padStart(2, "0")
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const AddWorkLog = ({ taskId, onSuccess }: AddWorkLogProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<FormData>({
    mode: "onBlur",
    defaultValues: {
      title: "",
      description: "",
      start_time: toLocalDatetimeString(new Date()),
      end_time: toLocalDatetimeString(new Date(Date.now() + 3600000)),
      amount: "0",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: WorkLogEntryCreate) =>
      WorkLogsService.tasksCreateWorkLog({ taskId, requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Work log entry created successfully")
      form.reset()
      setIsOpen(false)
      onSuccess()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["worklogs", taskId] })
      queryClient.invalidateQueries({ queryKey: ["tasks"] })
    },
  })

  const onSubmit = (data: FormData) => {
    const amount = parseFloat(data.amount)
    if (isNaN(amount) || amount <= 0) {
      showErrorToast("Amount must be a valid number greater than 0")
      return
    }

    const workLogData: WorkLogEntryCreate = {
      task_id: taskId,
      title: data.title,
      description: data.description,
      start_time: formatDateWithTimezone(data.start_time),
      end_time: formatDateWithTimezone(data.end_time),
      amount,
    }
    mutation.mutate(workLogData)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        onSelect={(e) => e.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        <Clock />
        Add Worklog Entry
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>Add Worklog Entry</DialogTitle>
              <DialogDescription>
                Create a new work log entry for this task.
              </DialogDescription>
            </DialogHeader>
            <div className="mb-4 p-3 bg-blue-50 rounded-md border border-blue-200">
              <p className="text-sm text-blue-900">
                ℹ️ Using your browser timezone: <strong>{getBrowserTimezone()}</strong>
              </p>
            </div>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Title <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="text"
                        placeholder="Work log entry title"
                        {...field}
                        required
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Input
                        type="text"
                        placeholder="Description (optional)"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="start_time"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Start Date & Time{" "}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="datetime-local"
                        {...field}
                        required
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="end_time"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      End Date & Time <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="datetime-local"
                        {...field}
                        required
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="amount"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Amount <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        {...field}
                        required
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Cancel
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                Save
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default AddWorkLog
