import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Plus, X } from "lucide-react"
import { useState } from "react"
import { useFieldArray, useForm } from "react-hook-form"
import { z } from "zod"

import { WorklogsService } from "@/components/Worklogs/service"
import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
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
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const timeEntrySchema = z.object({
    date: z.string().min(1, { message: "Date is required" }),
    hours: z.coerce.number().positive({ message: "Hours must be positive" }),
    description: z.string().min(1, { message: "Description is required" }),
})

const formSchema = z.object({
    task_name: z.string().min(1, { message: "Task name is required" }),
    freelancer_id: z.coerce.number().int().positive({ message: "Freelancer ID must be a positive integer" }),
    hourly_rate: z.coerce.number().positive({ message: "Hourly rate must be positive" }),
    time_entries: z.array(timeEntrySchema).min(1, { message: "At least one time entry is required" }),
})

type FormData = z.infer<typeof formSchema>

const AddWorklog = () => {
    const [isOpen, setIsOpen] = useState(false)
    const queryClient = useQueryClient()
    const { showSuccessToast, showErrorToast } = useCustomToast()

    const form = useForm<FormData>({
        resolver: zodResolver(formSchema),
        mode: "onBlur",
        criteriaMode: "all",
        defaultValues: {
            task_name: "",
            freelancer_id: undefined,
            hourly_rate: undefined,
            time_entries: [
                {
                    date: new Date().toISOString().split("T")[0],
                    hours: undefined,
                    description: "",
                },
            ],
        },
    })

    const { fields, append, remove } = useFieldArray({
        control: form.control,
        name: "time_entries",
    })

    const mutation = useMutation({
        mutationFn: (data: FormData) => WorklogsService.createWorklog(data),
        onSuccess: () => {
            showSuccessToast("Worklog created successfully")
            form.reset()
            setIsOpen(false)
        },
        onError: (error) => handleError(showErrorToast, error),
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["worklogs"] })
        },
    })

    const onSubmit = (data: FormData) => {
        mutation.mutate(data)
    }

    const addTimeEntry = () => {
        append({
            date: new Date().toISOString().split("T")[0],
            hours: undefined,
            description: "",
        })
    }

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button>
                    <Plus className="mr-2" />
                    Create Worklog
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Create Worklog</DialogTitle>
                    <DialogDescription>
                        Add a new worklog with time entries for a freelancer.
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)}>
                        <div className="grid gap-4 py-4">
                            <FormField
                                control={form.control}
                                name="task_name"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>
                                            Task Name <span className="text-destructive">*</span>
                                        </FormLabel>
                                        <FormControl>
                                            <Input
                                                placeholder="e.g., Build authentication module"
                                                type="text"
                                                {...field}
                                                required
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <div className="grid grid-cols-2 gap-4">
                                <FormField
                                    control={form.control}
                                    name="freelancer_id"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>
                                                Freelancer ID <span className="text-destructive">*</span>
                                            </FormLabel>
                                            <FormControl>
                                                <Input
                                                    placeholder="e.g., 1"
                                                    type="number"
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
                                    name="hourly_rate"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>
                                                Hourly Rate ($) <span className="text-destructive">*</span>
                                            </FormLabel>
                                            <FormControl>
                                                <Input
                                                    placeholder="e.g., 50"
                                                    type="number"
                                                    step="0.01"
                                                    {...field}
                                                    required
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>

                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <FormLabel>
                                        Time Entries <span className="text-destructive">*</span>
                                    </FormLabel>
                                    <Button
                                        type="button"
                                        variant="outline"
                                        size="sm"
                                        onClick={addTimeEntry}
                                    >
                                        <Plus className="h-4 w-4 mr-1" />
                                        Add Entry
                                    </Button>
                                </div>

                                {fields.map((field, index) => (
                                    <div
                                        key={field.id}
                                        className="border rounded-lg p-4 space-y-3 relative"
                                    >
                                        {fields.length > 1 && (
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                size="icon"
                                                className="absolute top-2 right-2 h-6 w-6"
                                                onClick={() => remove(index)}
                                            >
                                                <X className="h-4 w-4" />
                                            </Button>
                                        )}

                                        <div className="grid grid-cols-2 gap-3">
                                            <FormField
                                                control={form.control}
                                                name={`time_entries.${index}.date`}
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Date</FormLabel>
                                                        <FormControl>
                                                            <Input type="date" {...field} required />
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />

                                            <FormField
                                                control={form.control}
                                                name={`time_entries.${index}.hours`}
                                                render={({ field }) => (
                                                    <FormItem>
                                                        <FormLabel>Hours</FormLabel>
                                                        <FormControl>
                                                            <Input
                                                                type="number"
                                                                step="0.5"
                                                                placeholder="e.g., 8"
                                                                {...field}
                                                                required
                                                            />
                                                        </FormControl>
                                                        <FormMessage />
                                                    </FormItem>
                                                )}
                                            />
                                        </div>

                                        <FormField
                                            control={form.control}
                                            name={`time_entries.${index}.description`}
                                            render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>Description</FormLabel>
                                                    <FormControl>
                                                        <Input
                                                            placeholder="What was worked on..."
                                                            {...field}
                                                            required
                                                        />
                                                    </FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )}
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>

                        <DialogFooter>
                            <DialogClose asChild>
                                <Button variant="outline" disabled={mutation.isPending}>
                                    Cancel
                                </Button>
                            </DialogClose>
                            <LoadingButton type="submit" loading={mutation.isPending}>
                                Create Worklog
                            </LoadingButton>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    )
}

export default AddWorklog
