import { useState, useEffect } from "react"
import { createFileRoute } from "@tanstack/react-router"
import axios from "axios"
import { WorklogDetail } from "@/components/Worklogs/WorklogDetail"

export const Route = createFileRoute("/_layout/worklogs/$worklogId")({
  component: WorklogDetailPage,
  head: () => ({
    meta: [
      {
        title: "Worklog Details - Payment Dashboard",
      },
    ],
  }),
})

function WorklogDetailPage() {
  const { worklogId } = Route.useParams()
  const [worklog, setWorklog] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  const axiosInstance = axios.create({
    baseURL: "http://localhost:8000",
  })

  useEffect(() => {
    const fetchWorklog = async () => {
      setIsLoading(true)
      try {
        const token = localStorage.getItem("access_token")
        const response = await axiosInstance.get(`http://localhost:8000/api/v1/worklogs/${worklogId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        setWorklog(response.data)
      } catch (error: any) {
        console.error("Failed to fetch worklog:", error)
        setWorklog(null)
      } finally {
        setIsLoading(false)
      }
    }

    fetchWorklog()
  }, [worklogId])

  if (!worklog && !isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-muted-foreground">Worklog not found</div>
      </div>
    )
  }

  return <WorklogDetail worklog={worklog} isLoading={isLoading} />
}

