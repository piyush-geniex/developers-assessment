'use client';

import { Freelancer } from '@/types';

interface FreelancerExclusionProps {
    freelancers: Freelancer[];
    excludedIds: string[];
    onToggle: (id: string) => void;
}

export default function FreelancerExclusion({
    freelancers,
    excludedIds,
    onToggle,
}: FreelancerExclusionProps) {
    if (freelancers.length === 0) {
        return null;
    }

    return (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-header">
                <h3 className="card-title">
                    <span>👤</span>
                    <span>Exclude Freelancers</span>
                </h3>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    {excludedIds.length} excluded
                </span>
            </div>
            <div className="card-body">
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                    {freelancers.map((freelancer) => {
                        const isExcluded = excludedIds.includes(freelancer.id);
                        return (
                            <div
                                key={freelancer.id}
                                className="checkbox-wrapper"
                                onClick={() => onToggle(freelancer.id)}
                                style={{
                                    padding: '0.5rem 1rem',
                                    background: isExcluded ? 'rgba(239, 68, 68, 0.1)' : 'var(--bg-tertiary)',
                                    borderRadius: 'var(--radius-md)',
                                    border: `1px solid ${isExcluded ? 'var(--accent-danger)' : 'var(--border-primary)'}`,
                                }}
                            >
                                <div className={`checkbox ${isExcluded ? 'checked' : ''}`} style={{
                                    background: isExcluded ? 'var(--accent-danger)' : undefined,
                                    borderColor: isExcluded ? 'var(--accent-danger)' : undefined,
                                }}>
                                    {isExcluded && '✗'}
                                </div>
                                <span className="checkbox-label" style={{
                                    textDecoration: isExcluded ? 'line-through' : 'none',
                                    color: isExcluded ? 'var(--text-muted)' : 'var(--text-primary)',
                                }}>
                                    {freelancer.name}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
