import axios from "axios"
import { useEffect, useState } from "react"
import { Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export default function WorklogList() {
  const [worklogs, setWorklogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const pageSize = 10

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    setLoading(true)
    axios
      .get(`${apiUrl}/api/v1/worklogs/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((response) => {
        setWorklogs(response.data || [])
        setLoading(false)
      })
      .catch((err) => {
        setError("Failed to load worklogs")
        setLoading(false)
        console.error(err)
      })
  }, [])

  if (loading) {
    return <div className="text-center py-12">Loading worklogs...</div>
  }

  if (error) {
    return <div className="text-center py-12 text-red-500">{error}</div>
  }

  if (worklogs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No worklogs found</h3>
        <p className="text-muted-foreground">Create a new worklog to get started</p>
      </div>
    )
  }

  const displayed = worklogs.slice((page - 1) * pageSize, page * pageSize)
  const totalPages = Math.ceil(worklogs.length / pageSize)

  return (
    <div className="flex flex-col gap-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Task Name</TableHead>
            <TableHead>Freelancer</TableHead>
            <TableHead>Total Hours</TableHead>
            <TableHead>Amount Earned</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Created At</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayed.map((wl: any) => (
            <TableRow key={wl.id}>
              <TableCell className="font-medium">{wl.task_name}</TableCell>
              <TableCell>{wl.freelancer_name}</TableCell>
              <TableCell>{wl.total_hours}</TableCell>
              <TableCell>${wl.amount_earned.toFixed(2)}</TableCell>
              <TableCell>
                <span
                  className={
                    wl.payment_status === "PAID"
                      ? "text-green-600"
                      : "text-yellow-600"
                  }
                >
                  {wl.payment_status}
                </span>
              </TableCell>
              <TableCell>{wl.created_at}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
          >
            Previous
          </Button>
          <span className="py-2 px-4">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            onClick={() => setPage(page + 1)}
            disabled={page === totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
