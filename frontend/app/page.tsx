'use client';

import { useState, useEffect } from 'react';
import WorkLogTable from '../components/WorkLogTable';
import DateFilter from '../components/DateFilter';
import PaymentReview from '../components/PaymentReview';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [worklogs, setWorklogs] = useState<any[]>([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedLogs, setSelectedLogs] = useState<number[]>([]);
  const [isReviewing, setIsReviewing] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchWorkLogs = async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/worklogs`;
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (params.toString()) url += `?${params.toString()}`;

      const res = await fetch(url);
      const data = await res.json();
      setWorklogs(data);
    } catch (err) {
      console.error('Failed to fetch worklogs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkLogs();
  }, [startDate, endDate]);

  const toggleSelect = (id: number) => {
    setSelectedLogs(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const handleProcessPayment = () => {
    if (selectedLogs.length > 0) {
      setIsReviewing(true);
    }
  };

  const handleConfirmPayment = async (idsToPay: number[]) => {
    try {
      const res = await fetch(`${API_URL}/payments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(idsToPay),
      });
      if (res.ok) {
        alert('Payment processed successfully!');
        setIsReviewing(false);
        setSelectedLogs([]);
        fetchWorkLogs();
      } else {
        const err = await res.json();
        alert(`Error: ${err.detail}`);
      }
    } catch (err) {
      alert('Failed to process payment');
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">WorkLog Payment Dashboard</h1>
            <p className="text-gray-600">Review and process freelancer payments</p>
          </div>
          <button 
            onClick={handleProcessPayment}
            disabled={selectedLogs.length === 0}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-sm"
          >
            Process Payment ({selectedLogs.length})
          </button>
        </header>

        <section className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200 bg-gray-50 flex gap-4 items-end">
            <DateFilter 
              label="From" 
              value={startDate} 
              onChange={setStartDate} 
            />
            <DateFilter 
              label="To" 
              value={endDate} 
              onChange={setEndDate} 
            />
          </div>

          <WorkLogTable 
            worklogs={worklogs} 
            loading={loading}
            selectedLogs={selectedLogs}
            onToggleSelect={toggleSelect}
          />
        </section>
      </div>

      {isReviewing && (
        <PaymentReview 
          worklogs={worklogs.filter(w => selectedLogs.includes(w.id))}
          onClose={() => setIsReviewing(false)}
          onConfirm={handleConfirmPayment}
        />
      )}
    </main>
  );
}
