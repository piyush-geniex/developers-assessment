import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, Clock } from "lucide-react";
import { Suspense } from "react";

import { WorklogsService } from "@/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function getTaskDetailQueryOptions(taskId: string) {
  return {
    queryFn: () => WorklogsService.getWorklogDetail({ taskId: parseInt(taskId) }),
    queryKey: ["worklog", taskId],
  };
}

export const Route = createFileRoute("/_layout/worklogs/$taskId")({
  component: WorklogDetail,
  head: () => ({
    meta: [
      {
        title: "Task Details - FastAPI Cloud",
      },
    ],
  }),
});

function TaskDetailContent() {
  const { taskId } = Route.useParams();
  const { data: taskData } = useSuspenseQuery(getTaskDetailQueryOptions(taskId));

  if (!taskData) {
    return (
      <div className="flex flex-col gap-6">
        <Link to="/worklogs">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Worklogs
          </Button>
        </Link>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Task not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Link to="/worklogs">
        <Button variant="ghost" size="sm">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Worklogs
        </Button>
      </Link>

      <div>
        <h1 className="text-2xl font-bold tracking-tight">{taskData.name}</h1>
        <p className="text-muted-foreground">{taskData.description || "No description"}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Total Hours</CardTitle>
            <CardDescription>Logged time for this task</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{taskData.total_hours.toFixed(2)}h</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Total Amount</CardTitle>
            <CardDescription>Total earnings for this task</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">${taskData.total_amount.toFixed(2)}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Time Entries</CardTitle>
          <CardDescription>
            {taskData.entries.length} entr{taskData.entries.length !== 1 ? "ies" : "y"} logged
          </CardDescription>
        </CardHeader>
        <CardContent>
          {taskData.entries.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No time entries</h3>
              <p className="text-muted-foreground">No time has been logged for this task yet</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Freelancer</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Hours</TableHead>
                  <TableHead className="text-right">Rate</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Logged At</TableHead>
                  <TableHead>Created At</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {taskData.entries.map((entry: any) => (
                  <TableRow key={entry.id}>
                    <TableCell className="font-medium">{entry.freelancer_name}</TableCell>
                    <TableCell>
                      {entry.payment_status === "paid" ? (
                        <div className="flex flex-col gap-1">
                          <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                            Paid
                          </span>
                          {entry.payment_batch_id && (
                            <span className="text-xs text-muted-foreground font-mono">
                              {entry.payment_batch_id}
                            </span>
                          )}
                          {entry.paid_at && (
                            <span className="text-xs text-muted-foreground">{entry.paid_at}</span>
                          )}
                        </div>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
                          Unpaid
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">{entry.hours.toFixed(2)}h</TableCell>
                    <TableCell className="text-right">${entry.hourly_rate.toFixed(2)}/h</TableCell>
                    <TableCell className="text-right font-medium">
                      ${entry.amount.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {entry.description || "-"}
                    </TableCell>
                    <TableCell className="font-mono text-sm">{entry.logged_at}</TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">
                      {entry.created_at}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function WorklogDetail() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-12">
          <Skeleton className="h-64 w-full" />
        </div>
      }
    >
      <TaskDetailContent />
    </Suspense>
  );
}

export default WorklogDetail;
