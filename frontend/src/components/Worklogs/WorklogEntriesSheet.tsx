import { useQuery } from "@tanstack/react-query"
import { Clock, DollarSign, Eye } from "lucide-react"
import { useState } from "react"

import type { WorklogPublic } from "@/client"
import { WorklogsService } from "@/client"
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

function formatDate(isoString: string) {
  return new Date(isoString).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
}

function formatTime(isoString: string) {
  return new Date(isoString).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
  })
}

interface WorklogEntriesSheetProps {
  worklog: WorklogPublic
}

export function WorklogEntriesSheet({ worklog }: WorklogEntriesSheetProps) {
  const [open, setOpen] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ["worklog", worklog.id],
    queryFn: () => WorklogsService.readWorklog({ worklogId: worklog.id }),
    enabled: open,
  })

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`View time entries for ${worklog.title}`}
        >
          <Eye className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader className="mb-6">
          <SheetTitle className="text-xl">{worklog.title}</SheetTitle>
          <SheetDescription>
            {worklog.description || "No description provided."}
          </SheetDescription>
          <div className="flex items-center gap-4 pt-2 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {worklog.total_hours.toFixed(2)}h total
            </span>
            <span className="flex items-center gap-1">
              <DollarSign className="h-3.5 w-3.5" />
              ${worklog.total_earned.toFixed(2)} earned
            </span>
            <Badge variant="outline">${worklog.hourly_rate}/hr</Badge>
          </div>
        </SheetHeader>

        {isLoading && (
          <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
            Loading time entries…
          </div>
        )}

        {error && (
          <div className="py-8 text-center text-sm text-destructive">
            Failed to load time entries. Please try again.
          </div>
        )}

        {data && data.time_entries.length === 0 && (
          <div className="py-12 text-center text-sm text-muted-foreground">
            No time entries recorded for this worklog.
          </div>
        )}

        {data && data.time_entries.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Date</TableHead>
                <TableHead>Start</TableHead>
                <TableHead>End</TableHead>
                <TableHead className="text-right">Hours</TableHead>
                <TableHead>Description</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.time_entries.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell className="whitespace-nowrap text-sm">
                    {formatDate(entry.start_time)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatTime(entry.start_time)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatTime(entry.end_time)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {entry.hours.toFixed(2)}h
                  </TableCell>
                  <TableCell className="max-w-xs text-sm text-muted-foreground truncate">
                    {entry.description || "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SheetContent>
    </Sheet>
  )
}
