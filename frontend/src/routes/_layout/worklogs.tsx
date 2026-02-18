import { createFileRoute, Outlet } from "@tanstack/react-router"

const WorklogsLayout = () => <Outlet />

export const Route = createFileRoute("/_layout/worklogs")({
  component: WorklogsLayout,
})
