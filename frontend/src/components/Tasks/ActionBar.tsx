import { useState } from "react"
import { Trash2, DollarSign } from "lucide-react"
import { Button } from "@/components/ui/button"
import { TasksService } from "@/client"
import { useTaskSelection } from "./TaskSelectionContext"
import { PayConfirmationDialog } from "./PayConfirmationDialog"
import { DeleteConfirmationDialog } from "./DeleteConfirmationDialog"

export const ActionBar = ({
  onSelectAll,
  onSelectNone,
  onDeleteSelected,
  onPaySelected,
  tasks,
}: {
  onSelectAll: (taskIds: string[]) => void
  onSelectNone: () => void
  onDeleteSelected: () => void
  onPaySelected: () => void
  tasks: { id: string }[]
}) => {
  const { selectedTasks, selectedWorklogs } = useTaskSelection()
  const [showPayDialog, setShowPayDialog] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [paymentData, setPaymentData] = useState<{
    taskCount: number
    worklogCount: number
    totalAmount: number
  } | null>(null)

  const hasTasksSelected = Object.values(selectedTasks).some(Boolean)
  const hasWorklogsSelected = Object.values(selectedWorklogs).some(Boolean)
  const hasSelection = hasTasksSelected || hasWorklogsSelected

  if (!hasSelection) {
    return null
  }

  const selectedTaskCount = Object.values(selectedTasks).filter(Boolean).length
  const selectedWorklogCount = Object.values(selectedWorklogs).filter(Boolean).length

  const handlePayClick = async () => {
    // Calculate total amount from selected worklogs
    let totalAmount = 0
    
    // Get all task IDs with selected worklogs
    const taskIdsWithWorklogs = Object.keys(selectedTasks).filter(taskId => selectedTasks[taskId])
    
    // For each task, get its worklogs and sum amounts of selected ones
    for (const taskId of taskIdsWithWorklogs) {
      try {
        const response = await TasksService.readWorkLogs({ taskId })
        const worklogs = response.data || []
        worklogs.forEach((log) => {
          if (selectedWorklogs[log.id]) {
            totalAmount += Number(log.amount)
          }
        })
      } catch (error) {
        console.error(`Failed to fetch worklogs for task ${taskId}:`, error)
      }
    }

    setPaymentData({
      taskCount: selectedTaskCount,
      worklogCount: selectedWorklogCount,
      totalAmount,
    })
    setShowPayDialog(true)
  }

  const handlePayConfirm = async () => {
    setShowPayDialog(false)
    onPaySelected()
  }

  const handleDeleteClick = () => {
    setShowDeleteDialog(true)
  }

  const handleDeleteConfirm = async () => {
    setShowDeleteDialog(false)
    onDeleteSelected()
  }

  return (
    <>
      <div className="flex items-center justify-between gap-4 p-4 bg-muted rounded-lg border mb-4">
        <div className="text-sm text-muted-foreground">
          {selectedTaskCount > 0 && <span>{selectedTaskCount} task(s) selected</span>}
          {selectedTaskCount > 0 && selectedWorklogCount > 0 && <span> | </span>}
          {selectedWorklogCount > 0 && <span>{selectedWorklogCount} worklog(s) selected</span>}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onSelectAll(tasks.map((t) => t.id))}
          >
            Select All
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={onSelectNone}
            disabled={!hasSelection}
          >
            Select None
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDeleteClick}
            disabled={!hasSelection}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete Selected
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={handlePayClick}
            disabled={!hasWorklogsSelected}
          >
            <DollarSign className="h-4 w-4 mr-2" />
            Pay Selected
          </Button>
        </div>
      </div>

      {paymentData && (
        <PayConfirmationDialog
          open={showPayDialog}
          onConfirm={handlePayConfirm}
          onCancel={() => setShowPayDialog(false)}
          taskCount={paymentData.taskCount}
          worklogCount={paymentData.worklogCount}
          totalAmount={paymentData.totalAmount}
        />
      )}

      <DeleteConfirmationDialog
        open={showDeleteDialog}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setShowDeleteDialog(false)}
        taskCount={selectedTaskCount}
        worklogCount={selectedWorklogCount}
      />
    </>
  )
}
