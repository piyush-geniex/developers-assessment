import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface DateRangeFilterProps {
  onFilter: (dateFrom: string, dateTo: string) => void
}

export default function DateRangeFilter({ onFilter }: DateRangeFilterProps) {
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")

  const handleApply = () => {
    if (dateFrom && dateTo) {
      onFilter(dateFrom, dateTo)
    }
  }

  return (
    <div className="border rounded-lg p-4 bg-muted/20">
      <h3 className="font-semibold mb-3">Filter by Date Range</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="dateFrom">From Date</Label>
          <Input
            id="dateFrom"
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="dateTo">To Date</Label>
          <Input
            id="dateTo"
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>
      </div>
      <Button onClick={handleApply} className="mt-4">
        Apply Filter
      </Button>
    </div>
  )
}
