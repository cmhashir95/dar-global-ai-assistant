const STATUS_STYLES = {
  new: "bg-ink/10 text-ink",
  qualifying: "bg-brass/15 text-brass",
  scheduled: "bg-ok/15 text-ok",
  escalated: "bg-warn/15 text-warn",
  closed: "bg-ink/10 text-muted",
};

export default function LeadsTable({ leads, selectedId, onSelect }) {
  if (leads.length === 0) {
    return (
      <div className="border border-ink/10 bg-white p-10 text-center text-muted text-sm">
        No leads yet. Conversations from the website chat widget will appear here automatically.
      </div>
    );
  }

  return (
    <div className="border border-ink/10 bg-white overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-ink/10 text-left text-muted font-mono text-[11px] uppercase tracking-wide">
            <th className="px-4 py-3">Buyer</th>
            <th className="px-4 py-3">Last intent</th>
            <th className="px-4 py-3">Interested in</th>
            <th className="px-4 py-3">Consultant</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Updated</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr
              key={lead.session_id}
              onClick={() => onSelect(lead.session_id)}
              className={`border-b border-ink/5 cursor-pointer hover:bg-parchment transition-colors ${
                selectedId === lead.session_id ? "bg-parchment" : ""
              }`}
            >
              <td className="px-4 py-3">
                <div className="font-medium">{lead.buyer_name || "Anonymous visitor"}</div>
                <div className="text-muted text-xs">{lead.buyer_email || lead.session_id}</div>
              </td>
              <td className="px-4 py-3 text-muted">{lead.last_intent?.replaceAll("_", " ") || "—"}</td>
              <td className="px-4 py-3 font-mono text-xs">
                {lead.interested_properties.length > 0 ? lead.interested_properties.join(", ") : "—"}
              </td>
              <td className="px-4 py-3">{lead.assigned_consultant || "—"}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 text-[11px] font-medium rounded-sm ${STATUS_STYLES[lead.status] || ""}`}>
                  {lead.status}
                </span>
              </td>
              <td className="px-4 py-3 text-muted text-xs">
                {new Date(lead.updated_at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
