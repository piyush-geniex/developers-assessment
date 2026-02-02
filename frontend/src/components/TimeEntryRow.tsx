'use client';

import { TimeEntry } from '@/types';
import { formatHours, formatTime, formatDate } from '@/lib/utils';

interface TimeEntryRowProps {
    entry: TimeEntry;
}

export default function TimeEntryRow({ entry }: TimeEntryRowProps) {
    return (
        <div className="time-entry-item">
            <div className="time-entry-info">
                <div className="time-entry-description">
                    {entry.description || 'No description'}
                </div>
                <div className="time-entry-time">
                    <span>📅 {formatDate(entry.start_time)}</span>
                    <span>🕐 {formatTime(entry.start_time)} - {formatTime(entry.end_time)}</span>
                </div>
            </div>
            <div className="time-entry-hours">
                {formatHours(entry.hours)}
            </div>
        </div>
    );
}
