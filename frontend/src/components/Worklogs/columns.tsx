import type { ColumnDef } from "@tanstack/react-table"

export type WorkLogPublic = {
    id: number
    freelancer_id: number
    task_name: string
    total_hours: number
    hourly_rate: number
    total_earned: number
    status: string
    created_at: string
}

export const columns: ColumnDef<WorkLogPublic>[] = [
    {
        accessorKey: "task_name",
        header: "Task Name",
        cell: ({ row }) => (
            <span className="font-medium">{row.original.task_name}</span>
        ),
    },
    {
        accessorKey: "freelancer_id",
        header: "Freelancer ID",
        cell: ({ row }) => (
            <span className="text-muted-foreground">{row.original.freelancer_id}</span>
        ),
    },
    {
        accessorKey: "total_hours",
        header: "Hours",
        cell: ({ row }) => (
            <span>{row.original.total_hours.toFixed(2)}</span>
        ),
    },
    {
        accessorKey: "hourly_rate",
        header: "Rate",
        cell: ({ row }) => (
            <span>${row.original.hourly_rate.toFixed(2)}</span>
        ),
    },
    {
        accessorKey: "total_earned",
        header: "Total",
        cell: ({ row }) => (
            <span className="font-medium">${row.original.total_earned.toFixed(2)}</span>
        ),
    },
    {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
            const status = row.original.status
            const colors = {
                PAID: "bg-green-100 text-green-800",
                EXCLUDED: "bg-gray-100 text-gray-800",
                PENDING: "bg-yellow-100 text-yellow-800",
            }
            return (
                <span className={`px-2 py-1 rounded text-xs ${colors[status as keyof typeof colors] || colors.PENDING}`}>
                    {status}
                </span>
            )
        },
    },
    {
        id: "actions",
        header: () => <span className="sr-only">Actions</span>,
        cell: ({ row }) => (
            <div className="flex justify-end">
                <a
                    href={`/worklog-detail?id=${row.original.id}`}
                    className="text-primary hover:underline text-sm"
                >
                    View Details
                </a>
            </div>
        ),
    },
]
