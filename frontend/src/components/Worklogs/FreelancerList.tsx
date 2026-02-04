import axios from "axios"
import { useQuery } from "@tanstack/react-query"
import { Search } from "lucide-react"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export default function FreelancerList() {
  const { data, isLoading: loading, isError } = useQuery({
    queryKey: ["freelancers"],
    queryFn: async () => {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
      const token = localStorage.getItem("access_token")
      const response = await axios.get(`${apiUrl}/api/v1/worklogs/freelancers`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      return response.data
    },
  })

  const freelancers = data?.data || []

  if (loading) {
    return <div className="text-center py-12">Loading freelancers...</div>
  }

  if (isError) {
    return <div className="text-center py-12 text-red-500">Failed to load freelancers</div>
  }

  if (freelancers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No freelancers found</h3>
        <p className="text-muted-foreground">Add freelancers to get started</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Hourly Rate</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created At</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {freelancers.map((fl: any) => (
          <TableRow key={fl.id}>
            <TableCell className="font-medium">{fl.full_name}</TableCell>
            <TableCell>${fl.hourly_rate.toFixed(2)}</TableCell>
            <TableCell>
              <span
                className={
                  fl.status === "active" ? "text-green-600" : "text-gray-600"
                }
              >
                {fl.status}
              </span>
            </TableCell>
            <TableCell>{fl.created_at}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
