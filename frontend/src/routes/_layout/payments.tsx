import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

export const Route = createFileRoute("/_layout/payments")({
  component: PaymentsPage,
  head: () => ({
    meta: [
      {
        title: "Payments - WorkLog Payment Dashboard",
      },
    ],
  }),
})

function PaymentsPage() {
  const [fromDate, setFromDate] = useState("")
  const [toDate, setToDate] = useState("")
  const [excludeWorklogs, setExcludeWorklogs] = useState("")
  const [excludeFreelancers, setExcludeFreelancers] = useState("")
  const [preview, setPreview] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const parseIdList = (value: string): string[] | null => {
    const trimmed = value.trim()
    if (!trimmed) return null
    return trimmed.split(",").map((v) => v.trim())
  }

  const handlePreview = async () => {
    setLoading(true)
    setError(null)
    try {
      const body: any = {
        from_date: fromDate,
        to_date: toDate,
        worklog_ids: null,
        exclude_worklog_ids: parseIdList(excludeWorklogs),
        exclude_freelancer_ids: parseIdList(excludeFreelancers),
      }

      const res = await fetch(
        "http://localhost:8000/api/v1/worklogs/payment-preview",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        },
      )
      if (!res.ok) {
        throw new Error(`Failed to preview payment: ${res.status}`)
      }
      const data: any = await res.json()
      setPreview(data)
    } catch (err: any) {
      console.error(err)
      setError("Failed to preview payment. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async () => {
    if (!fromDate || !toDate) return

    setLoading(true)
    setError(null)
    try {
      const body: any = {
        from_date: fromDate,
        to_date: toDate,
        worklog_ids: null,
        exclude_worklog_ids: parseIdList(excludeWorklogs),
        exclude_freelancer_ids: parseIdList(excludeFreelancers),
      }

      const res = await fetch(
        "http://localhost:8000/api/v1/worklogs/payment-batch",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        },
      )
      if (!res.ok) {
        throw new Error(`Failed to create payment batch: ${res.status}`)
      }
      const data: any = await res.json()
      setPreview(data)
    } catch (err: any) {
      console.error(err)
      setError("Failed to create payment batch. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Payments</h1>

      <div className="space-y-2 max-w-xl">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">From date (YYYY-MM-DD)</label>
          <input
            type="text"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">To date (YYYY-MM-DD)</label>
          <input
            type="text"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">
            Exclude worklog IDs (comma-separated UUIDs)
          </label>
          <input
            type="text"
            value={excludeWorklogs}
            onChange={(e) => setExcludeWorklogs(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium">
            Exclude freelancer IDs (comma-separated UUIDs)
          </label>
          <input
            type="text"
            value={excludeFreelancers}
            onChange={(e) => setExcludeFreelancers(e.target.value)}
            className="border rounded px-2 py-1 text-sm"
          />
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={handlePreview}
            disabled={loading}
            className="border rounded px-3 py-1 text-sm disabled:opacity-50"
          >
            Preview
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={loading}
            className="border rounded px-3 py-1 text-sm disabled:opacity-50"
          >
            Confirm Batch
          </button>
        </div>

        {loading && <div>Processing...</div>}
        {error && <div className="text-red-500">{error}</div>}
      </div>

      {preview && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Preview Result</h2>
          <div className="text-sm space-y-1">
            <div>From: {preview.from_date}</div>
            <div>To: {preview.to_date}</div>
            <div>Total Amount: {preview.total_amount}</div>
          </div>

          <div className="overflow-x-auto border rounded-md mt-2">
            <table className="min-w-full text-sm">
              <thead className="border-b bg-muted">
                <tr>
                  <th className="px-3 py-2 text-left">Task</th>
                  <th className="px-3 py-2 text-left">Freelancer ID</th>
                  <th className="px-3 py-2 text-left">Status</th>
                  <th className="px-3 py-2 text-left">Total Amount</th>
                  <th className="px-3 py-2 text-left">First Entry</th>
                  <th className="px-3 py-2 text-left">Last Entry</th>
                </tr>
              </thead>
              <tbody>
                {(preview.worklogs || []).map((wl: any) => (
                  <tr key={wl.id} className="border-b last:border-b-0">
                    <td className="px-3 py-2 align-top">{wl.task_name}</td>
                    <td className="px-3 py-2 align-top">{wl.freelancer_id}</td>
                    <td className="px-3 py-2 align-top">{wl.status}</td>
                    <td className="px-3 py-2 align-top">{wl.total_amount}</td>
                    <td className="px-3 py-2 align-top">{wl.first_entry_at}</td>
                    <td className="px-3 py-2 align-top">{wl.last_entry_at}</td>
                  </tr>
                ))}
                {(!preview.worklogs || preview.worklogs.length === 0) && (
                  <tr>
                    <td className="px-3 py-4 text-center" colSpan={6}>
                      No worklogs in this range.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
