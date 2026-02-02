'use client';

import { useState, useEffect } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function WorkLogDetail({ worklogId, onClose }: { 
  worklogId: number, 
  onClose: () => void 
}) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_URL}/worklogs/${worklogId}`);
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error('Failed to fetch detail:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [worklogId]);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-gray-900">WorkLog Details</h2>
            {data && (
              <p className="text-sm text-gray-500">
                {data.freelancer.name} • {data.task.title} (${data.task.rate_per_hour}/hr)
              </p>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="text-center py-12 text-gray-500">Loading entries...</div>
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr className="text-xs text-gray-400 uppercase">
                  <th className="pb-4 font-semibold">Date</th>
                  <th className="pb-4 font-semibold text-center">Hours</th>
                  <th className="pb-4 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.time_entries.map((entry: any) => (
                  <tr key={entry.id}>
                    <td className="py-4 text-sm text-gray-600">
                      {new Date(entry.date).toLocaleDateString()}
                    </td>
                    <td className="py-4 text-sm text-center font-medium text-gray-900">
                      {entry.hours}h
                    </td>
                    <td className="py-4 text-sm text-gray-600">
                      {entry.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-end">
          <button 
            onClick={onClose}
            className="px-6 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
