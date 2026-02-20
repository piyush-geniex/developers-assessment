import { X, Search as SearchIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface DateFilterProps {
  startDate: string | null
  endDate: string | null
  onStartDateChange: (date: string | null) => void
  onEndDateChange: (date: string | null) => void
  onReset: () => void
  onSearch: () => void
}

export function DateFilter({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  onReset,
  onSearch,
}: DateFilterProps) {
  const hasFilters = startDate || endDate

  return (
    <div className="flex items-end gap-3">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="start-date" className="text-sm font-medium">
          Start Date
        </Label>
        <Input
          id="start-date"
          type="date"
          value={startDate || ""}
          onChange={(e) => onStartDateChange(e.target.value || null)}
          className="w-40"
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="end-date" className="text-sm font-medium">
          End Date
        </Label>
        <Input
          id="end-date"
          type="date"
          value={endDate || ""}
          onChange={(e) => onEndDateChange(e.target.value || null)}
          className="w-40"
        />
      </div>

      <Button
        variant="default"
        size="sm"
        onClick={onSearch}
        className="gap-1.5"
      >
        <SearchIcon className="h-4 w-4" />
        Search
      </Button>

      {hasFilters && (
        <Button
          variant="outline"
          size="sm"
          onClick={onReset}
          className="gap-1.5"
        >
          <X className="h-4 w-4" />
          Clear
        </Button>
      )}
    </div>
  )
}

