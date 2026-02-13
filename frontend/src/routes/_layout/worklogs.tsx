import { Fragment, useEffect, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { Loader2, Eye, CircleDollarSign } from 'lucide-react'

import { WorklogsService } from '@/client'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'

export const Route = createFileRoute('/_layout/worklogs')({
  component: Worklogs
})

function Worklogs () {
  const queryClient = useQueryClient()
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [drillDownId, setDrillDownId] = useState<string | null>(null)
  const [isReviewOpen, setIsReviewOpen] = useState(false)
  const [excludedFreelancerUuidsInBatch, setExcludedFreelancerUuidsInBatch] =
    useState<string[]>([])
  const [excludedWorklogIdsInBatch, setExcludedWorklogIdsInBatch] = useState<
    string[]
  >([])
  const [excludedTimeEntryIdsInBatch, setExcludedTimeEntryIdsInBatch] = useState<
    string[]
  >([])

  const { data: worklogs, isLoading } = useQuery({
    queryKey: ['worklogs', startDate, endDate],
    queryFn: () =>
      WorklogsService.readWorklogs({
        startDate: startDate || undefined,
        endDate: endDate || undefined
      })
  })

  useEffect(() => {
    // Date range defines "eligible for payment" – reset selection/review to avoid stale batches.
    setSelectedIds([])
    setIsReviewOpen(false)
    setDrillDownId(null)
    setExcludedFreelancerUuidsInBatch([])
    setExcludedWorklogIdsInBatch([])
    setExcludedTimeEntryIdsInBatch([])
  }, [startDate, endDate])

  useEffect(() => {
    // Keep selection in sync with the filtered list.
    if (!worklogs?.data) return
    const visibleIds = new Set(worklogs.data.map(w => w.id))
    setSelectedIds(prev => prev.filter(id => visibleIds.has(id)))
  }, [worklogs?.data])

  const selectedWorklogs =
    worklogs?.data.filter(w => selectedIds.includes(w.id)) || []

  const { data: detailData, isLoading: isDetailLoading } = useQuery({
    queryKey: ['worklog', drillDownId, startDate, endDate],
    queryFn: () =>
      drillDownId
        ? WorklogsService.readWorklog({
            id: drillDownId,
            startDate: startDate || undefined,
            endDate: endDate || undefined
          })
        : null,
    enabled: !!drillDownId
  })

  const mutation = useMutation({
    mutationFn: (data: {
      worklog_ids: string[]
      time_entry_ids: string[]
      excluded_freelancer_ids: string[]
    }) => WorklogsService.processPayments({ requestBody: data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['worklogs'] })
      setSelectedIds([])
      setIsReviewOpen(false)
      setExcludedTimeEntryIdsInBatch([])
      toast.success('Payments processed successfully')
    },
    onError: () => {
      toast.error('Failed to process payments')
    }
  })

  const toggleSelect = (id: string) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const handleReview = () => {
    if (selectedIds.length === 0) {
      toast.error('Please select at least one worklog')
      return
    }
    setExcludedFreelancerUuidsInBatch([])
    setExcludedWorklogIdsInBatch([])
    setExcludedTimeEntryIdsInBatch([])
    setIsReviewOpen(true)
  }

  const { data: batchDetails, isLoading: isBatchDetailsLoading } = useQuery({
    queryKey: ['worklog-batch-details', selectedIds, startDate, endDate],
    queryFn: async () => {
      const ids = [...selectedIds]
      const res = await Promise.all(
        ids.map(id =>
          WorklogsService.readWorklog({
            id,
            startDate: startDate || undefined,
            endDate: endDate || undefined
          })
        )
      )
      const byId: Record<string, any> = {}
      for (const wl of res) byId[wl.id] = wl
      return byId
    },
    enabled: isReviewOpen && selectedIds.length > 0
  })

  const includedTimeEntryIds = useMemo(() => {
    if (!batchDetails) return []
    const included: string[] = []
    for (const wlId of selectedIds) {
      const wl = batchDetails[wlId]
      if (!wl) continue
      if (excludedWorklogIdsInBatch.includes(wl.id)) continue
      if (excludedFreelancerUuidsInBatch.includes(wl.freelancer_uuid)) continue
      for (const te of wl.time_entries || []) {
        if (te.is_paid) continue
        if (excludedTimeEntryIdsInBatch.includes(te.id)) continue
        included.push(te.id)
      }
    }
    return included
  }, [
    batchDetails,
    excludedFreelancerUuidsInBatch,
    excludedTimeEntryIdsInBatch,
    excludedWorklogIdsInBatch,
    selectedIds
  ])

  const calculatedPayout = useMemo(() => {
    if (!batchDetails) {
      return selectedWorklogs
        .filter(
          w =>
            !excludedWorklogIdsInBatch.includes(w.id) &&
            !excludedFreelancerUuidsInBatch.includes(w.freelancer_uuid)
        )
        .reduce((sum, w) => sum + (w.total_earned || 0), 0)
    }
    let total = 0
    for (const wlId of selectedIds) {
      const wl = batchDetails[wlId]
      if (!wl) continue
      if (excludedWorklogIdsInBatch.includes(wl.id)) continue
      if (excludedFreelancerUuidsInBatch.includes(wl.freelancer_uuid)) continue
      for (const te of wl.time_entries || []) {
        if (te.is_paid) continue
        if (excludedTimeEntryIdsInBatch.includes(te.id)) continue
        total += te.hours * te.hourly_rate
      }
    }
    return total
  }, [
    batchDetails,
    excludedFreelancerUuidsInBatch,
    excludedTimeEntryIdsInBatch,
    excludedWorklogIdsInBatch,
    selectedIds,
    selectedWorklogs
  ])

  const handleConfirmPayment = () => {
    const activeWorklogs = selectedWorklogs.filter(
      w => !excludedWorklogIdsInBatch.includes(w.id)
    )
    const excludedFreelancerUuids = excludedFreelancerUuidsInBatch

    const includedWorklogIds = activeWorklogs
      .filter(w => !excludedFreelancerUuids.includes(w.freelancer_uuid))
      .map(w => w.id)

    if (includedWorklogIds.length === 0) {
      toast.error('Your batch is empty after exclusions')
      return
    }

    if (isBatchDetailsLoading) {
      toast.error('Loading time logs, please wait...')
      return
    }

    if (includedTimeEntryIds.length === 0) {
      toast.error('No time logs selected for payout')
      return
    }

    mutation.mutate({
      worklog_ids: activeWorklogs.map(w => w.id),
      time_entry_ids: includedTimeEntryIds,
      excluded_freelancer_ids: excludedFreelancerUuids
    })
  }

  if (isLoading) {
    return (
      <div className='flex items-center justify-center p-8'>
        <Loader2 className='h-8 w-8 animate-spin text-primary' />
      </div>
    )
  }

  return (
    <div className='container mx-auto py-8'>
      <div className='sticky top-16 z-40 -mx-6 mb-8 flex items-center justify-between gap-4 border-b bg-background/95 px-6 py-4 backdrop-blur supports-backdrop-filter:bg-background/60'>
        <div>
          <h1 className='text-3xl font-bold'>WorkLog Payments</h1>
          <p className='text-muted-foreground'>
            Review and process payments for freelancer worklogs.
          </p>
        </div>
        <Button onClick={handleReview} disabled={selectedIds.length === 0}>
          <CircleDollarSign className='mr-2 h-4 w-4' />
          Review & Pay ({selectedIds.length})
        </Button>
      </div>

      <div className='space-y-8'>
      <Card>
        <CardHeader>
          <CardTitle className='text-sm font-medium'>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='flex gap-4'>
            <div className='space-y-1'>
              <label className='text-xs font-semibold uppercase tracking-wider text-muted-foreground'>
                Start Date
              </label>
              <Input
                type='date'
                value={startDate}
                onChange={e => setStartDate(e.target.value)}
                className='w-[200px]'
              />
            </div>
            <div className='space-y-1'>
              <label className='text-xs font-semibold uppercase tracking-wider text-muted-foreground'>
                End Date
              </label>
              <Input
                type='date'
                value={endDate}
                onChange={e => setEndDate(e.target.value)}
                className='w-[200px]'
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className='rounded-md border bg-card'>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className='w-[50px]'></TableHead>
              <TableHead>Task Name</TableHead>
              <TableHead>Freelancer</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className='text-right'>Total Earned</TableHead>
              <TableHead className='text-right'>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {worklogs?.data.map(wl => (
              <TableRow
                key={wl.id}
                className={selectedIds.includes(wl.id) ? 'bg-muted/50' : ''}
              >
                <TableCell>
                  <Checkbox
                    checked={selectedIds.includes(wl.id)}
                    onCheckedChange={() => toggleSelect(wl.id)}
                    disabled={wl.status === 'paid'}
                  />
                </TableCell>
                <TableCell className='font-medium'>{wl.task_name}</TableCell>
                <TableCell>
                  <div className='flex flex-col'>
                    <span className='font-semibold text-sm'>
                      {wl.freelancer_name}
                    </span>
                    <span className='text-[10px] text-muted-foreground font-mono uppercase tracking-tighter bg-muted px-1 rounded w-fit'>
                      {wl.freelancer_id}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={wl.status === 'paid' ? 'default' : 'outline'}
                    className='capitalize'
                  >
                    {wl.status}
                  </Badge>
                </TableCell>
                <TableCell className='text-right font-semibold'>
                  ${(wl.total_earned || 0).toFixed(2)}
                </TableCell>
                <TableCell className='text-right'>
                  <Button
                    variant='ghost'
                    size='sm'
                    onClick={() => setDrillDownId(wl.id)}
                  >
                    <Eye className='h-4 w-4 mr-1' /> Details
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {worklogs?.data.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className='h-24 text-center'>
                  No worklogs found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      </div>

      {/* Drill Down Dialog */}
      <Dialog
        open={!!drillDownId}
        onOpenChange={open => !open && setDrillDownId(null)}
      >
        <DialogContent className='max-w-5xl w-[90vw] sm:max-w-5xl overflow-hidden flex flex-col max-h-[85vh] p-0'>
          <DialogHeader className='p-6 pb-4 border-b'>
            <div className='flex items-center gap-3 text-primary'>
              <Eye className='h-6 w-6' />
              <DialogTitle className='text-2xl font-bold'>
                Worklog Activity: {detailData?.task_name}
              </DialogTitle>
            </div>
          </DialogHeader>

          <div className='flex-1 overflow-y-auto p-6 space-y-8'>
            {isDetailLoading ? (
              <div className='flex flex-col items-center justify-center py-20 space-y-4'>
                <Loader2 className='h-12 w-12 animate-spin text-primary/50' />
                <p className='text-muted-foreground font-medium'>
                  Fetching activity logs...
                </p>
              </div>
            ) : (
              detailData && (
                <>
                  <div className='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4'>
                    <Card className='shadow-sm border-primary/10 bg-muted/30'>
                      <CardHeader className='p-4 pb-1'>
                        <CardTitle className='text-[10px] font-bold uppercase tracking-wider text-muted-foreground'>
                          Freelancer
                        </CardTitle>
                      </CardHeader>
                      <CardContent className='p-4 pt-0'>
                        <div className='flex flex-col'>
                          <span className='text-base font-bold text-foreground leading-tight truncate'>
                            {detailData.freelancer_name}
                          </span>
                          <span className='text-[10px] font-mono text-primary font-bold uppercase'>
                            {detailData.freelancer_id}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                    <Card className='shadow-sm border-primary/10 bg-muted/30'>
                      <CardHeader className='p-4 pb-1'>
                        <CardTitle className='text-[10px] font-bold uppercase tracking-wider text-muted-foreground'>
                          Total Effort
                        </CardTitle>
                      </CardHeader>
                      <CardContent className='p-4 pt-0'>
                        <span className='text-2xl font-black text-foreground'>
                          {detailData.time_entries
                            .reduce((acc, te) => acc + te.hours, 0)
                            .toFixed(1)}
                          <small className='text-sm font-normal ml-1 text-muted-foreground'>
                            hrs
                          </small>
                        </span>
                      </CardContent>
                    </Card>
                    <Card className='shadow-sm border-primary/10 bg-muted/30'>
                      <CardHeader className='p-4 pb-1'>
                        <CardTitle className='text-[10px] font-bold uppercase tracking-wider text-muted-foreground'>
                          Avg. Rate
                        </CardTitle>
                      </CardHeader>
                      <CardContent className='p-4 pt-0'>
                        <span className='text-2xl font-black text-foreground'>
                          $
                          {(
                            detailData.total_earned! /
                            Math.max(
                              detailData.time_entries.reduce(
                                (acc, te) => acc + te.hours,
                                0
                              ),
                              1
                            )
                          ).toFixed(2)}
                          <small className='text-sm font-normal ml-1 text-muted-foreground'>
                            /h
                          </small>
                        </span>
                      </CardContent>
                    </Card>
                    <Card className='shadow-sm border-primary text-primary-foreground bg-primary'>
                      <CardHeader className='p-4 pb-1'>
                        <CardTitle className='text-[10px] font-bold uppercase tracking-wider opacity-80'>
                          Accumulated
                        </CardTitle>
                      </CardHeader>
                      <CardContent className='p-4 pt-0'>
                        <span className='text-2xl font-black'>
                          $
                          {detailData.total_earned?.toLocaleString(undefined, {
                            minimumFractionDigits: 2
                          })}
                        </span>
                      </CardContent>
                    </Card>
                  </div>

                  <div className='space-y-4'>
                    <div className='flex items-center justify-between px-1'>
                      <h3 className='text-xs font-bold uppercase tracking-widest text-muted-foreground'>
                        Activity Timeline
                      </h3>
                      <Badge variant='outline' className='text-[10px]'>
                        {detailData.time_entries.length} Logs
                      </Badge>
                    </div>
                    <div className='rounded-xl border shadow-sm overflow-hidden bg-card'>
                      <Table>
                        <TableHeader className='bg-muted/50'>
                          <TableRow className='hover:bg-transparent'>
                            <TableHead className='w-[140px] font-bold'>
                              Date
                            </TableHead>
                            <TableHead className='w-[100px] font-bold'>
                              Hours
                            </TableHead>
                            <TableHead className='w-[120px] text-right font-bold'>
                              Rate
                            </TableHead>
                            <TableHead className='font-bold'>
                              Summary of Work
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {detailData.time_entries.map(te => (
                            <TableRow key={te.id} className='hover:bg-muted/5'>
                              <TableCell className='font-medium text-sm'>
                                {te.date}
                              </TableCell>
                              <TableCell>
                                <code className='text-xs font-bold bg-primary/10 text-primary px-2 py-0.5 rounded-md'>
                                  {te.hours.toFixed(1)}h
                                </code>
                              </TableCell>
                              <TableCell className='text-right font-mono text-sm text-muted-foreground'>
                                ${te.hourly_rate.toFixed(2)}
                              </TableCell>
                              <TableCell className='text-sm text-muted-foreground leading-snug py-4'>
                                {te.description ||
                                  'No specific details provided for this entry.'}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </>
              )
            )}
          </div>
          <DialogFooter className='p-6 border-t bg-muted/30 mt-auto'>
            <Button
              variant='outline'
              onClick={() => setDrillDownId(null)}
              className='font-bold px-8'
            >
              Close Activity View
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Review Dialog */}
      <Dialog open={isReviewOpen} onOpenChange={setIsReviewOpen}>
        <DialogContent className='max-w-4xl w-[85vw] sm:max-w-4xl p-0 overflow-hidden'>
          <DialogHeader className='p-6 border-b bg-muted/20'>
            <div className='flex items-center gap-3 text-primary'>
              <CircleDollarSign className='h-7 w-7' />
              <DialogTitle className='text-2xl font-black tracking-tight'>
                Payment Confirmation
              </DialogTitle>
            </div>
          </DialogHeader>
          <div className='space-y-6 py-6 px-6'>
            <div className='p-6 bg-primary text-primary-foreground rounded-xl shadow-inner relative overflow-hidden'>
              <div className='relative z-10 space-y-1'>
                <p className='text-sm font-medium opacity-80 uppercase tracking-widest'>
                  Calculated Payout
                </p>
                <h2 className='text-4xl font-black'>
                  $
                  {calculatedPayout.toFixed(2)}
                </h2>
                <p className='text-xs opacity-70 mt-2'>
                  Batch contains {includedTimeEntryIds.length} time logs
                </p>
              </div>
              <CircleDollarSign className='absolute -bottom-4 -right-4 h-32 w-32 opacity-10 rotate-12' />
            </div>

            <div className='space-y-4'>
              <div className='flex items-center justify-between px-1'>
                <h3 className='text-sm font-bold uppercase text-muted-foreground'>
                  Selection Drilldown
                </h3>
                <p className='text-[10px] text-muted-foreground italic'>
                  Toggle visibility to exclude from this specific payout
                </p>
              </div>
              <div className='max-h-[350px] overflow-y-auto rounded-lg border shadow-sm px-1 bg-card'>
                <Table>
                  <TableHeader className='bg-muted/30 sticky top-0 z-10'>
                    <TableRow className='hover:bg-transparent'>
                      <TableHead className='w-[40px]'></TableHead>
                      <TableHead className='font-bold'>Task Details</TableHead>
                      <TableHead className='text-right font-bold'>
                        Payout
                      </TableHead>
                      <TableHead className='w-[100px]'></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedWorklogs.map(w => {
                      const isWorklogExcluded =
                        excludedWorklogIdsInBatch.includes(w.id)
                      const isFreelancerExcluded =
                        excludedFreelancerUuidsInBatch.includes(
                          w.freelancer_uuid
                        )
                      const isInactive =
                        isWorklogExcluded || isFreelancerExcluded

                      const wlDetail = batchDetails?.[w.id]
                      const timeEntries = (wlDetail?.time_entries || []) as any[]
                      const activeEntries = timeEntries.filter(
                        te =>
                          !te.is_paid &&
                          !excludedTimeEntryIdsInBatch.includes(te.id)
                      )
                      const worklogPayout = isInactive
                        ? 0
                        : wlDetail
                          ? activeEntries.reduce(
                              (sum, te) => sum + te.hours * te.hourly_rate,
                              0
                            )
                          : (w.total_earned || 0)

                      return (
                        <Fragment key={w.id}>
                          <TableRow
                            className={cn(
                              'transition-all duration-200',
                              isInactive
                                ? 'bg-muted/30 opacity-40'
                                : 'hover:bg-muted/5'
                            )}
                          >
                            <TableCell className='py-3'>
                              <Checkbox
                                checked={!isInactive}
                                disabled={isFreelancerExcluded}
                                onCheckedChange={() => {
                                  setExcludedWorklogIdsInBatch(prev =>
                                    prev.includes(w.id)
                                      ? prev.filter(id => id !== w.id)
                                      : [...prev, w.id]
                                  )
                                }}
                              />
                            </TableCell>
                            <TableCell className='py-3'>
                              <div className='flex flex-col'>
                                <span
                                  className={cn(
                                    'text-sm font-bold leading-none',
                                    isInactive &&
                                      'line-through text-muted-foreground'
                                  )}
                                >
                                  {w.task_name}
                                </span>
                                <span className='text-[10px] text-muted-foreground mt-1 font-medium italic'>
                                  {w.freelancer_name} ({w.freelancer_id})
                                </span>
                              </div>
                            </TableCell>
                            <TableCell className='text-sm py-3 text-right font-black text-primary'>
                              {`$${worklogPayout.toFixed(2)}`}
                            </TableCell>
                            <TableCell className='text-right'>
                              <div className='flex justify-end gap-2'>
                                <Button
                                  variant={isInactive ? 'outline' : 'ghost'}
                                  size='sm'
                                  className='text-[10px] h-7 px-2'
                                  onClick={() => {
                                    setExcludedWorklogIdsInBatch(prev =>
                                      prev.includes(w.id)
                                        ? prev.filter(id => id !== w.id)
                                        : [...prev, w.id]
                                    )
                                  }}
                                >
                                  {isWorklogExcluded
                                    ? 'Restore Task'
                                    : 'Drop Task'}
                                </Button>
                                <Button
                                  variant={
                                    isFreelancerExcluded ? 'secondary' : 'ghost'
                                  }
                                  size='sm'
                                  className='text-[10px] h-7 px-2'
                                  onClick={() => {
                                    setExcludedFreelancerUuidsInBatch(prev =>
                                      prev.includes(w.freelancer_uuid)
                                        ? prev.filter(
                                            id => id !== w.freelancer_uuid
                                          )
                                        : [...prev, w.freelancer_uuid]
                                    )
                                  }}
                                >
                                  {isFreelancerExcluded
                                    ? 'Include Person'
                                    : 'Drop Person'}
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>

                          <TableRow>
                            <TableCell colSpan={4} className='pt-0 pb-4'>
                              <div className='ml-8 mr-2 rounded-md border bg-muted/10 overflow-hidden'>
                                <div className='flex items-center justify-between px-3 py-2 border-b bg-muted/20'>
                                  <span className='text-[10px] font-bold uppercase tracking-wider text-muted-foreground'>
                                    Time logs
                                  </span>
                                  {isBatchDetailsLoading ? (
                                    <span className='text-[10px] text-muted-foreground'>
                                      Loading…
                                    </span>
                                  ) : (
                                    <span className='text-[10px] text-muted-foreground'>
                                      {timeEntries.length} entries
                                    </span>
                                  )}
                                </div>

                                <div className='max-h-[180px] overflow-y-auto'>
                                  {timeEntries.length === 0 ? (
                                    <div className='px-3 py-3 text-xs text-muted-foreground'>
                                      No time logs in the selected date range.
                                    </div>
                                  ) : (
                                    <Table>
                                      <TableHeader className='bg-muted/10 sticky top-0'>
                                        <TableRow className='hover:bg-transparent'>
                                          <TableHead className='w-[40px]'></TableHead>
                                          <TableHead className='w-[120px] font-bold'>
                                            Date
                                          </TableHead>
                                          <TableHead className='w-[80px] font-bold'>
                                            Hours
                                          </TableHead>
                                          <TableHead className='w-[100px] text-right font-bold'>
                                            Rate
                                          </TableHead>
                                          <TableHead className='text-right font-bold'>
                                            Amount
                                          </TableHead>
                                          <TableHead className='w-[90px]'></TableHead>
                                        </TableRow>
                                      </TableHeader>
                                      <TableBody>
                                        {timeEntries.map(te => {
                                          const isExcluded =
                                            excludedTimeEntryIdsInBatch.includes(
                                              te.id
                                            )
                                          const isDisabled =
                                            isInactive || te.is_paid
                                          const isIncluded =
                                            !isDisabled && !isExcluded
                                          const amt = te.hours * te.hourly_rate

                                          return (
                                            <TableRow
                                              key={te.id}
                                              className={cn(
                                                isDisabled || isExcluded
                                                  ? 'opacity-60'
                                                  : 'hover:bg-muted/10'
                                              )}
                                            >
                                              <TableCell>
                                                <Checkbox
                                                  checked={isIncluded}
                                                  disabled={isDisabled}
                                                  onCheckedChange={() => {
                                                    setExcludedTimeEntryIdsInBatch(
                                                      prev =>
                                                        prev.includes(te.id)
                                                          ? prev.filter(
                                                              id => id !== te.id
                                                            )
                                                          : [...prev, te.id]
                                                    )
                                                  }}
                                                />
                                              </TableCell>
                                              <TableCell className='text-xs font-medium'>
                                                {te.date}
                                                {te.is_paid ? (
                                                  <span className='ml-2 text-[10px] font-bold uppercase text-muted-foreground'>
                                                    paid
                                                  </span>
                                                ) : null}
                                              </TableCell>
                                              <TableCell className='text-xs font-mono'>
                                                {te.hours.toFixed(1)}h
                                              </TableCell>
                                              <TableCell className='text-right text-xs font-mono text-muted-foreground'>
                                                ${te.hourly_rate.toFixed(2)}
                                              </TableCell>
                                              <TableCell className='text-right text-xs font-black'>
                                                {isIncluded
                                                  ? `$${amt.toFixed(2)}`
                                                  : '$0.00'}
                                              </TableCell>
                                              <TableCell className='text-right'>
                                                <Button
                                                  variant={
                                                    isExcluded
                                                      ? 'outline'
                                                      : 'ghost'
                                                  }
                                                  size='sm'
                                                  className='text-[10px] h-7 px-2'
                                                  disabled={isDisabled}
                                                  onClick={() => {
                                                    setExcludedTimeEntryIdsInBatch(
                                                      prev =>
                                                        prev.includes(te.id)
                                                          ? prev.filter(
                                                              id => id !== te.id
                                                            )
                                                          : [...prev, te.id]
                                                    )
                                                  }}
                                                >
                                                  {isExcluded
                                                    ? 'Restore'
                                                    : 'Drop log'}
                                                </Button>
                                              </TableCell>
                                            </TableRow>
                                          )
                                        })}
                                      </TableBody>
                                    </Table>
                                  )}
                                </div>
                              </div>
                            </TableCell>
                          </TableRow>
                        </Fragment>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>
            </div>

            <div className='flex items-start gap-4 p-4 bg-orange-50 border border-orange-200 rounded-xl text-orange-900 shadow-sm'>
              <div className='mt-0.5 text-xl'>⚠️</div>
              <div className='text-sm'>
                <p className='font-bold text-base'>Final Review Required</p>
                <p className='opacity-80'>
                  This will mark all selected worklogs as{' '}
                  <b className='text-orange-950 underline underline-offset-2'>
                    PAID
                  </b>
                  . This action is irreversible.
                </p>
              </div>
            </div>
          </div>
          <DialogFooter className='bg-muted/30 p-6 border-t flex gap-3'>
            <Button
              variant='outline'
              onClick={() => setIsReviewOpen(false)}
              className='flex-1 font-bold h-11'
            >
              Back to Selection
            </Button>
            <Button
              onClick={handleConfirmPayment}
              disabled={mutation.isPending}
              className='flex-1 font-bold h-11 shadow-sm'
            >
              {mutation.isPending ? (
                <Loader2 className='mr-2 h-4 w-4 animate-spin' />
              ) : (
                <CircleDollarSign className='mr-2 h-4 w-4' />
              )}
              Confirm & Issue Payout
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
