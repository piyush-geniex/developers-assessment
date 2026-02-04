import { createFileRoute } from "@tanstack/react-router"

import PaymentBatch from "@/components/Worklogs/PaymentBatch"

export const Route = createFileRoute("/_layout/payments")({
  component: Payments,
  head: () => ({
    meta: [
      {
        title: "Payments - FastAPI Cloud",
      },
    ],
  }),
})

function Payments() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Payments</h1>
          <p className="text-muted-foreground">Process payment batches for worklogs</p>
        </div>
      </div>
      <PaymentBatch />
    </div>
  )
}
