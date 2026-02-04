
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { useState } from "react"
import type { ColumnDef } from "@tanstack/react-table"
import { MoreHorizontal, CalendarIcon } from "lucide-react"

import { WorkLogService, type WorkLogPublic } from "@/client/WorkLogService"
import { Button } from "@/components/ui/button"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Checkbox } from "@/components/ui/checkbox"
import { Calendar } from "@/components/ui/calendar"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { format } from "date-fns"
import useCustomToast from "@/hooks/useCustomToast"

// --- Columns ---
const columns: ColumnDef<WorkLogPublic>[] = [
    {
        id: "select",
        header: ({ table }) => (
            <Checkbox
                checked={
                    table.getIsAllPageRowsSelected() ||
                    (table.getIsSomePageRowsSelected() && "indeterminate")
                }
                onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
                aria-label="Select all"
            />
        ),
        cell: ({ row }) => (
            <Checkbox
                checked={row.getIsSelected()}
                onCheckedChange={(value) => row.toggleSelected(!!value)}
                aria-label="Select row"
            />
        ),
        enableSorting: false,
        enableHiding: false,
    },
    {
        accessorKey: "task_name",
        header: "Task",
        cell: ({ row }) => <div className="font-medium">{row.getValue("task_name")}</div>,
    },
    {
        accessorKey: "total_duration_hours",
        header: "Hours",
        cell: ({ row }) => <div>{row.getValue("total_duration_hours")}</div>,
    },
    {
        accessorKey: "total_amount",
        header: "Amount ($)",
        cell: ({ row }) => <div>{row.getValue("total_amount")}</div>,
    },
    {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => (
            <div className={cn(
                "font-medium capitalize",
                row.getValue("status") === "paid" ? "text-green-600" : "text-amber-600"
            )}>
                {row.getValue("status")}
            </div>
        ),
    },
    {
        accessorKey: "created_at",
        header: "Date",
        cell: ({ row }) => <div>{new Date(row.getValue("created_at")).toLocaleDateString()}</div>,
    },
    {
        id: "actions",
        cell: ({ row }) => {
            const worklog = row.original

            return (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                            <span className="sr-only">Open menu</span>
                            <MoreHorizontal className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Actions</DropdownMenuLabel>
                        <DropdownMenuItem asChild>
                            <Link to="/worklogs/$workLogId" params={{ workLogId: worklog.id }}>View Details</Link>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            )
        },
    },
]

export const Route = createFileRoute("/_layout/worklogs")({
    component: WorkLogs,
})

function WorkLogs() {
    const [date, setDate] = useState<Date | undefined>(undefined)

    // Fetch Logic
    const { data: worklogsData, isLoading } = useQuery({
        queryKey: ["worklogs", date],
        queryFn: () => WorkLogService.readWorkLogs({
            date_from: date ? date.toISOString() : undefined,
            // For simplicity, just filtering by start date if selected. 
            // Ideally we'd have a range picker.
        }),
    })

    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">WorkLogs</h1>
                    <p className="text-muted-foreground">Manage freelancer worklogs and payments</p>
                </div>

                <div className="flex gap-2">
                    <Popover>
                        <PopoverTrigger asChild>
                            <Button
                                variant={"outline"}
                                className={cn(
                                    "w-[240px] justify-start text-left font-normal",
                                    !date && "text-muted-foreground"
                                )}
                            >
                                <CalendarIcon className="mr-2 h-4 w-4" />
                                {date ? format(date, "PPP") : <span>Filter by Date (from)</span>}
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                            <Calendar
                                mode="single"
                                selected={date}
                                onSelect={setDate}
                                initialFocus
                            />
                        </PopoverContent>
                    </Popover>
                    {/* Payment Button and Selection logic will be added after checking DataTable */}
                </div>
            </div>

            {isLoading ? (
                <div>Loading...</div>
            ) : (
                <WorkLogsTable data={worklogsData?.data || []} />
            )}
        </div>
    )
}

// I'll create a local table wrapper that supports selection, 
// ignoring the shared DataTable for now to ensure I have control over selection.
// Or I'll write the table using shadcn-ui components directly here.

import {
    flexRender,
    getCoreRowModel,
    useReactTable,
} from "@tanstack/react-table"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog"

function WorkLogsTable({ data }: { data: WorkLogPublic[] }) {
    const [rowSelection, setRowSelection] = useState({})
    const queryClient = useQueryClient()
    const { showSuccessToast, showErrorToast } = useCustomToast()

    const payMutation = useMutation({
        mutationFn: (ids: string[]) => WorkLogService.payWorkLogs(ids),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["worklogs"] })
            setRowSelection({})
            showSuccessToast("Payments processed successfully!")
        },
        onError: () => {
            showErrorToast("Failed to process payments.")
        }
    })

    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        onRowSelectionChange: setRowSelection,
        state: {
            rowSelection,
        },
    })
    const [isConfirmOpen, setIsConfirmOpen] = useState(false)

    // Calculate totals for selected items
    const selectedRows = table.getFilteredSelectedRowModel().rows
    const selectedCount = selectedRows.length
    const totalAmount = selectedRows.reduce((sum, row) => sum + row.original.total_amount, 0)

    return (
        <div className="space-y-4">
            {selectedCount > 0 && (
                <div className="bg-muted p-2 rounded-md flex justify-between items-center">
                    <span>{selectedCount} selected</span>
                    <Button
                        size="sm"
                        onClick={() => setIsConfirmOpen(true)}
                        disabled={payMutation.isPending}
                    >
                        Pay Selected
                    </Button>
                </div>
            )}

            <Dialog open={isConfirmOpen} onOpenChange={setIsConfirmOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Confirm Payment</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to mark <strong>{selectedCount}</strong> worklogs as paid?
                            <br />
                            Total Amount: <strong>${totalAmount.toFixed(2)}</strong>
                        </DialogDescription>
                    </DialogHeader>
                    <div className="flex justify-end gap-2">
                        <Button variant="outline" onClick={() => setIsConfirmOpen(false)}>Cancel</Button>
                        <Button onClick={() => {
                            payMutation.mutate(selectedRows.map(r => r.original.id))
                            setIsConfirmOpen(false)
                        }}>
                            Confirm Payment
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>

            <div className="rounded-md border">
                <Table>
                    <TableHeader>
                        {table.getHeaderGroups().map((headerGroup) => (
                            <TableRow key={headerGroup.id}>
                                {headerGroup.headers.map((header) => {
                                    return (
                                        <TableHead key={header.id}>
                                            {header.isPlaceholder
                                                ? null
                                                : flexRender(
                                                    header.column.columnDef.header,
                                                    header.getContext()
                                                )}
                                        </TableHead>
                                    )
                                })}
                            </TableRow>
                        ))}
                    </TableHeader>
                    <TableBody>
                        {table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <TableRow
                                    key={row.id}
                                    data-state={row.getIsSelected() && "selected"}
                                >
                                    {row.getVisibleCells().map((cell) => (
                                        <TableCell key={cell.id}>
                                            {flexRender(
                                                cell.column.columnDef.cell,
                                                cell.getContext()
                                            )}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell
                                    colSpan={columns.length}
                                    className="h-24 text-center"
                                >
                                    No results.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    )
}
