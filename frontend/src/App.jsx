import { useEffect, useState } from 'react';
import AppShell from './components/layout/AppShell.jsx';
import ChatPanel from './features/chat/ChatPanel.jsx';
import SetupGuide from './features/status/SetupGuide.jsx';
import UploadPanel from './features/upload/UploadPanel.jsx';
import { API_BASE_URL, fetchHealth } from './lib/api.js';

export default function App() {
  const [backendStatus, setBackendStatus] = useState('checking');

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
    <AppShell>
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <ChatPanel />
        </div>

        <div className="space-y-6">
          <UploadPanel />
          <SetupGuide apiBaseUrl={API_BASE_URL} backendStatus={backendStatus} />
        </div>
      </section>
    </AppShell>
  );
}
