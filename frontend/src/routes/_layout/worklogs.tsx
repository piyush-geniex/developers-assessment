import { createFileRoute } from "@tanstack/react-router"

import WorklogList from "@/components/Worklogs/WorklogList"
import AddWorklog from "@/components/Worklogs/AddWorklog"

export const Route = createFileRoute("/_layout/worklogs")({
  component: Worklogs,
  head: () => ({
    meta: [
      {
        title: "Worklogs - FastAPI Cloud",
      },
    ],
  }),
})

function Worklogs() {
  const handleSuccess = () => {
    window.location.reload()
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Worklogs</h1>
          <p className="text-muted-foreground">View all worklogs and earnings</p>
        </div>
        <AddWorklog onSuccess={handleSuccess} />
      </div>
      <WorklogList />
    </div>
  )
}
