import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Calendar, Clock, DollarSign, X } from "lucide-react";
import { Suspense, useState, useEffect } from "react";

import { WorklogsService } from "@/client";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PendingWorklogs from "@/components/Pending/PendingWorklogs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function getWorklogsQueryOptions(dtFrom?: string, dtTo?: string) {
  return {
    queryFn: () => WorklogsService.listWorklogs({ dtFrom, dtTo }),
    queryKey: ["worklogs", dtFrom, dtTo],
  };
}

function getThisWeekDates() {
  const now = new Date();
  const dayOfWeek = now.getDay();
  const monday = new Date(now);
  monday.setDate(now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1));
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  return {
    from: monday.toISOString().split("T")[0],
    to: sunday.toISOString().split("T")[0],
  };
}

function getThisMonthDates() {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return {
    from: firstDay.toISOString().split("T")[0],
    to: lastDay.toISOString().split("T")[0],
  };
}

export const Route = createFileRoute("/_layout/worklogs/")({
  component: WorklogsList,
  head: () => ({
    meta: [
      {
        title: "Worklogs - FastAPI Cloud",
      },
    ],
  }),
});

function WorklogsTableContent({
  dtFrom,
  dtTo,
  selectedTasks,
  onToggleTask,
  onToggleAll,
}: {
  dtFrom?: string;
  dtTo?: string;
  selectedTasks: Set<number>;
  onToggleTask: (taskId: number) => void;
  onToggleAll: () => void;
}) {
  const { data: worklogs } = useSuspenseQuery(getWorklogsQueryOptions(dtFrom, dtTo));

  if (!worklogs.data || worklogs.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Clock className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No worklogs found</h3>
        <p className="text-muted-foreground">Check back later for task updates</p>
      </div>
    );
  }

  const allTaskIds = worklogs.data.map((task: any) => task.id);
  const allSelected =
    allTaskIds.length > 0 && allTaskIds.every((id: number) => selectedTasks.has(id));

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12">
            <Checkbox
              checked={allSelected}
              onCheckedChange={onToggleAll}
              aria-label="Select all tasks"
            />
          </TableHead>
          <TableHead>Task Name</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Total Hours</TableHead>
          <TableHead className="text-right">Total Amount</TableHead>
          <TableHead className="text-right">Entries</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {worklogs.data.map((task: any) => {
          const isSelected = selectedTasks.has(task.id);
          return (
            <TableRow key={task.id} className={isSelected ? "bg-muted/50" : ""}>
              <TableCell>
                <Checkbox
                  checked={isSelected}
                  onCheckedChange={() => onToggleTask(task.id)}
                  aria-label={`Select ${task.name}`}
                />
              </TableCell>
              <TableCell className="font-medium">{task.name}</TableCell>
              <TableCell className="text-muted-foreground">{task.description || "-"}</TableCell>
              <TableCell>
                {task.payment_status === "paid" && (
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    Paid
                  </span>
                )}
                {task.payment_status === "unpaid" && (
                  <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
                    Unpaid
                  </span>
                )}
                {task.payment_status === "partial" && (
                  <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                    Partial
                  </span>
                )}
              </TableCell>
              <TableCell className="text-right">{task.total_hours.toFixed(2)}h</TableCell>
              <TableCell className="text-right font-medium">
                ${task.total_amount.toFixed(2)}
              </TableCell>
              <TableCell className="text-right">{task.entry_count}</TableCell>
              <TableCell className="text-right">
                <Link to="/worklogs/$taskId" params={{ taskId: String(task.id) }}>
                  <Button variant="outline" size="sm">
                    View Details
                  </Button>
                </Link>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

function WorklogsTable({
  dtFrom,
  dtTo,
  selectedTasks,
  onToggleTask,
  onToggleAll,
}: {
  dtFrom?: string;
  dtTo?: string;
  selectedTasks: Set<number>;
  onToggleTask: (taskId: number) => void;
  onToggleAll: () => void;
}) {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <WorklogsTableContent
        dtFrom={dtFrom}
        dtTo={dtTo}
        selectedTasks={selectedTasks}
        onToggleTask={onToggleTask}
        onToggleAll={onToggleAll}
      />
    </Suspense>
  );
}

function WorklogsList() {
  const [filterType, setFilterType] = useState<string>("all");
  const [customFrom, setCustomFrom] = useState<string>("");
  const [customTo, setCustomTo] = useState<string>("");
  const [selectedTasks, setSelectedTasks] = useState<Set<number>>(new Set());
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviewTasks, setReviewTasks] = useState<Set<number>>(new Set());
  const [excludedPairs, setExcludedPairs] = useState<Set<string>>(new Set());

  let dtFrom: string | undefined;
  let dtTo: string | undefined;

  if (filterType === "week") {
    const dates = getThisWeekDates();
    dtFrom = dates.from;
    dtTo = dates.to;
  } else if (filterType === "month") {
    const dates = getThisMonthDates();
    dtFrom = dates.from;
    dtTo = dates.to;
  } else if (filterType === "custom") {
    dtFrom = customFrom || undefined;
    dtTo = customTo || undefined;
  }

  const { data: allWorklogs } = useSuspenseQuery(getWorklogsQueryOptions(dtFrom, dtTo));

  const toggleTask = (taskId: number) => {
    setSelectedTasks((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const toggleAll = () => {
    if (allWorklogs?.data) {
      const allTaskIds = allWorklogs.data.map((task: any) => task.id);
      const allSelected = allTaskIds.every((id: number) => selectedTasks.has(id));

      if (allSelected) {
        setSelectedTasks(new Set());
      } else {
        setSelectedTasks(new Set(allTaskIds));
      }
    }
  };

  const selectedTasksData =
    allWorklogs?.data?.filter((task: any) => selectedTasks.has(task.id)) || [];
  const totalSelectedAmount = selectedTasksData.reduce(
    (sum: number, task: any) => sum + task.total_amount,
    0,
  );
  const totalSelectedHours = selectedTasksData.reduce(
    (sum: number, task: any) => sum + task.total_hours,
    0,
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Worklogs</h1>
        <p className="text-muted-foreground">View and manage freelancer work logs and earnings</p>
      </div>

      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-muted-foreground" />
          <span className="text-sm font-medium">Filter by Date Range</span>
        </div>

        <Tabs value={filterType} onValueChange={setFilterType}>
          <TabsList>
            <TabsTrigger value="all">All Time</TabsTrigger>
            <TabsTrigger value="week">This Week</TabsTrigger>
            <TabsTrigger value="month">This Month</TabsTrigger>
            <TabsTrigger value="custom">Custom Range</TabsTrigger>
          </TabsList>
        </Tabs>

        {filterType === "custom" && (
          <div className="flex gap-4 items-center">
            <div className="flex flex-col gap-2">
              <label className="text-sm text-muted-foreground">From</label>
              <Input
                type="date"
                value={customFrom}
                onChange={(e) => setCustomFrom(e.target.value)}
                className="w-48"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-sm text-muted-foreground">To</label>
              <Input
                type="date"
                value={customTo}
                onChange={(e) => setCustomTo(e.target.value)}
                className="w-48"
              />
            </div>
          </div>
        )}
      </div>

      {selectedTasks.size > 0 && (
        <div className="sticky bottom-0 bg-background border-t border-border p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm text-muted-foreground">Selected for Payment</p>
                  <p className="text-2xl font-bold">${totalSelectedAmount.toFixed(2)}</p>
                </div>
              </div>
              <div className="border-l pl-6">
                <p className="text-sm text-muted-foreground">
                  {selectedTasks.size} task{selectedTasks.size !== 1 ? "s" : ""} ·{" "}
                  {totalSelectedHours.toFixed(1)} hours
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setSelectedTasks(new Set())}>
                Clear Selection
              </Button>
              <Button
                onClick={() => {
                  setReviewTasks(new Set(selectedTasks));
                  setExcludedPairs(new Set());
                  setShowReviewDialog(true);
                }}
              >
                Review Payment
              </Button>
            </div>
          </div>
        </div>
      )}

      <WorklogsTable
        dtFrom={dtFrom}
        dtTo={dtTo}
        selectedTasks={selectedTasks}
        onToggleTask={toggleTask}
        onToggleAll={toggleAll}
      />

      <PaymentReviewDialog
        open={showReviewDialog}
        onOpenChange={setShowReviewDialog}
        tasks={allWorklogs?.data || []}
        selectedTaskIds={reviewTasks}
        excludedPairs={excludedPairs}
        onRemoveTaskFromFreelancer={(taskId, freelancerId) => {
          setExcludedPairs((prev) => {
            const newSet = new Set(prev);
            newSet.add(`${taskId}-${freelancerId}`);
            return newSet;
          });
        }}
        onConfirm={async () => {
          const taskIds = Array.from(reviewTasks);
          const batchId = `BATCH_${new Date().toISOString().split("T")[0]}_${Date.now()}`;

          try {
            await WorklogsService.markPaid({
              requestBody: {
                task_ids: taskIds,
                payment_batch_id: batchId,
              },
            });

            setShowReviewDialog(false);
            setSelectedTasks(new Set());
            setReviewTasks(new Set());

            window.location.reload();
          } catch (error) {
            console.error("Failed to mark as paid:", error);
            alert("Failed to mark worklogs as paid. Please try again.");
          }
        }}
      />
    </div>
  );
}

function PaymentReviewDialog({
  open,
  onOpenChange,
  tasks,
  selectedTaskIds,
  excludedPairs,
  onRemoveTaskFromFreelancer,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tasks: any[];
  selectedTaskIds: Set<number>;
  excludedPairs: Set<string>;
  onRemoveTaskFromFreelancer: (taskId: number, freelancerId: number) => void;
  onConfirm: () => void;
}) {
  const [taskDetails, setTaskDetails] = useState<Map<number, any>>(new Map());
  const [loading, setLoading] = useState(false);

  const selectedTasks = tasks.filter((task) => selectedTaskIds.has(task.id));

  // Fetch task details to get freelancer information
  useEffect(() => {
    if (open && selectedTasks.length > 0) {
      setLoading(true);
      Promise.all(
        selectedTasks.map((task) =>
          WorklogsService.getWorklogDetail({ taskId: task.id }).then((detail) => ({
            taskId: task.id,
            detail,
          })),
        ),
      ).then((results) => {
        const detailsMap = new Map();
        results.forEach(({ taskId, detail }) => {
          detailsMap.set(taskId, detail);
        });
        setTaskDetails(detailsMap);
        setLoading(false);
      });
    } else if (selectedTasks.length === 0) {
      setTaskDetails(new Map());
    }
  }, [open, selectedTasks.length, Array.from(selectedTaskIds).join(",")]);

  // Group by freelancer using actual names from task details
  const freelancerGroups = new Map<
    string,
    { freelancerId: number; tasks: any[]; total: number; hours: number }
  >();

  selectedTasks.forEach((task) => {
    const detail = taskDetails.get(task.id);
    if (detail && detail.entries) {
      // Group entries by freelancer for this task
      const taskFreelancerMap = new Map<number, { name: string; hours: number; amount: number }>();

      detail.entries.forEach((entry: any) => {
        const flId = entry.freelancer_id;
        if (!taskFreelancerMap.has(flId)) {
          taskFreelancerMap.set(flId, {
            name: entry.freelancer_name || `Freelancer ${flId}`,
            hours: 0,
            amount: 0,
          });
        }
        const flData = taskFreelancerMap.get(flId)!;
        flData.hours += entry.hours;
        flData.amount += entry.amount;
      });

      // Now add aggregated data to freelancer groups
      taskFreelancerMap.forEach((flData, flId) => {
        // Skip if this task-freelancer pair is excluded
        if (excludedPairs.has(`${task.id}-${flId}`)) {
          return;
        }

        const freelancerKey = flData.name;
        if (!freelancerGroups.has(freelancerKey)) {
          freelancerGroups.set(freelancerKey, {
            freelancerId: flId,
            tasks: [],
            total: 0,
            hours: 0,
          });
        }
        const group = freelancerGroups.get(freelancerKey)!;

        group.tasks.push({
          ...task,
          freelancerId: flId,
          freelancerHours: flData.hours,
          freelancerAmount: flData.amount,
        });

        group.total += flData.amount;
        group.hours += flData.hours;
      });
    }
  });

  const grandTotal = Array.from(freelancerGroups.values()).reduce(
    (sum, group) => sum + group.total,
    0,
  );
  const grandHours = Array.from(freelancerGroups.values()).reduce(
    (sum, group) => sum + group.hours,
    0,
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Review Payment Batch</DialogTitle>
          <DialogDescription>
            Review the selected worklogs grouped by freelancer before confirming payment.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {selectedTasks.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No tasks selected for payment
            </div>
          ) : (
            <>
              {Array.from(freelancerGroups.entries()).map(([freelancer, group]) => (
                <div key={freelancer} className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold">{freelancer}</h3>
                      <p className="text-sm text-muted-foreground">
                        {group.tasks.length} task{group.tasks.length !== 1 ? "s" : ""} ·{" "}
                        {group.hours.toFixed(1)} hours
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold">${group.total.toFixed(2)}</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    {group.tasks.map((task) => (
                      <div
                        key={`${task.id}-${task.freelancerId}`}
                        className="flex items-center justify-between bg-muted/50 rounded p-3"
                      >
                        <div className="flex-1">
                          <p className="font-medium">{task.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {(task.freelancerHours || task.total_hours).toFixed(2)}h · $
                            {(task.freelancerAmount || task.total_amount).toFixed(2)}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onRemoveTaskFromFreelancer(task.id, task.freelancerId)}
                          aria-label={`Remove ${task.name} from ${freelancer}`}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              ))}

              <div className="border-t pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Payment</p>
                    <p className="text-sm text-muted-foreground">
                      {selectedTasks.length} task{selectedTasks.length !== 1 ? "s" : ""} ·{" "}
                      {grandHours.toFixed(1)} hours
                    </p>
                  </div>
                  <p className="text-3xl font-bold">${grandTotal.toFixed(2)}</p>
                </div>
              </div>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={onConfirm} disabled={selectedTasks.length === 0}>
            Confirm Payment
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
