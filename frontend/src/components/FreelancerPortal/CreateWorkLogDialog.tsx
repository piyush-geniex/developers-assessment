import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, Trash2, Clock } from "lucide-react"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"

import {
  FreelancerPortalService,
  type FreelancerWorkLogCreate,
} from "@/client/freelancerPortalService"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import useCustomToast from "@/hooks/useCustomToast"

// Validation schema
const timeEntrySchema = z.object({
  start_time: z.string().min(1, "Start time is required"),
  end_time: z.string().min(1, "End time is required"),
  notes: z.string().optional(),
})

const workLogSchema = z.object({
  task_description: z.string().min(1, "Task description is required"),
  time_entries: z
    .array(timeEntrySchema)
    .min(1, "At least one time entry is required"),
})

type WorkLogFormValues = z.infer<typeof workLogSchema>

interface CreateWorkLogDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function CreateWorkLogDialog({
  open,
  onOpenChange,
}: CreateWorkLogDialogProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<WorkLogFormValues>({
    resolver: zodResolver(workLogSchema),
    defaultValues: {
      task_description: "",
      time_entries: [
        {
          start_time: "",
          end_time: "",
          notes: "",
        },
      ],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "time_entries",
  })

  const mutation = useMutation({
    mutationFn: (data: FreelancerWorkLogCreate) =>
      FreelancerPortalService.createWorklog(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["freelancer", "worklogs"] })
      queryClient.invalidateQueries({ queryKey: ["freelancer", "dashboard"] })
      showSuccessToast("WorkLog created successfully")
      form.reset()
      onOpenChange(false)
    },
    onError: (error: any) => {
      showErrorToast(error?.body?.detail || "Failed to create worklog")
    },
  })

  const onSubmit = (data: WorkLogFormValues) => {
    // Convert datetime-local to ISO format
    const formattedData: FreelancerWorkLogCreate = {
      task_description: data.task_description,
      time_entries: data.time_entries.map((entry) => ({
        start_time: new Date(entry.start_time).toISOString(),
        end_time: new Date(entry.end_time).toISOString(),
        notes: entry.notes || null,
      })),
    }
    mutation.mutate(formattedData)
  }

  const handleClose = () => {
    form.reset()
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New WorkLog</DialogTitle>
          <DialogDescription>
            Log your work hours by adding time entries for your tasks.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Task Description */}
            <FormField
              control={form.control}
              name="task_description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Task Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Describe the work you completed..."
                      className="min-h-[80px]"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Time Entries */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <FormLabel className="text-base">Time Entries</FormLabel>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="gap-1"
                  onClick={() =>
                    append({
                      start_time: "",
                      end_time: "",
                      notes: "",
                    })
                  }
                >
                  <Plus className="h-4 w-4" />
                  Add Entry
                </Button>
              </div>

              {fields.map((field, index) => (
                <div
                  key={field.id}
                  className="p-4 border rounded-lg space-y-4 relative"
                >
                  <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    Entry {index + 1}
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name={`time_entries.${index}.start_time`}
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
                      control={form.control}
                      name={`time_entries.${index}.end_time`}
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
                    control={form.control}
                    name={`time_entries.${index}.notes`}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Notes (Optional)</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="Brief notes about this time entry..."
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {fields.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute top-2 right-2 h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => remove(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}

              {form.formState.errors.time_entries?.message && (
                <p className="text-sm text-destructive">
                  {form.formState.errors.time_entries.message}
                </p>
              )}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? "Creating..." : "Create WorkLog"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
