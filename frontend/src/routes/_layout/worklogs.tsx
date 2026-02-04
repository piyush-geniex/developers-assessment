import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Search } from "lucide-react"
import { Suspense, useState } from "react"

import PendingItems from "@/components/Pending/PendingItems"
import WorkLogList from "@/components/WorkLogs/WorkLogList"
import PaymentFlow from "@/components/WorkLogs/PaymentFlow"
import { Button } from "@/components/ui/button"

const axios = require('axios').default
axios.defaults.baseURL = 'http://localhost:8000'

function getWorkLogsQueryOptions() {
  return {
    queryFn: async (): Promise<any> => {
      const token = localStorage.getItem('access_token')
      const response = await axios.get('/api/v1/worklogs/', {
        headers: { Authorization: `Bearer ${token}` },
        params: { skip: 0, limit: 100 }
      })
      return response.data
    },
    queryKey: ["worklogs"],
  }
}

export const Route = createFileRoute("/_layout/worklogs")({
  component: WorkLogs,
  head: () => ({
    meta: [
      {
        title: "WorkLogs - Payment Dashboard",
      },
    ],
  }),
})

function WorkLogsTableContent() {
  const { data: worklogs } = useSuspenseQuery(getWorkLogsQueryOptions())
  const [showPaymentFlow, setShowPaymentFlow] = useState(false)
  const [selectedWorklogs, setSelectedWorklogs] = useState<string[]>([])

  if (worklogs.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No worklogs found</h3>
        <p className="text-muted-foreground">Worklogs will appear here once created</p>
      </div>
    )
  }

  return (
    <div>
      <WorkLogList
        worklogs={worklogs.data}
        selectedWorklogs={selectedWorklogs}
        setSelectedWorklogs={setSelectedWorklogs}
      />

      {selectedWorklogs.length > 0 && (
        <div className="mt-4 flex justify-end">
          <Button onClick={() => setShowPaymentFlow(true)}>
            Process Payment ({selectedWorklogs.length} worklogs)
          </Button>
        </div>
      )}

      {showPaymentFlow && (
        <PaymentFlow
          worklogIds={selectedWorklogs}
          onClose={() => {
            setShowPaymentFlow(false)
            setSelectedWorklogs([])
          }}
        />
      )}
    </div>
  )
}

function WorkLogsTable() {
  return (
    <Suspense fallback={<PendingItems />}>
      <WorkLogsTableContent />
    </Suspense>
  )
}

function WorkLogs() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">WorkLog Payment Dashboard</h1>
          <p className="text-muted-foreground">Review freelancer worklogs and process payments</p>
        </div>
      </div>
      <WorkLogsTable />
    </div>
  )
}
