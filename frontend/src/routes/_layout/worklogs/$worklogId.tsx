import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"

const API_URL = import.meta.env.VITE_API_URL

async function fetchWorklogDetail(id: string): Promise<any> {
  const token = localStorage.getItem("access_token")
  const res = await fetch(`${API_URL}/api/v1/worklogs/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to load worklog")
  return res.json()
}

export const Route = createFileRoute("/_layout/worklogs/$worklogId")({
  component: WorklogDetailPage,
  loader: ({ params }) => fetchWorklogDetail((params as { worklogId: string }).worklogId),
  head: () => ({
    meta: [{ title: "Worklog detail - Payment Dashboard" }],
  }),
})

function WorklogDetailContent() {
  const data = Route.useLoaderData() as any

  return (
    <div className="flex flex-col gap-6">
      <Link
        to="/worklogs"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to worklogs
      </Link>

      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {data.task_title}
        </h1>
        <p className="text-muted-foreground">
          Freelancer: {data.freelancer_email} · Status: {data.status} · Total: $
          {Number(data.total_amount).toFixed(2)}
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          Created: {data.created_at}
        </p>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">Time entries</h2>
        <div className="rounded-md border">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left p-3 font-medium">Date</th>
                <th className="text-left p-3 font-medium">Hours</th>
                <th className="text-left p-3 font-medium">Rate</th>
                <th className="text-left p-3 font-medium">Amount</th>
                <th className="text-left p-3 font-medium">Description</th>
              </tr>
            </thead>
            <tbody>
              {(data.time_entries ?? []).map((e: any) => (
                <tr key={e.id} className="border-b last:border-0">
                  <td className="p-3">{e.entry_date}</td>
                  <td className="p-3">{e.hours}</td>
                  <td className="p-3">${e.rate}</td>
                  <td className="p-3">
                    ${(e.hours * e.rate).toFixed(2)}
                  </td>
                  <td className="p-3 text-muted-foreground">
                    {e.description ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function WorklogDetailPage() {
  return <WorklogDetailContent />
}
