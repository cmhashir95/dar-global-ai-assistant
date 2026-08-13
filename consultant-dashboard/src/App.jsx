import { useEffect, useState } from "react";
import { getLeads, getLead } from "./lib/api";
import LeadsTable from "./components/LeadsTable";
import LeadDetail from "./components/LeadDetail";

const POLL_MS = 8000;

export default function App() {
  const [leads, setLeads] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedLead, setSelectedLead] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    async function poll() {
      try {
        const data = await getLeads();
        if (active) {
          setLeads(data);
          setError(null);
        }
      } catch {
        if (active) setError("Couldn't reach the backend API.");
      }
    }
    poll();
    const id = setInterval(poll, POLL_MS);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    getLead(selectedId).then(setSelectedLead).catch(() => setSelectedLead(null));
  }, [selectedId]);

  return (
    <div className="min-h-screen">
      <header className="bg-ink text-parchment">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <p className="font-mono text-xs tracking-[0.25em] text-brass-light uppercase mb-1">Internal tool</p>
          <h1 className="font-display text-3xl">Consultant Dashboard</h1>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-10">
        {error && (
          <p className="text-sm text-warn bg-warn/10 border border-warn/30 px-4 py-3 mb-6">{error}</p>
        )}
        <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6 items-start">
          <LeadsTable leads={leads} selectedId={selectedId} onSelect={setSelectedId} />
          <div className="h-[600px]">
            <LeadDetail lead={selectedLead} />
          </div>
        </div>
      </main>
    </div>
  );
}
