export default function LeadDetail({ lead }) {
  if (!lead) {
    return (
      <div className="border border-ink/10 bg-white p-10 text-center text-muted text-sm h-full">
        Select a lead to see their conversation, preferences, and match details.
      </div>
    );
  }

  const preferences = lead.preferences || {};

  return (
    <div className="border border-ink/10 bg-white flex flex-col h-full">
      <div className="p-5 border-b border-ink/10">
        <h2 className="font-display text-2xl">{lead.buyer_name || "Anonymous visitor"}</h2>
        <p className="text-sm text-muted mt-1">
          {lead.buyer_email || "No email captured yet"} {lead.buyer_phone ? `· ${lead.buyer_phone}` : ""}
        </p>

        <div className="mt-4 grid grid-cols-2 gap-3 text-xs font-mono">
          <Field label="Status" value={lead.status} />
          <Field label="Assigned consultant" value={lead.assigned_consultant || "Not yet assigned"} />
          <Field label="Interested properties" value={lead.interested_properties.join(", ") || "—"} />
          <Field label="Inferred purpose" value={preferences.purpose || "—"} />
        </div>

        {preferences.tags?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {preferences.tags.map((t) => (
              <span key={t} className="text-[11px] font-mono border border-brass/40 text-brass px-2 py-0.5">
                {t}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-3">
        {lead.messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] px-3 py-2 text-sm ${
                m.role === "user" ? "bg-ink text-parchment" : "bg-parchment text-ink"
              }`}
            >
              <p>{m.content}</p>
              <p className="mt-1 text-[10px] font-mono opacity-60">
                {m.intent?.replaceAll("_", " ")}
                {m.grounded === "false" ? " · ungrounded fallback used" : ""}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div>
      <div className="text-muted uppercase tracking-wide text-[10px]">{label}</div>
      <div className="text-ink mt-0.5">{value}</div>
    </div>
  );
}
