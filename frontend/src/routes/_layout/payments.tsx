import { createFileRoute, Outlet } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/payments")({
  component: PaymentsLayout,
})

function PaymentsLayout() {
  return <Outlet />
}
