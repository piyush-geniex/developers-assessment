import { useQuery } from "@tanstack/react-query"
import { Eye } from "lucide-react"
import { useState } from "react"

import type { EligibleEntry, PaymentBatchPublic } from "@/client"
import { PaymentsService } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
}

type FreelancerGroup = {
  freelancer_id: string
  freelancer_name: string | null
  totalHours: number
  totalAmount: number
  entries: EligibleEntry[]
}

function groupByFreelancer(lines: EligibleEntry[]): FreelancerGroup[] {
  const map = new Map<string, FreelancerGroup>()

  for (const line of lines) {
    const existing = map.get(line.freelancer_id)
    if (existing) {
      existing.totalHours += line.hours
      existing.totalAmount += line.amount
      existing.entries.push(line)
    } else {
      map.set(line.freelancer_id, {
        freelancer_id: line.freelancer_id,
        freelancer_name: line.freelancer_name ?? null,
        totalHours: line.hours,
        totalAmount: line.amount,
        entries: [line],
      })
    }
  }

  return Array.from(map.values())
}

function PaymentLinesTable({ lines }: { lines: EligibleEntry[] }) {
  const groups = groupByFreelancer(lines)
  const grandTotal = lines.reduce((s, e) => s + e.amount, 0)
  const grandHours = lines.reduce((s, e) => s + e.hours, 0)

  if (lines.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No payment records found for this batch.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {groups.map((group) => (
        <div key={group.freelancer_id} className="rounded-md border">
          <div className="flex items-center justify-between border-b bg-muted/40 px-4 py-2">
            <span className="font-medium text-sm">
              {group.freelancer_name ?? "Unknown"}
            </span>
            <span className="font-mono text-sm text-muted-foreground">
              {group.totalHours.toFixed(2)}h · ${group.totalAmount.toFixed(2)}
            </span>
          </div>
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Worklog</TableHead>
                <TableHead className="text-right">Hours</TableHead>
                <TableHead className="text-right">Rate</TableHead>
                <TableHead className="text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {group.entries.map((entry) => (
                <TableRow key={entry.time_entry_id}>
                  <TableCell className="text-sm">{entry.worklog_title}</TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {entry.hours.toFixed(2)}h
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm text-muted-foreground">
                    ${entry.hourly_rate.toFixed(2)}/hr
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm font-medium">
                    ${entry.amount.toFixed(2)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ))}

      <div className="flex items-center justify-between rounded-md bg-muted/50 px-4 py-2 text-sm">
        <span className="text-muted-foreground">
          {groups.length} freelancer{groups.length !== 1 ? "s" : ""} · {lines.length} entries
        </span>
        <span className="font-mono font-semibold">
          {grandHours.toFixed(2)}h · ${grandTotal.toFixed(2)}
        </span>
      </div>
    </div>
  )
}

function BatchDetailContent({ batchId }: { batchId: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["payment-batch", batchId],
    queryFn: () => PaymentsService.readBatch({ batchId }),
  })

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3 pt-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    )
  }

  if (isError || !data) {
    return (
      <p className="pt-4 text-sm text-destructive">
        Failed to load batch details.
      </p>
    )
  }

  const lines = data.payment_lines ?? []

  return (
    <div className="flex flex-col gap-6 pt-2">
      <dl className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-muted-foreground">Period</dt>
          <dd className="font-medium">
            {formatDate(data.date_from)} – {formatDate(data.date_to)}
          </dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Status</dt>
          <dd>
            <Badge variant={data.status === "confirmed" ? "default" : "secondary"}>
              {data.status.charAt(0).toUpperCase() + data.status.slice(1)}
            </Badge>
          </dd>
        </div>
        {data.total_amount != null && (
          <div className="col-span-2">
            <dt className="text-muted-foreground">Total Payout</dt>
            <dd className="font-mono text-lg font-bold">
              ${data.total_amount.toFixed(2)}
            </dd>
          </div>
        )}
      </dl>

      <div>
        <h4 className="text-sm font-semibold mb-3">
          {data.status === "confirmed" ? "Payments Made" : "Eligible Entries"}
        </h4>
        {data.status === "confirmed" ? (
          <PaymentLinesTable lines={lines} />
        ) : (
          <p className="text-sm text-muted-foreground">
            This batch is still a draft. Confirm it to see the final payment breakdown.
          </p>
        )}
      </div>
    </div>
  )
}

interface BatchDetailSheetProps {
  batch: PaymentBatchPublic
}

export function BatchDetailSheet({ batch }: BatchDetailSheetProps) {
  const [open, setOpen] = useState(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`View details for batch ${batch.id}`}
        >
          <Eye className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Batch Details</SheetTitle>
          <SheetDescription>
            {formatDate(batch.date_from)} – {formatDate(batch.date_to)}
          </SheetDescription>
        </SheetHeader>
        {open && <BatchDetailContent batchId={batch.id} />}
      </SheetContent>
    </Sheet>
  )
}
