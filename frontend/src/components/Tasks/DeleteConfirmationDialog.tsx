import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"

interface DeleteConfirmationDialogProps {
  open: boolean
  onConfirm: () => void | Promise<void>
  onCancel: () => void
  taskCount: number
  worklogCount: number
}

export const DeleteConfirmationDialog = ({
  open,
  onConfirm,
  onCancel,
  taskCount,
  worklogCount,
}: DeleteConfirmationDialogProps) => {
  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Confirm Deletion</DialogTitle>
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
              <p className="text-sm text-destructive pt-4">
                This action cannot be undone. All selected items will be permanently deleted.
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={onConfirm}>
            Delete Permanently
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
