import { createFileRoute, Link, Outlet } from "@tanstack/react-router"
import { useEffect, useMemo, useState } from "react"

const PAGE_SIZE = 10

export const Route = createFileRoute("/_layout/worklogs")({
  component: WorklogsPage,
  head: () => ({
    meta: [
      {
        title: "Worklogs - WorkLog Payment Dashboard",
      },
    ],
  }),
})

function WorklogsPage() {
  const [allWorklogs, setAllWorklogs] = useState<any[]>([])
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchWorklogs = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(
          "http://localhost:8000/api/v1/worklogs?skip=0&limit=1000",
        )
        if (!res.ok) {
          throw new Error(`Failed to load worklogs: ${res.status}`)
        }
        const data: any = await res.json()
        setAllWorklogs(data?.data ?? [])
      } catch (err: any) {
        console.error(err)
        setError("Failed to load worklogs. Please try again.")
      } finally {
        setLoading(false)
      }
    }

    fetchWorklogs()
  }, [])

  const totalPages = useMemo(() => {
    if (allWorklogs.length === 0) return 1
    return Math.ceil(allWorklogs.length / PAGE_SIZE)
  }, [allWorklogs.length])

  const pageData = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE
    const end = start + PAGE_SIZE
    return allWorklogs.slice(start, end)
  }, [allWorklogs, page])

  if (loading) {
    return <div>Loading worklogs...</div>
  }

  if (error) {
    return <div className="text-red-500">{error}</div>
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Worklogs</h1>
      <div className="overflow-x-auto border rounded-md">
        <table className="min-w-full text-sm">
          <thead className="border-b bg-muted">
            <tr>
              <th className="px-3 py-2 text-left">Task</th>
              <th className="px-3 py-2 text-left">Freelancer ID</th>
              <th className="px-3 py-2 text-left">Status</th>
              <th className="px-3 py-2 text-left">Total Amount</th>
              <th className="px-3 py-2 text-left">First Entry</th>
              <th className="px-3 py-2 text-left">Last Entry</th>
              <th className="px-3 py-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {pageData.map((wl: any) => (
              <tr key={wl.id} className="border-b last:border-b-0">
                <td className="px-3 py-2 align-top">{wl.task_name}</td>
                <td className="px-3 py-2 align-top">{wl.freelancer_id}</td>
                <td className="px-3 py-2 align-top">{wl.status}</td>
                <td className="px-3 py-2 align-top">{wl.total_amount}</td>
                <td className="px-3 py-2 align-top">{wl.first_entry_at}</td>
                <td className="px-3 py-2 align-top">{wl.last_entry_at}</td>
                <td className="px-3 py-2 align-top">
                  <Link
                    to="/worklogs/$worklogId"
                    params={{ worklogId: wl.id }}
                    className="text-blue-500 underline"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
            {pageData.length === 0 && (
              <tr>
                <td className="px-3 py-4 text-center" colSpan={7}>
                  No worklogs found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="border rounded px-2 py-1 disabled:opacity-50"
        >
          Previous
        </button>
        <span>
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          onClick={() =>
            setPage((p) => (p < totalPages ? p + 1 : p))
          }
          disabled={page >= totalPages}
          className="border rounded px-2 py-1 disabled:opacity-50"
        >
          Next
        </button>
      </div>

      {/* Render worklog detail route when on /worklogs/$worklogId */}
      <Outlet />
    </div>
  )
}
