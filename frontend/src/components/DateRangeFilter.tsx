'use client';

import { getDateDaysAgo, getTodayDate } from '@/lib/utils';

interface DateRangeFilterProps {
    dateFrom: string;
    dateTo: string;
    onDateFromChange: (date: string) => void;
    onDateToChange: (date: string) => void;
    onApply: () => void;
}

export default function DateRangeFilter({
    dateFrom,
    dateTo,
    onDateFromChange,
    onDateToChange,
    onApply,
}: DateRangeFilterProps) {
    const presets = [
        { label: 'Last 7 days', days: 7 },
        { label: 'Last 14 days', days: 14 },
        { label: 'Last 30 days', days: 30 },
        { label: 'This month', days: 0 },
    ];

    const applyPreset = (days: number) => {
        if (days === 0) {
            // This month
            const now = new Date();
            const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
            onDateFromChange(firstDay.toISOString().split('T')[0]);
            onDateToChange(getTodayDate());
        } else {
            onDateFromChange(getDateDaysAgo(days));
            onDateToChange(getTodayDate());
        }
    };

    return (
        <div className="filters-section">
            <div className="filters-row">
                <div className="form-group">
                    <label className="form-label">From Date</label>
                    <input
                        type="date"
                        className="form-input"
                        value={dateFrom}
                        onChange={(e) => onDateFromChange(e.target.value)}
                    />
                </div>

                <div className="form-group">
                    <label className="form-label">To Date</label>
                    <input
                        type="date"
                        className="form-input"
                        value={dateTo}
                        onChange={(e) => onDateToChange(e.target.value)}
                    />
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {presets.map((preset) => (
                        <button
                            key={preset.label}
                            className="btn btn-secondary"
                            onClick={() => applyPreset(preset.days)}
                            style={{ padding: '0.5rem 1rem', fontSize: '0.75rem' }}
                        >
                            {preset.label}
                        </button>
                    ))}
                </div>

                <button className="btn btn-primary" onClick={onApply}>
                    Apply Filter
                </button>
            </div>
        </div>
    );
}
