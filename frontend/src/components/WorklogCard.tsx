'use client';

import Link from 'next/link';
import { Worklog } from '@/types';
import { formatCurrency, formatHours, formatDate, getStatusColor } from '@/lib/utils';

interface WorklogCardProps {
    worklog: Worklog;
    selectable?: boolean;
    selected?: boolean;
    onSelect?: (id: string) => void;
}

export default function WorklogCard({
    worklog,
    selectable = false,
    selected = false,
    onSelect,
}: WorklogCardProps) {
    const initials = worklog.freelancer_name
        ?.split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase() || '?';

    const handleClick = () => {
        if (selectable && onSelect) {
            onSelect(worklog.id);
        }
    };

    const CardContent = (
        <>
            <div className="worklog-card-header">
                <div>
                    <div className="worklog-task-title">{worklog.task_title || 'Untitled Task'}</div>
                    <div className="worklog-freelancer">
                        <div className="freelancer-avatar">{initials}</div>
                        <span>{worklog.freelancer_name}</span>
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {selectable && (
                        <div
                            className={`checkbox ${selected ? 'checked' : ''}`}
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                handleClick();
                            }}
                        >
                            {selected && '✓'}
                        </div>
                    )}
                    <span className={`status-badge ${getStatusColor(worklog.status)}`}>
                        {worklog.status}
                    </span>
                </div>
            </div>

            {worklog.description && (
                <p className="worklog-description">{worklog.description}</p>
            )}

            <div className="worklog-stats">
                <div className="worklog-stat">
                    <span className="worklog-stat-value">{formatHours(worklog.total_hours)}</span>
                    <span className="worklog-stat-label">Hours</span>
                </div>
                <div className="worklog-stat">
                    <span className="worklog-stat-value">{formatCurrency(worklog.total_amount)}</span>
                    <span className="worklog-stat-label">Earned</span>
                </div>
                {worklog.time_entries_count !== undefined && worklog.time_entries_count !== null && (
                    <div className="worklog-stat">
                        <span className="worklog-stat-value">{worklog.time_entries_count}</span>
                        <span className="worklog-stat-label">Entries</span>
                    </div>
                )}
                <div className="worklog-stat">
                    <span className="worklog-stat-value">{formatDate(worklog.created_at)}</span>
                    <span className="worklog-stat-label">Date</span>
                </div>
            </div>
        </>
    );

    if (selectable) {
        return (
            <div
                className="worklog-card"
                onClick={handleClick}
                style={{
                    borderColor: selected ? 'var(--accent-primary)' : undefined,
                    boxShadow: selected ? 'var(--shadow-glow)' : undefined,
                }}
            >
                {CardContent}
            </div>
        );
    }

    return (
        <Link href={`/worklogs/${worklog.id}`} className="worklog-card">
            {CardContent}
        </Link>
    );
}
