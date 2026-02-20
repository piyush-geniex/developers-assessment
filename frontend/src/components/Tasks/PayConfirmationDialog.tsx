import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

interface PayConfirmationDialogProps {
  open: boolean
  onConfirm: () => void | Promise<void>
  onCancel: () => void
  taskCount: number
  worklogCount: number
  totalAmount: number
}

export const PayConfirmationDialog = ({
  open,
  onConfirm,
  onCancel,
  taskCount,
  worklogCount,
  totalAmount,
}: PayConfirmationDialogProps) => {
  const formattedAmount = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(totalAmount)

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm Payment</DialogTitle>
          <DialogDescription>
            <div className="space-y-3 mt-4">
              <div className="flex justify-between border-b pb-2">
                <span className="text-sm font-medium">Tasks:</span>
                <span className="text-sm">{taskCount}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-sm font-medium">Work Logs:</span>
                <span className="text-sm">{worklogCount}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span className="text-base font-semibold">Total Amount:</span>
                <span className="text-base font-semibold text-green-600">
                  {formattedAmount}
                </span>
              </div>
              <p className="text-sm text-muted-foreground pt-4">
                Are you sure you want to proceed with this payment?
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={onConfirm}>Confirm Payment</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
