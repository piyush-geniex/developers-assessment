import { createFileRoute, Outlet } from "@tanstack/react-router";

export const Route = createFileRoute("/_layout/worklogs")({
  component: Worklogs,
});

function Worklogs() {
  return <Outlet />;
}
