import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState, useMemo } from "react"
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../../components/ui/table"
import { Button } from "../../components/ui/button"
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription,
} from "../../components/ui/dialog"
import { Input } from "../../components/ui/input"
import { Badge } from "../../components/ui/badge"
import { WorklogsService, type WorkLogPublic } from "../../client"
import { CalendarIcon, FilterX } from "lucide-react"

export const Route = createFileRoute("/_layout/worklogs")({
  component: WorkLogsDashboard,
})

function WorkLogsDashboard() {
  const queryClient = useQueryClient()
  const [selectedLog, setSelectedLog] = useState<WorkLogPublic | null>(null)
  const [dateRange, setDateRange] = useState({ start: "", end: "" })
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ["worklogs"],
    queryFn: () => WorklogsService.listWorklogs({ skip: 0, limit: 100 }),
  })

  const payMutation = useMutation({
    mutationFn: (id: string) => WorklogsService.payWorklog({ id }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["worklogs"] }),
  })

  // --- FIXED FILTER LOGIC ---
  const filteredData = useMemo(() => {
    if (!data?.data) return []
    return data.data.filter(log => {
      // 1. If no dates selected, show everything
      if (!dateRange.start && !dateRange.end) return true

      // 2. Safety check: If log has no history, it can't match a date filter
      if (!log.time_entries || log.time_entries.length === 0) return false

      // 3. String Comparison (Safer than Date objects)
      // entry.date is "YYYY-MM-DD" from backend
      // dateRange.start is "YYYY-MM-DD" from input
      return log.time_entries.some(entry => {
        const entryDate = String(entry.date) // Ensure it's a string
        const afterStart = !dateRange.start || entryDate >= dateRange.start
        const beforeEnd = !dateRange.end || entryDate <= dateRange.end
        return afterStart && beforeEnd
      })
    })
  }, [data, dateRange])

  const toggleSelection = (id: string) => {
    const next = new Set(selectedIds)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelectedIds(next)
  }

  const handleBatchPay = async () => {
    await Promise.all(Array.from(selectedIds).map(id => payMutation.mutateAsync(id)))
    setSelectedIds(new Set())
    setIsBatchModalOpen(false)
  }

  const pendingAmount = filteredData
    .filter(d => selectedIds.has(d.id) && d.status === 'pending')
    .reduce((acc, curr) => acc + curr.total_amount, 0)

  if (isLoading) return <div className="p-8">Loading...</div>

  return (
    <div className="h-full flex-1 flex-col space-y-8 p-8 md:flex">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">WorkLogs</h2>
          <p className="text-muted-foreground">Manage invoices and payments.</p>
        </div>
        <div className="flex items-center gap-3">
            {selectedIds.size > 0 && (
                <Button onClick={() => setIsBatchModalOpen(true)}>
                    Pay {selectedIds.size} Items (${pendingAmount.toLocaleString()})
                </Button>
            )}
            <div className="flex items-center gap-2 bg-background border rounded-md p-1 shadow-sm">
                <CalendarIcon className="w-4 h-4 ml-2 text-muted-foreground" />
                <Input type="date" className="border-0 shadow-none focus-visible:ring-0 w-32 h-8 text-xs"
                    value={dateRange.start} onChange={e => setDateRange(prev => ({ ...prev, start: e.target.value }))} />
                <span className="text-muted-foreground">-</span>
                <Input type="date" className="border-0 shadow-none focus-visible:ring-0 w-32 h-8 text-xs"
                    value={dateRange.end} onChange={e => setDateRange(prev => ({ ...prev, end: e.target.value }))} />
                {(dateRange.start || dateRange.end) && (
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setDateRange({ start: "", end: "" })}>
                        <FilterX className="w-3 h-3" />
                    </Button>
                )}
            </div>
        </div>
      </div>

      <div className="rounded-md border bg-card shadow-sm">
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead className="w-[50px]"></TableHead>
                    <TableHead>Task Name</TableHead>
                    <TableHead>Freelancer</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Hours</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {filteredData.length === 0 ? (
                    <TableRow><TableCell colSpan={7} className="h-24 text-center text-muted-foreground">No worklogs found matching criteria.</TableCell></TableRow>
                ) : (
                    filteredData.map(log => (
                        <TableRow key={log.id}>
                            <TableCell>
                                {log.status === 'pending' && (
                                    <input type="checkbox" className="h-4 w-4 rounded border-gray-300"
                                        checked={selectedIds.has(log.id)} onChange={() => toggleSelection(log.id)} />
                                )}
                            </TableCell>
                            <TableCell className="font-medium">{log.task_name}</TableCell>
                            <TableCell>{log.freelancer_name}</TableCell>
                            <TableCell>
                                <Badge variant={log.status === 'paid' ? 'secondary' : 'default'} 
                                       className={log.status === 'paid' ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"}>
                                    {log.status}
                                </Badge>
                            </TableCell>
                            <TableCell className="text-right">{log.total_hours.toFixed(1)}</TableCell>
                            <TableCell className="text-right font-medium">${log.total_amount.toLocaleString()}</TableCell>
                            <TableCell className="text-right">
                                <Dialog>
                                    <DialogTrigger asChild><Button variant="ghost" size="sm" className="h-8 p-0 text-primary underline">View</Button></DialogTrigger>
                                    <DialogContent>
                                        <DialogHeader><DialogTitle>{log.task_name}</DialogTitle><DialogDescription>Details for {log.freelancer_name}</DialogDescription></DialogHeader>
                                        <div className="py-4">
                                            <div className="rounded-md border divide-y max-h-[200px] overflow-y-auto">
                                                {/* CHECK FOR EMPTY HISTORY */}
                                                {(!log.time_entries || log.time_entries.length === 0) ? (
                                                    <div className="p-4 text-center text-sm text-gray-500">
                                                        No time history available. <br/>
                                                        (Backend may need restart)
                                                    </div>
                                                ) : (
                                                    log.time_entries.map((entry, i) => (
                                                        <div key={i} className="p-3 text-sm grid grid-cols-3">
                                                            <span className="text-muted-foreground">{String(entry.date)}</span>
                                                            <span className="truncate">{entry.description}</span>
                                                            <span className="text-right font-mono">{entry.hours}h</span>
                                                        </div>
                                                    ))
                                                )}
                                            </div>
                                            <div className="mt-4 flex justify-between font-bold text-lg">
                                                <span>Total</span><span>${log.total_amount.toLocaleString()}</span>
                                            </div>
                                        </div>
                                    </DialogContent>
                                </Dialog>
                            </TableCell>
                        </TableRow>
                    ))
                )}
            </TableBody>
        </Table>
      </div>

      <Dialog open={isBatchModalOpen} onOpenChange={setIsBatchModalOpen}>
        <DialogContent>
            <DialogHeader><DialogTitle>Confirm Payment</DialogTitle></DialogHeader>
            <div className="py-6 text-center text-4xl font-bold text-green-600">${pendingAmount.toLocaleString()}</div>
            <DialogFooter>
                <Button variant="outline" onClick={() => setIsBatchModalOpen(false)}>Cancel</Button>
                <Button onClick={handleBatchPay}>Confirm</Button>
            </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}