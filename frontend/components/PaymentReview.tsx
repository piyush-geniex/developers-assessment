'use client';

import { useState } from 'react';

export default function PaymentReview({ worklogs, onClose, onConfirm }: { 
  worklogs: any[], 
  onClose: () => void, 
  onConfirm: (ids: number[]) => void 
}) {
  const [items, setItems] = useState<any[]>(worklogs);

  const removeItem = (id: number) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };

  const total = items.reduce((acc, item) => acc + item.total_earned, 0);

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Review Payment Batch</h2>
            <p className="text-sm text-gray-500">Exlucde specific worklogs before confirming</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {items.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No items in batch.</div>
          ) : (
            <div className="space-y-4">
              {items.map((item) => (
                <div key={item.id} className="flex justify-between items-center p-4 bg-gray-50 rounded-xl border border-gray-100">
                  <div>
                    <div className="font-bold text-gray-900">{item.freelancer_name}</div>
                    <div className="text-sm text-gray-500">{item.task_title} ({item.total_hours}h)</div>
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="font-bold text-gray-900">${item.total_earned.toFixed(2)}</div>
                    <button 
                      onClick={() => removeItem(item.id)}
                      className="text-red-500 hover:text-red-700 p-1"
                      title="Exclude from batch"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-xs text-gray-500 font-semibold uppercase">Total Batch Amount</span>
            <span className="text-2xl font-black text-gray-900">${total.toFixed(2)}</span>
          </div>
          <div className="flex gap-3">
            <button 
              onClick={onClose}
              className="px-6 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm"
            >
              Cancel
            </button>
            <button 
              onClick={() => onConfirm(items.map(i => i.id))}
              disabled={items.length === 0}
              className="px-8 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 shadow-lg shadow-indigo-200 disabled:opacity-50 transition-all active:scale-95"
            >
              Confirm & Issue Payment
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
