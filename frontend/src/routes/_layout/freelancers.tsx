import { createFileRoute } from "@tanstack/react-router"

import FreelancerList from "@/components/Worklogs/FreelancerList"
import AddFreelancer from "@/components/Worklogs/AddFreelancer"

export const Route = createFileRoute("/_layout/freelancers")({
  component: Freelancers,
  head: () => ({
    meta: [
      {
        title: "Freelancers - FastAPI Cloud",
      },
    ],
  }),
})

function Freelancers() {
  const handleSuccess = () => {
    window.location.reload()
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Freelancers</h1>
          <p className="text-muted-foreground">Manage freelancers and their rates</p>
        </div>
        <AddFreelancer onSuccess={handleSuccess} />
      </div>
      <FreelancerList />
    </div>
  )
}
