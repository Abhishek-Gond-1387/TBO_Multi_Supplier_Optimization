import { useEffect, useState } from "react";

type ReviewItem = {
  id: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  score: number;
  left: { name?: string; destination?: string };
  right: { name?: string; destination?: string };
};

type Props = { apiBase?: string };

export function MatchReviewQueue({ apiBase = "http://127.0.0.1:8000/api/v1" }: Props) {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      const response = await fetch(`${apiBase}/review-queue?status=PENDING`);
      if (!response.ok) throw new Error(`Could not load queue (${response.status})`);
      const data = await response.json();
      setItems(data.items);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load review queue");
    }
  }

  async function decide(id: string, status: "APPROVED" | "REJECTED") {
    const response = await fetch(`${apiBase}/review-queue/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (!response.ok) {
      setError(`Could not save decision (${response.status})`);
      return;
    }
    setItems((current) => current.filter((item) => item.id !== id));
  }

  useEffect(() => { void refresh(); }, [apiBase]);

  return (
    <section aria-labelledby="review-heading">
      <h2 id="review-heading">Potential duplicate matches</h2>
      {error && <p role="alert">{error}</p>}
      {!error && items.length === 0 && <p>No pending matches to review.</p>}
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <strong>{item.left.name ?? "Unnamed listing"}</strong>
            <span> ↔ </span>
            <strong>{item.right.name ?? "Unnamed listing"}</strong>
            <small> Similarity {Math.round(item.score * 100)}%</small>
            <button type="button" onClick={() => void decide(item.id, "APPROVED")}>Link listings</button>
            <button type="button" onClick={() => void decide(item.id, "REJECTED")}>Keep separate</button>
          </li>
        ))}
      </ul>
    </section>
  );
}
