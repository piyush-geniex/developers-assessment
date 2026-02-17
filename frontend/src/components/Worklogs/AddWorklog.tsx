import { Plus } from "lucide-react"
import { useState, useEffect } from "react"
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
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"

interface AddWorklogProps {
  onSuccess?: () => void
}

interface Task {
  id: string
  title: string
  description: string | null
  created_at: string
}

interface Freelancer {
  id: string
  email: string
  full_name: string | null
}

export function AddWorklog({ onSuccess }: AddWorklogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [tasks, setTasks] = useState<Task[]>([])
  const [freelancers, setFreelancers] = useState<Freelancer[]>([])
  const [selectedTaskId, setSelectedTaskId] = useState("")
  const [selectedFreelancerId, setSelectedFreelancerId] = useState("")
  const [status, setStatus] = useState("PENDING")

  const axiosInstance = axios.create({
    baseURL: "http://localhost:8000",
  })

  useEffect(() => {
    if (isOpen) {
      loadTasks()
      loadFreelancers()
    }
  }, [isOpen])

  const loadTasks = async () => {
    try {
      const token = localStorage.getItem("access_token")
      const response = await axiosInstance.get(
        "http://localhost:8000/api/v1/worklogs/tasks",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      setTasks(response.data as any)
    } catch (error: any) {
      console.error("Failed to load tasks:", error)
    }
  }

  const loadFreelancers = async () => {
    try {
      const token = localStorage.getItem("access_token")
      const response = await axiosInstance.get(
        "http://localhost:8000/api/v1/worklogs/freelancers",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      setFreelancers(response.data as any)
    } catch (error: any) {
      console.error("Failed to load freelancers:", error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTaskId || !selectedFreelancerId) {
      toast.error("Please select both task and freelancer")
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem("access_token")
      await axiosInstance.post(
        "http://localhost:8000/api/v1/worklogs",
        {
          task_id: selectedTaskId,
          freelancer_id: selectedFreelancerId,
          status: status,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      toast.success("Worklog created successfully")
      setSelectedTaskId("")
      setSelectedFreelancerId("")
      setStatus("PENDING")
      setIsOpen(false)
      if (onSuccess) {
        onSuccess()
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to create worklog")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Worklog
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Worklog</DialogTitle>
          <DialogDescription>
            Create a new worklog by assigning a freelancer to a task.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="worklog-task">
                Task <span className="text-destructive">*</span>
              </Label>
              <Select value={selectedTaskId} onValueChange={setSelectedTaskId} required>
                <SelectTrigger id="worklog-task">
                  <SelectValue placeholder="Select a task" />
                </SelectTrigger>
                <SelectContent>
                  {tasks.map((task) => (
                    <SelectItem key={task.id} value={task.id}>
                      {task.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="worklog-freelancer">
                Freelancer <span className="text-destructive">*</span>
              </Label>
              <Select
                value={selectedFreelancerId}
                onValueChange={setSelectedFreelancerId}
                required
              >
                <SelectTrigger id="worklog-freelancer">
                  <SelectValue placeholder="Select a freelancer" />
                </SelectTrigger>
                <SelectContent>
                  {freelancers.map((freelancer) => (
                    <SelectItem key={freelancer.id} value={freelancer.id}>
                      {freelancer.full_name || freelancer.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="worklog-status">Status</Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger id="worklog-status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PENDING">PENDING</SelectItem>
                  <SelectItem value="COMPLETED">COMPLETED</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" disabled={isLoading}>
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Creating..." : "Create Worklog"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

