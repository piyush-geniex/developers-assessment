import { createFileRoute } from "@tanstack/react-router"
import { PaymentWorkflow } from "@/components/Worklogs/PaymentWorkflow"

export const Route = createFileRoute("/_layout/payments")({
  component: Payments,
  head: () => ({
    meta: [
      {
        title: "Process Payments - Payment Dashboard",
      },
    ],
  }),
})

function Payments() {
  return <PaymentWorkflow />
}

