import { useEffect, useRef, useState } from "react";
import { sendChatMessage, getSessionId } from "../lib/api";
import BookingConfirm from "./BookingConfirm";

const WELCOME = {
  role: "assistant",
  content:
    "Hello! I'm the Dar Global property assistant. Ask me about a development, pricing, or say you'd like to book a call with a consultant.",
};

export default function ChatWidget({ prefill, onPrefillConsumed }) {
  const [sessionId] = useState(getSessionId);
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [bookingSlot, setBookingSlot] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (prefill) {
      setInput(prefill);
      onPrefillConsumed?.();
    }
  }, [prefill]);

  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await sendChatMessage({ session_id: sessionId, message: text });
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.reply,
          grounded: res.grounded,
          retrieved_properties: res.retrieved_properties,
          proposed_slots: res.proposed_slots,
          handoff_to_human: res.handoff_to_human,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "I couldn't reach the server. Please make sure the backend is running." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="assistant" className="bg-ink py-24">
      <div className="mx-auto max-w-3xl px-6">
        <p className="font-mono text-xs tracking-[0.25em] text-brass-light uppercase mb-2 text-center">
          AI concierge
        </p>
        <h2 className="font-display text-4xl text-parchment text-center mb-10">Ask about a property</h2>

        <div className="blueprint-corners bg-parchment flex flex-col h-[520px]">
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
            {messages.map((m, i) => (
              <ChatBubble key={i} message={m} sessionId={sessionId} onPickSlot={setBookingSlot} />
            ))}
            {loading && <TypingBubble />}
          </div>

          <form onSubmit={handleSend} className="border-t border-ink/10 p-4 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. 3-bedroom villa in Dubai under $3M"
              className="flex-1 border border-ink/15 px-3 py-2 text-sm focus:border-brass outline-none bg-white"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-ink text-parchment px-5 py-2 text-sm font-semibold hover:bg-brass hover:text-ink transition-colors disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </div>
      </div>

      {bookingSlot && (
        <BookingConfirm
          slot={bookingSlot}
          sessionId={sessionId}
          onClose={() => setBookingSlot(null)}
          onConfirmed={(confirmation) => {
            setBookingSlot(null);
            setMessages((m) => [
              ...m,
              {
                role: "assistant",
                content: `Booked. ${confirmation.consultant_name} will call you at the scheduled time (confirmation ${confirmation.booking_id}). A calendar invite will be sent to your email.`,
              },
            ]);
          }}
        />
      )}
    </section>
  );
}

function ChatBubble({ message, sessionId, onPickSlot }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] ${isUser ? "bg-ink text-parchment" : "bg-white text-ink border border-ink/10"} px-4 py-3 text-sm leading-relaxed`}>
        <p>{message.content}</p>

        {message.retrieved_properties?.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.retrieved_properties.map((p) => (
              <span key={p.id} className="font-mono text-[11px] border border-brass/50 text-brass px-2 py-1">
                {p.id} · {p.name}
              </span>
            ))}
          </div>
        )}

        {message.proposed_slots?.length > 0 && (
          <div className="mt-3 flex flex-col gap-2">
            {message.proposed_slots.map((slot, i) => (
              <button
                key={i}
                onClick={() => onPickSlot(slot)}
                className="text-left border border-brass/40 hover:border-brass hover:bg-parchment px-3 py-2 text-xs transition-colors"
              >
                <span className="font-semibold">{slot.consultant_name}</span>
                {" — "}
                {new Date(slot.slot_start).toLocaleString(undefined, {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })}
                {slot.match_reasons?.length > 0 && (
                  <span className="text-muted"> · fit: {slot.match_reasons.join(", ")}</span>
                )}
              </button>
            ))}
          </div>
        )}

        {message.handoff_to_human && (
          <p className="mt-2 text-[11px] text-brass font-medium">A human consultant has been looped in.</p>
        )}
      </div>
    </div>
  );
}

function TypingBubble() {
  return (
    <div className="flex justify-start">
      <div className="bg-white border border-ink/10 px-4 py-3 text-sm text-muted">Thinking…</div>
    </div>
  );
}
