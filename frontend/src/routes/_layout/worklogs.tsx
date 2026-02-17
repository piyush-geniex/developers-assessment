import { useState, useEffect } from "react"
import { createFileRoute } from "@tanstack/react-router"
import { Calendar, DollarSign } from "lucide-react"
import axios from "axios"
import { WorklogList } from "@/components/Worklogs/WorklogList"
import { AddTask } from "@/components/Worklogs/AddTask"
import { AddWorklog } from "@/components/Worklogs/AddWorklog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export const Route = createFileRoute("/_layout/worklogs")({
  component: Worklogs,
  head: () => ({
    meta: [
      {
        title: "Worklogs - Payment Dashboard",
      },
    ],
  }),
})

function Worklogs() {
  const [worklogs, setWorklogs] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")

  const axiosInstance = axios.create({
    baseURL: "http://localhost:8000",
  })

  const fetchWorklogs = async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem("access_token")
      const params: any = { skip: 0, limit: 100 }
      if (startDate) {
        params.start_date = new Date(startDate).toISOString()
      }
      if (endDate) {
        params.end_date = new Date(endDate).toISOString()
      }

      const response = await axiosInstance.get("http://localhost:8000/api/v1/worklogs", {
        params,
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      setWorklogs(response.data.data || [])
    } catch (error: any) {
      console.error("Failed to fetch worklogs:", error)
      setWorklogs([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchWorklogs()
  }, [])

  const handleFilter = () => {
    fetchWorklogs()
  }

  const totalEarnings = worklogs.reduce(
    (sum, wl) => sum + (wl.total_earnings || 0),
    0
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Worklogs</h1>
          <p className="text-muted-foreground">
            View all worklogs and earnings per task
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <DollarSign className="h-5 w-5" />
            Total: ${totalEarnings.toFixed(2)}
          </div>
          <div className="flex gap-2">
            <AddTask onSuccess={fetchWorklogs} />
            <AddWorklog onSuccess={fetchWorklogs} />
          </div>
        </div>
      </div>

      <div className="flex gap-4 items-end">
        <div className="space-y-2">
          <Label htmlFor="filter-start-date">Start Date</Label>
          <Input
            id="filter-start-date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="filter-end-date">End Date</Label>
          <Input
            id="filter-end-date"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <Button onClick={handleFilter}>
          <Calendar className="mr-2 h-4 w-4" />
          Filter
        </Button>
        {(startDate || endDate) && (
          <Button variant="outline" onClick={() => {
            setStartDate("")
            setEndDate("")
            fetchWorklogs()
          }}>
            Clear
          </Button>
        )}
      </div>

      <WorklogList worklogs={worklogs} isLoading={isLoading} />
    </div>
  )
}

