import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { X, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

const axios = require('axios').default
axios.defaults.baseURL = 'http://localhost:8000'

interface PaymentFlowProps {
  worklogIds: string[]
  onClose: () => void
}

export default function PaymentFlow({ worklogIds, onClose }: PaymentFlowProps) {
  const [step, setStep] = useState<'review' | 'confirm'>('review')
  const [batchName, setBatchName] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [excludedIds, setExcludedIds] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)

  const { data: worklogsData, isLoading } = useQuery({
    queryKey: ["paymentWorklogs", worklogIds],
    queryFn: async (): Promise<any> => {
      const token = localStorage.getItem('access_token')
      const response = await axios.get('http://localhost:8000/api/v1/worklogs/', {
        headers: { Authorization: `Bearer ${token}` },
        params: { skip: 0, limit: 100 }
      })
      return response.data.data.filter((wl: any) => worklogIds.includes(wl.id))
    },
  })

  const handleExclude = (id: string) => {
    if (excludedIds.includes(id)) {
      setExcludedIds(excludedIds.filter((wlId) => wlId !== id))
    } else {
      setExcludedIds([...excludedIds, id])
    }
  }

  const finalWorklogIds = worklogIds.filter((id) => !excludedIds.includes(id))
  const totalAmount = worklogsData
    ? worklogsData
        .filter((wl: any) => finalWorklogIds.includes(wl.id))
        .reduce((sum: number, wl: any) => sum + wl.total_amount, 0)
    : 0

  const handleConfirmPayment = async () => {
    try {
      setIsProcessing(true)
      const token = localStorage.getItem('access_token')

      const paymentResponse = await axios.post(
        'http://localhost:8000/api/v1/worklogs/payments/',
        {
          batch_name: batchName,
          date_from: dateFrom,
          date_to: dateTo,
          worklog_ids: finalWorklogIds,
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      await axios.post(
        `http://localhost:8000/api/v1/worklogs/payments/${paymentResponse.data.id}/confirm`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      alert('Payment processed successfully!')
      window.location.reload()
    } catch (error) {
      console.error('Failed to process payment:', error)
      alert('Failed to process payment. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  if (isLoading) {
    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {step === 'review' ? 'Review Payment Selection' : 'Confirm Payment'}
          </DialogTitle>
          <DialogDescription>
            {step === 'review'
              ? 'Review the worklogs included in this payment batch. You can exclude specific worklogs before proceeding.'
              : 'Enter payment batch details and confirm to process the payment.'}
          </DialogDescription>
        </DialogHeader>

        {step === 'review' && (
          <div>
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full border rounded">
                <thead className="bg-muted/50 sticky top-0">
                  <tr>
                    <th className="text-left p-2">Task</th>
                    <th className="text-left p-2">Freelancer</th>
                    <th className="text-left p-2">Amount</th>
                    <th className="text-left p-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {worklogsData?.map((wl: any) => (
                    <tr
                      key={wl.id}
                      className={`border-t ${
                        excludedIds.includes(wl.id) ? 'bg-red-50 opacity-50' : ''
                      }`}
                    >
                      <td className="p-2">{wl.task_name}</td>
                      <td className="p-2">{wl.freelancer_id}</td>
                      <td className="p-2">${wl.total_amount.toFixed(2)}</td>
                      <td className="p-2">
                        <Button
                          variant={excludedIds.includes(wl.id) ? 'default' : 'ghost'}
                          size="sm"
                          onClick={() => handleExclude(wl.id)}
                        >
                          {excludedIds.includes(wl.id) ? 'Include' : 'Exclude'}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 p-4 bg-muted/20 rounded">
              <div className="flex justify-between items-center">
                <span className="font-semibold">Total Amount:</span>
                <span className="text-2xl font-bold">${totalAmount.toFixed(2)}</span>
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                {finalWorklogIds.length} worklog(s) selected
              </div>
            </div>
          </div>
        )}

        {step === 'confirm' && (
          <div className="space-y-4">
            <div>
              <Label htmlFor="batchName">Batch Name</Label>
              <Input
                id="batchName"
                placeholder="e.g., January 2026 Payment"
                value={batchName}
                onChange={(e) => setBatchName(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="dateFrom">Date From</Label>
                <Input
                  id="dateFrom"
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="dateTo">Date To</Label>
                <Input
                  id="dateTo"
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>
            </div>

            <div className="p-4 bg-muted/20 rounded">
              <div className="flex justify-between items-center">
                <span className="font-semibold">Total Amount:</span>
                <span className="text-2xl font-bold">${totalAmount.toFixed(2)}</span>
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                {finalWorklogIds.length} worklog(s) will be paid
              </div>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose} disabled={isProcessing}>
            Cancel
          </Button>
          {step === 'review' && (
            <Button onClick={() => setStep('confirm')} disabled={finalWorklogIds.length === 0}>
              Continue
            </Button>
          )}
          {step === 'confirm' && (
            <>
              <Button variant="ghost" onClick={() => setStep('review')} disabled={isProcessing}>
                Back
              </Button>
              <Button
                onClick={handleConfirmPayment}
                disabled={!batchName || !dateFrom || !dateTo || isProcessing}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Confirm Payment'
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
