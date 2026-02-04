import { useQuery } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"

const axios = require('axios').default
axios.defaults.baseURL = 'http://localhost:8000'

interface TimeEntriesViewProps {
  worklogId: string
}

export default function TimeEntriesView({ worklogId }: TimeEntriesViewProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["timeEntries", worklogId],
    queryFn: async (): Promise<any> => {
      const token = localStorage.getItem('access_token')
      const response = await axios.get(`http://localhost:8000/api/v1/worklogs/${worklogId}/time-entries`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-500 p-4">
        Failed to load time entries. Please try again.
      </div>
    )
  }

  if (!data || data.data.length === 0) {
    return (
      <div className="text-muted-foreground p-4">
        No time entries recorded for this worklog yet.
      </div>
    )
  }

  return (
    <div>
      <h4 className="font-semibold mb-3">Time Entries</h4>
      <table className="w-full border rounded">
        <thead className="bg-muted/30">
          <tr>
            <th className="text-left p-2">Date</th>
            <th className="text-left p-2">Description</th>
            <th className="text-left p-2">Hours</th>
          </tr>
        </thead>
        <tbody>
          {data.data.map((entry: any) => (
            <tr key={entry.id} className="border-t">
              <td className="p-2">{entry.date}</td>
              <td className="p-2">{entry.description}</td>
              <td className="p-2">{entry.hours.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
