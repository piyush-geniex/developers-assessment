import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const PendingWorklogs = () => (
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Task Name</TableHead>
        <TableHead>Description</TableHead>
        <TableHead className="text-right">Total Hours</TableHead>
        <TableHead className="text-right">Total Amount</TableHead>
        <TableHead className="text-right">Entries</TableHead>
        <TableHead className="text-right">Actions</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {Array.from({ length: 5 }).map((_, index) => (
        <TableRow key={index}>
          <TableCell>
            <Skeleton className="h-4 w-32" />
          </TableCell>
          <TableCell>
            <Skeleton className="h-4 w-48" />
          </TableCell>
          <TableCell className="text-right">
            <Skeleton className="h-4 w-16 ml-auto" />
          </TableCell>
          <TableCell className="text-right">
            <Skeleton className="h-4 w-20 ml-auto" />
          </TableCell>
          <TableCell className="text-right">
            <Skeleton className="h-4 w-8 ml-auto" />
          </TableCell>
          <TableCell className="text-right">
            <Skeleton className="h-8 w-24 ml-auto rounded-md" />
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
);

export default PendingWorklogs;
