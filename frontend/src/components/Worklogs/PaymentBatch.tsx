import axios from "axios"
import { useEffect, useState } from "react"
import { Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"

export default function PaymentBatch() {
  const [worklogs, setWorklogs] = useState<any[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [processing, setProcessing] = useState(false)

  const fetchWorklogs = () => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)

    setLoading(true)
    axios
      .get(`${apiUrl}/api/v1/worklogs/payment-eligible/list?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((response) => {
        setWorklogs(response.data || [])
        setLoading(false)
      })
      .catch((err) => {
        setError("Failed to load payment-eligible worklogs")
        setLoading(false)
        console.error(err)
      })
  }

  useEffect(() => {
    fetchWorklogs()
  }, [])

  const handleSelect = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  const handleExcludeFreelancer = (freelancerId: string) => {
    const newSelected = new Set(selectedIds)
    worklogs.forEach((wl) => {
      if (wl.freelancer_id === freelancerId) {
        newSelected.delete(wl.id)
      }
    })
    setSelectedIds(newSelected)
  }

  const handleProcessPayment = () => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    setProcessing(true)
    axios
      .post(
        `${apiUrl}/api/v1/worklogs/process-payment`,
        {
          worklog_ids: Array.from(selectedIds),
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      )
      .then(() => {
        alert("Payment processed successfully!")
        setSelectedIds(new Set())
        fetchWorklogs()
        setProcessing(false)
      })
      .catch((err) => {
        alert("Failed to process payment")
        setProcessing(false)
        console.error(err)
      })
  }

  if (loading) {
    return <div className="text-center py-12">Loading payment-eligible worklogs...</div>
  }

  if (error) {
    return <div className="text-center py-12 text-red-500">{error}</div>
  }

  const selectedWorklogs = worklogs.filter((wl) => selectedIds.has(wl.id))
  const totalAmount = selectedWorklogs.reduce((sum, wl) => sum + wl.amount_earned, 0)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex gap-4">
        <div>
          <label className="text-sm font-medium">Start Date</label>
          <Input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div>
          <label className="text-sm font-medium">End Date</label>
          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <div className="flex items-end">
          <Button onClick={fetchWorklogs}>Filter</Button>
        </div>
      </div>

      {worklogs.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center py-12">
          <div className="rounded-full bg-muted p-4 mb-4">
            <Search className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">No payment-eligible worklogs</h3>
          <p className="text-muted-foreground">All worklogs have been paid</p>
        </div>
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Select</TableHead>
                <TableHead>Task Name</TableHead>
                <TableHead>Freelancer</TableHead>
                <TableHead>Hours</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {worklogs.map((wl: any) => (
                <TableRow key={wl.id}>
                  <TableCell>
                    <Checkbox
                      checked={selectedIds.has(wl.id)}
                      onCheckedChange={() => handleSelect(wl.id)}
                    />
                  </TableCell>
                  <TableCell className="font-medium">{wl.task_name}</TableCell>
                  <TableCell>{wl.freelancer_name}</TableCell>
                  <TableCell>{wl.total_hours}</TableCell>
                  <TableCell>${wl.amount_earned.toFixed(2)}</TableCell>
                  <TableCell>{wl.created_at}</TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleExcludeFreelancer(wl.freelancer_id)}
                    >
                      Exclude Freelancer
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {selectedIds.size > 0 && (
            <div className="bg-muted p-6 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Payment Summary</h3>
              <div className="space-y-2">
                <p>
                  <span className="font-medium">Total Worklogs:</span> {selectedIds.size}
                </p>
                <p>
                  <span className="font-medium">Total Amount:</span> $
                  {totalAmount.toFixed(2)}
                </p>
              </div>
              <Button
                className="mt-4"
                onClick={handleProcessPayment}
                disabled={processing}
              >
                {processing ? "Processing..." : "Process Payment"}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
