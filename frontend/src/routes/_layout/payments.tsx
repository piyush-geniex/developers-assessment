import { createFileRoute } from "@tanstack/react-router"

import PaymentBatch from "@/components/Worklogs/PaymentBatch"
import AddPayment from "@/components/Worklogs/AddPayment"

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
  const handleSuccess = () => {
    window.location.reload()
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Payments</h1>
          <p className="text-muted-foreground">Process payment batches for worklogs</p>
        </div>
        <AddPayment onSuccess={handleSuccess} />
      </div>
      <PaymentBatch />
    </div>
  )
}
