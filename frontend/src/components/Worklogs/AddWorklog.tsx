import { zodResolver } from "@hookform/resolvers/zod"
import { Plus } from "lucide-react"
import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import axios from "axios"

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"

const formSchema = z.object({
  freelancer_id: z.string().min(1, { message: "Freelancer is required" }),
  task_name: z.string().min(1, { message: "Task name is required" }),
  task_description: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

interface AddWorklogProps {
  onSuccess?: () => void
}

const AddWorklog = ({ onSuccess }: AddWorklogProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [freelancers, setFreelancers] = useState<any[]>([])
  const [loadingFreelancers, setLoadingFreelancers] = useState(false)

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      freelancer_id: "",
      task_name: "",
      task_description: "",
    },
  })

  useEffect(() => {
    if (isOpen) {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
      const token = localStorage.getItem("access_token")

      setLoadingFreelancers(true)
      axios
        .get(`${apiUrl}/api/v1/worklogs/freelancers`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        .then((response) => {
          setFreelancers(response.data.data || [])
          setLoadingFreelancers(false)
        })
        .catch((err) => {
          console.error("Failed to load freelancers:", err)
          setLoadingFreelancers(false)
        })
    }
  }, [isOpen])

  const onSubmit = async (data: FormData) => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    setLoading(true)
    try {
      await axios.post(
        `${apiUrl}/api/v1/worklogs/`,
        data,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      )
      alert("Worklog created successfully")
      form.reset()
      setIsOpen(false)
      if (onSuccess) {
        onSuccess()
      }
    } catch (error: any) {
      console.error("Failed to create worklog:", error)
      const errorMessage = error.response?.data?.detail || "Failed to create worklog. Please try again."
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button aria-label="Add new worklog">
          <Plus />
          Add Worklog
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Worklog</DialogTitle>
          <DialogDescription>
            Fill in the details to create a new worklog.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="freelancer_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Freelancer <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      disabled={loadingFreelancers}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a freelancer" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {freelancers.map((freelancer) => (
                          <SelectItem key={freelancer.id} value={freelancer.id}>
                            {freelancer.full_name} (${freelancer.hourly_rate}/hr)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

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
                        placeholder="e.g. Frontend Development"
                        type="text"
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
                name="task_description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Task Description</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Optional description"
                        type="text"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={loading}>
                  Cancel
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={loading}>
                Save
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default AddWorklog
