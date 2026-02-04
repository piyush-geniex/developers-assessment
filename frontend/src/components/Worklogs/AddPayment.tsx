import { zodResolver } from "@hookform/resolvers/zod"
import { Plus } from "lucide-react"
import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import axios from "axios"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const formSchema = z.object({
  start_date: z.string().optional(),
  end_date: z.string().optional(),
})

type FormData = z.infer<typeof formSchema>

interface AddPaymentProps {
  onSuccess?: () => void
}

const AddPayment = ({ onSuccess }: AddPaymentProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [worklogs, setWorklogs] = useState<any[]>([])
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [loadingWorklogs, setLoadingWorklogs] = useState(false)

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      start_date: "",
      end_date: "",
    },
  })

  const fetchWorklogs = (startDate?: string, endDate?: string) => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    const params = new URLSearchParams()
    if (startDate) params.append("start_date", startDate)
    if (endDate) params.append("end_date", endDate)

    setLoadingWorklogs(true)
    axios
      .get(`${apiUrl}/api/v1/worklogs/payment-eligible/list?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      .then((response) => {
        setWorklogs(response.data || [])
        setLoadingWorklogs(false)
      })
      .catch((err) => {
        console.error("Failed to load worklogs:", err)
        setLoadingWorklogs(false)
      })
  }

  useEffect(() => {
    if (isOpen) {
      fetchWorklogs()
    }
  }, [isOpen])

  const handleSelect = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  const handleFilter = (data: FormData) => {
    fetchWorklogs(data.start_date, data.end_date)
  }

  const onSubmit = async () => {
    if (selectedIds.size === 0) {
      alert("Please select at least one worklog to process payment")
      return
    }

    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
    const token = localStorage.getItem("access_token")

    setLoading(true)
    try {
      await axios.post(
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
      alert("Payment processed successfully")
      form.reset()
      setSelectedIds(new Set())
      setIsOpen(false)
      if (onSuccess) {
        onSuccess()
      }
    } catch (error: any) {
      console.error("Failed to process payment:", error)
      const errorMessage = error.response?.data?.detail || "Failed to process payment. Please try again."
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const selectedWorklogs = worklogs.filter((wl) => selectedIds.has(wl.id))
  const totalAmount = selectedWorklogs.reduce((sum, wl) => sum + wl.amount_earned, 0)

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button aria-label="Add new payment batch">
          <Plus />
          Add Payment
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Process Payment Batch</DialogTitle>
          <DialogDescription>
            Select unpaid worklogs to process payment.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleFilter)}>
            <div className="grid grid-cols-2 gap-4 py-4">
              <FormField
                control={form.control}
                name="start_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Start Date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="end_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>End Date</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <Button type="submit" variant="outline" disabled={loadingWorklogs}>
              Filter
            </Button>
          </form>
        </Form>

        <div className="mt-4">
          {loadingWorklogs ? (
            <div className="text-center py-4">Loading worklogs...</div>
          ) : worklogs.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">
              No unpaid worklogs found
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50px]">Select</TableHead>
                    <TableHead>Task</TableHead>
                    <TableHead>Freelancer</TableHead>
                    <TableHead>Hours</TableHead>
                    <TableHead>Amount</TableHead>
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
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {selectedIds.size > 0 && (
                <div className="bg-muted p-4 rounded-lg mt-4">
                  <p className="text-sm">
                    <span className="font-medium">Selected:</span> {selectedIds.size} worklogs
                  </p>
                  <p className="text-sm">
                    <span className="font-medium">Total Amount:</span> ${totalAmount.toFixed(2)}
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" disabled={loading}>
              Cancel
            </Button>
          </DialogClose>
          <LoadingButton
            onClick={onSubmit}
            loading={loading}
            disabled={selectedIds.size === 0}
          >
            Process Payment
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default AddPayment
