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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"

interface AddTimeEntryProps {
  worklogId?: string
  onSuccess?: () => void
}

interface Worklog {
  id: string
  task_id: string
  freelancer_id: string
  status: string
  created_at: string
  task: {
    id: string
    title: string
  } | null
}

export function AddTimeEntry({ worklogId, onSuccess }: AddTimeEntryProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [worklogs, setWorklogs] = useState<Worklog[]>([])
  const [selectedWorklogId, setSelectedWorklogId] = useState(worklogId || "")
  const [hours, setHours] = useState("")
  const [rate, setRate] = useState("")
  const [description, setDescription] = useState("")
  const [entryDate, setEntryDate] = useState(
    new Date().toISOString().split("T")[0]
  )

  const axiosInstance = axios.create({
    baseURL: "http://localhost:8000",
  })

  useEffect(() => {
    if (isOpen && !worklogId) {
      loadWorklogs()
    } else if (worklogId) {
      setSelectedWorklogId(worklogId)
    }
  }, [isOpen, worklogId])

  const loadWorklogs = async () => {
    try {
      const token = localStorage.getItem("access_token")
      const response = await axiosInstance.get(
        "http://localhost:8000/api/v1/worklogs",
        {
          params: { skip: 0, limit: 100 },
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      setWorklogs(response.data.data || [])
    } catch (error: any) {
      console.error("Failed to load worklogs:", error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedWorklogId || !hours || !rate) {
      toast.error("Please fill in all required fields")
      return
    }

    const hoursNum = parseFloat(hours)
    const rateNum = parseFloat(rate)

    if (isNaN(hoursNum) || hoursNum <= 0) {
      toast.error("Hours must be a positive number")
      return
    }

    if (isNaN(rateNum) || rateNum < 0) {
      toast.error("Rate must be a non-negative number")
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem("access_token")
      await axiosInstance.post(
        "http://localhost:8000/api/v1/worklogs/time-entries",
        {
          worklog_id: selectedWorklogId,
          hours: hoursNum,
          rate: rateNum,
          description: description.trim() || null,
          entry_date: new Date(entryDate).toISOString(),
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      toast.success("Time entry created successfully")
      setHours("")
      setRate("")
      setDescription("")
      setEntryDate(new Date().toISOString().split("T")[0])
      setIsOpen(false)
      if (onSuccess) {
        onSuccess()
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to create time entry")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant={worklogId ? "outline" : "default"}>
          <Plus className="mr-2 h-4 w-4" />
          Add Time Entry
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Time Entry</DialogTitle>
          <DialogDescription>
            Record time worked on a task.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            {!worklogId && (
              <div className="space-y-2">
                <Label htmlFor="time-entry-worklog">
                  Worklog <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={selectedWorklogId}
                  onValueChange={setSelectedWorklogId}
                  required
                >
                  <SelectTrigger id="time-entry-worklog">
                    <SelectValue placeholder="Select a worklog" />
                  </SelectTrigger>
                  <SelectContent>
                    {worklogs.map((wl) => (
                      <SelectItem key={wl.id} value={wl.id}>
                        {wl.task?.title || "Unknown Task"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="time-entry-date">
                Date <span className="text-destructive">*</span>
              </Label>
              <Input
                id="time-entry-date"
                type="date"
                value={entryDate}
                onChange={(e) => setEntryDate(e.target.value)}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="time-entry-hours">
                  Hours <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="time-entry-hours"
                  type="number"
                  step="0.25"
                  min="0.25"
                  placeholder="2.5"
                  value={hours}
                  onChange={(e) => setHours(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="time-entry-rate">
                  Rate ($/hr) <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="time-entry-rate"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="50.00"
                  value={rate}
                  onChange={(e) => setRate(e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="time-entry-description">Description</Label>
              <Input
                id="time-entry-description"
                placeholder="What did you work on?"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline" disabled={isLoading}>
                Cancel
              </Button>
            </DialogClose>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Creating..." : "Create Time Entry"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

