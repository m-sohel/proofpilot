import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { QueueView } from './components/QueueView';
import { CaseView } from './components/CaseView';
import { BenchmarkView } from './components/BenchmarkView';
import type { HealthResponse, QueueItem } from './types';
import { api } from './api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'queue' | 'case' | 'benchmark'>('queue');
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [queueLoading, setQueueLoading] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const checkHealth = async () => {
    try {
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth({
        status: 'error',
        llm_status: 'offline',
        llm_provider: 'mock',
        demo_mode: true,
      });
    }
  };

  const loadQueue = async () => {
    setQueueLoading(true);
    try {
      const data = await api.getQueue();
      setQueue(data);
      if (data.length > 0 && !activeCaseId) {
        setActiveCaseId(data[0].case_id);
      }
    } catch (err: any) {
      console.error('Failed to load queue:', err);
    } finally {
      setQueueLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    loadQueue();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSeed = async () => {
    setIsSeeding(true);
    try {
      const res = await api.seedCases();
      setNotification({ message: res.message, type: 'success' });
      await loadQueue();
    } catch (err: any) {
      setNotification({ message: err.message || 'Failed to seed cases', type: 'error' });
    } finally {
      setIsSeeding(false);
      setTimeout(() => setNotification(null), 4000);
    }
  };

  const handleSelectCase = (caseId: string) => {
    setActiveCaseId(caseId);
    setCurrentTab('case');
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        activeCaseId={activeCaseId}
        health={health}
        onSeed={handleSeed}
        isSeeding={isSeeding}
      />

      {/* Toast notification */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 animate-bounce">
          <div
            className={`px-4 py-2.5 rounded-xl shadow-xl text-xs font-medium border flex items-center gap-2 ${
              notification.type === 'success'
                ? 'bg-emerald-950 border-emerald-500/50 text-emerald-200'
                : 'bg-rose-950 border-rose-500/50 text-rose-200'
            }`}
          >
            <span>{notification.message}</span>
          </div>
        </div>
      )}

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentTab === 'queue' && (
          <QueueView
            queue={queue}
            loading={queueLoading}
            onSelectCase={handleSelectCase}
            onSeed={handleSeed}
          />
        )}

        {currentTab === 'case' && activeCaseId && (
          <CaseView
            caseId={activeCaseId}
            onBackToQueue={() => setCurrentTab('queue')}
            onRefreshQueue={loadQueue}
          />
        )}

        {currentTab === 'benchmark' && <BenchmarkView />}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950/60 py-6 text-center text-xs text-slate-500">
        <p>
          ProofPilot • Payment Dispute Agent with Grounding Verifier & Economics Engine • Zero API Cost MVP
        </p>
      </footer>
    </div>
  );
};

export default App;
