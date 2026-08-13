import { useState } from "react";
import { bookSlot } from "../lib/api";

export default function BookingConfirm({ slot, sessionId, onClose, onConfirmed }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const start = new Date(slot.slot_start);
  const formatted = start.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

  async function handleConfirm(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const confirmation = await bookSlot({
        session_id: sessionId,
        consultant_id: slot.consultant_id,
        slot_start: slot.slot_start,
        buyer_name: name,
        buyer_email: email,
        buyer_phone: phone || null,
      });
      onConfirmed(confirmation);
    } catch (err) {
      setError("That slot may no longer be available. Please pick another time.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-ink/60 flex items-center justify-center p-4">
      <div className="bg-white max-w-sm w-full p-6 blueprint-corners">
        <p className="font-mono text-[11px] tracking-wider text-brass uppercase">Confirm your call</p>
        <h3 className="font-display text-2xl mt-1">{slot.consultant_name}</h3>
        <p className="text-sm text-muted mt-1">{formatted}</p>

        <form onSubmit={handleConfirm} className="mt-5 flex flex-col gap-3">
          <input
            required
            placeholder="Full name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="border border-ink/15 px-3 py-2 text-sm focus:border-brass outline-none"
          />
          <input
            required
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="border border-ink/15 px-3 py-2 text-sm focus:border-brass outline-none"
          />
          <input
            placeholder="Phone (optional)"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="border border-ink/15 px-3 py-2 text-sm focus:border-brass outline-none"
          />
          {error && <p className="text-xs text-red-700">{error}</p>}
          <div className="flex gap-2 mt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-ink text-parchment text-sm font-semibold py-2 hover:bg-brass hover:text-ink transition-colors disabled:opacity-50"
            >
              {loading ? "Booking…" : "Confirm booking"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 text-sm font-medium text-muted hover:text-ink transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
