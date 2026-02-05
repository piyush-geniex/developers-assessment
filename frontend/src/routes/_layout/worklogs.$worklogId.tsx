import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useState } from "react"

export const Route = createFileRoute("/_layout/worklogs/$worklogId")({
  component: WorklogDetailPage,
  head: () => ({
    meta: [
      {
        title: "Worklog Detail - WorkLog Payment Dashboard",
      },
    ],
  }),
})

function WorklogDetailPage() {
  const { worklogId } = Route.useParams()
  const [detail, setDetail] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchDetail = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(
          `http://localhost:8000/api/v1/worklogs/${worklogId}`,
        )
        if (!res.ok) {
          throw new Error(`Failed to load worklog: ${res.status}`)
        }
        const data: any = await res.json()
        setDetail(data)
      } catch (err: any) {
        console.error(err)
        setError("Failed to load worklog. Please try again.")
      } finally {
        setLoading(false)
      }
    }

    fetchDetail()
  }, [worklogId])

  if (loading) {
    return <div>Loading worklog...</div>
  }

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  if (!detail) {
    return <div>No worklog found.</div>
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Worklog Detail</h1>
        <p className="text-sm text-muted-foreground">ID: {detail.id}</p>
      </div>

      <div className="space-y-1 text-sm">
        <div>Task: {detail.task_name}</div>
        <div>Freelancer ID: {detail.freelancer_id}</div>
        <div>Status: {detail.status}</div>
        <div>Total Amount: {detail.total_amount}</div>
      </div>

      <div className="overflow-x-auto border rounded-md">
        <table className="min-w-full text-sm">
          <thead className="border-b bg-muted">
            <tr>
              <th className="px-3 py-2 text-left">Start Time (UTC)</th>
              <th className="px-3 py-2 text-left">End Time (UTC)</th>
              <th className="px-3 py-2 text-left">Rate / Hour</th>
              <th className="px-3 py-2 text-left">Amount</th>
              <th className="px-3 py-2 text-left">Notes</th>
            </tr>
          </thead>
          <tbody>
            {(detail.entries || []).map((entry: any) => (
              <tr key={entry.id} className="border-b last:border-b-0">
                <td className="px-3 py-2 align-top">{entry.start_time}</td>
                <td className="px-3 py-2 align-top">{entry.end_time}</td>
                <td className="px-3 py-2 align-top">{entry.rate_per_hour}</td>
                <td className="px-3 py-2 align-top">{entry.amount}</td>
                <td className="px-3 py-2 align-top">{entry.notes}</td>
              </tr>
            ))}
            {(!detail.entries || detail.entries.length === 0) && (
              <tr>
                <td className="px-3 py-4 text-center" colSpan={5}>
                  No time entries found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
