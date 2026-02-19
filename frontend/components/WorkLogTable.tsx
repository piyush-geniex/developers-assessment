'use client';

import { useState } from 'react';
import WorkLogDetail from './WorkLogDetail';

export default function WorkLogTable({ worklogs, loading, selectedLogs, onToggleSelect }: { 
  worklogs: any[], 
  loading: boolean, 
  selectedLogs: number[], 
  onToggleSelect: (id: number) => void 
}) {
  const [viewingLogId, setViewingLogId] = useState<number | null>(null);

  if (loading) {
    return <div className="p-12 text-center text-gray-500">Loading worklogs...</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead className="bg-gray-50 text-gray-700 text-xs font-semibold uppercase tracking-wider">
          <tr>
            <th className="px-6 py-4">
              <span className="sr-only">Select</span>
            </th>
            <th className="px-6 py-4">Freelancer</th>
            <th className="px-6 py-4">Task</th>
            <th className="px-6 py-4">Hours</th>
            <th className="px-6 py-4">Earnings</th>
            <th className="px-6 py-4">Status</th>
            <th className="px-6 py-4">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {worklogs.length === 0 ? (
            <tr>
              <td colSpan={7} className="px-6 py-12 text-center text-gray-500">No worklogs found for this period</td>
            </tr>
          ) : (
            worklogs.map((log) => (
              <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4">
                  <input 
                    type="checkbox" 
                    checked={selectedLogs.includes(log.id)}
                    onChange={() => onToggleSelect(log.id)}
                    disabled={log.status === 'paid'}
                    className="h-4 w-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500 disabled:opacity-30"
                  />
                </td>
                <td className="px-6 py-4">
                  <div className="font-medium text-gray-900">{log.freelancer_name}</div>
                </td>
                <td className="px-6 py-4 text-gray-600">{log.task_title}</td>
                <td className="px-6 py-4 text-gray-600">{log.total_hours}h</td>
                <td className="px-6 py-4 font-semibold text-gray-900">${log.total_earned.toFixed(2)}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    log.status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {log.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <button 
                    onClick={() => setViewingLogId(log.id)}
                    className="text-indigo-600 hover:text-indigo-900 font-medium text-sm"
                  >
                    View Entries
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      {viewingLogId && (
        <WorkLogDetail 
          worklogId={viewingLogId} 
          onClose={() => setViewingLogId(null)} 
        />
      )}
    </div>
  );
}
