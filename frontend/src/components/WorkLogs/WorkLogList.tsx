import { useState } from "react"
import { ChevronDown, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import TimeEntriesView from "./TimeEntriesView"
import DateRangeFilter from "./DateRangeFilter"

const axios = require('axios').default
axios.defaults.baseURL = 'http://localhost:8000'

interface WorkLogListProps {
  worklogs: any[]
  selectedWorklogs: string[]
  setSelectedWorklogs: (ids: string[]) => void
}

export default function WorkLogList({
  worklogs,
  selectedWorklogs,
  setSelectedWorklogs,
}: WorkLogListProps) {
  const [expandedWorklog, setExpandedWorklog] = useState<string | null>(null)
  const [filteredWorklogs, setFilteredWorklogs] = useState<any[]>(worklogs)
  const [activeFilter, setActiveFilter] = useState<string | null>(null)

  const handleToggleWorklog = (id: string) => {
    if (selectedWorklogs.includes(id)) {
      setSelectedWorklogs(selectedWorklogs.filter((wlId) => wlId !== id))
    } else {
      setSelectedWorklogs([...selectedWorklogs, id])
    }
  }

  const handleExclude = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token')
      await axios.post(`http://localhost:8000/api/v1/worklogs/${id}/exclude`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      window.location.reload()
    } catch (error) {
      console.error('Failed to exclude worklog:', error)
    }
  }

  const handleDateFilter = async (dateFrom: string, dateTo: string) => {
    try {
      const token = localStorage.getItem('access_token')
      const response = await axios.get('http://localhost:8000/api/v1/worklogs/filter/by-date-range', {
        headers: { Authorization: `Bearer ${token}` },
        params: { date_from: dateFrom, date_to: dateTo }
      })
      setFilteredWorklogs(response.data.worklogs)
    } catch (error) {
      console.error('Failed to filter worklogs:', error)
    }
  }

  const handleClearFilter = () => {
    setFilteredWorklogs(worklogs)
    setActiveFilter(null)
  }

  const displayWorklogs = filteredWorklogs.length > 0 ? filteredWorklogs : worklogs

  return (
    <div>
      <div className="mb-4 flex gap-2">
        <Button
          variant={activeFilter === 'date' ? 'default' : 'outline'}
          onClick={() => setActiveFilter(activeFilter === 'date' ? null : 'date')}
        >
          Date Range Filter
        </Button>
        {activeFilter && (
          <Button variant="ghost" onClick={handleClearFilter}>
            Clear Filter
          </Button>
        )}
      </div>

      {activeFilter === 'date' && (
        <div className="mb-4">
          <DateRangeFilter onFilter={handleDateFilter} />
        </div>
      )}

      <div className="border rounded-lg">
        <table className="w-full">
          <thead className="bg-muted/50 border-b">
            <tr>
              <th className="text-left p-3 w-12"></th>
              <th className="text-left p-3 w-12"></th>
              <th className="text-left p-3">Task Name</th>
              <th className="text-left p-3">Freelancer</th>
              <th className="text-left p-3">Total Hours</th>
              <th className="text-left p-3">Rate</th>
              <th className="text-left p-3">Amount Earned</th>
              <th className="text-left p-3">Status</th>
              <th className="text-left p-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {displayWorklogs.map((worklog: any) => (
              <>
                <tr key={worklog.id} className="border-b hover:bg-muted/30">
                  <td className="p-3">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={() =>
                        setExpandedWorklog(
                          expandedWorklog === worklog.id ? null : worklog.id
                        )
                      }
                    >
                      {expandedWorklog === worklog.id ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </Button>
                  </td>
                  <td className="p-3">
                    <Checkbox
                      checked={selectedWorklogs.includes(worklog.id)}
                      onCheckedChange={() => handleToggleWorklog(worklog.id)}
                      disabled={worklog.status === 'EXCLUDED' || worklog.status === 'PAID'}
                    />
                  </td>
                  <td className="p-3 font-medium">{worklog.task_name}</td>
                  <td className="p-3">{worklog.freelancer_id}</td>
                  <td className="p-3">{worklog.total_hours.toFixed(2)}</td>
                  <td className="p-3">${worklog.hourly_rate.toFixed(2)}</td>
                  <td className="p-3 font-semibold">${worklog.total_amount.toFixed(2)}</td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        worklog.status === 'PENDING'
                          ? 'bg-yellow-100 text-yellow-800'
                          : worklog.status === 'PAID'
                          ? 'bg-green-100 text-green-800'
                          : worklog.status === 'EXCLUDED'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {worklog.status}
                    </span>
                  </td>
                  <td className="p-3">
                    {worklog.status === 'PENDING' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleExclude(worklog.id)}
                      >
                        Exclude
                      </Button>
                    )}
                  </td>
                </tr>
                {expandedWorklog === worklog.id && (
                  <tr>
                    <td colSpan={9} className="p-4 bg-muted/20">
                      <TimeEntriesView worklogId={worklog.id} />
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
