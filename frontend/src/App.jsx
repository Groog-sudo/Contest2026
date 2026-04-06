import { useEffect, useState } from 'react';
import AppShell from './components/layout/AppShell.jsx';
import CallRequestPanel from './features/calls/CallRequestPanel.jsx';
import LeadCapturePanel from './features/leads/LeadCapturePanel.jsx';
import KnowledgeBasePanel from './features/knowledge/KnowledgeBasePanel.jsx';
import MetricsPanel from './features/status/MetricsPanel.jsx';
import SetupGuide from './features/status/SetupGuide.jsx';
import { API_BASE_URL, fetchHealth } from './lib/api.js';

export default function App() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [latestLead, setLatestLead] = useState(null);

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then(() => {
        if (!cancelled) {
          setBackendStatus('online');
        }
      })
      .catch(() => {
        if (!cancelled) {
          setBackendStatus('offline');
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell latestLead={latestLead}>
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <LeadCapturePanel onLeadCaptured={setLatestLead} />
          <CallRequestPanel lead={latestLead} />
        </div>

        <div className="space-y-6">
          <MetricsPanel />
          <KnowledgeBasePanel />
          <SetupGuide apiBaseUrl={API_BASE_URL} backendStatus={backendStatus} />
        </div>
      </section>
    </AppShell>
  );
}
