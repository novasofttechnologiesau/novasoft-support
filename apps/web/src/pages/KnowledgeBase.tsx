import type { KnowledgeArticle, TicketCategory } from "@novasoft/shared";
import { TICKET_CATEGORIES } from "@novasoft/shared";
import { useEffect, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ApiError, api } from "../lib/api";
import { useAuth } from "../lib/auth";

export function KnowledgeBasePage() {
  const { user } = useAuth();
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState<TicketCategory | "">("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setArticles(await api.get<KnowledgeArticle[]>("/knowledge-articles"));
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  async function createArticle() {
    if (!title.trim() || !body.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/knowledge-articles", { title, body, category: category || null });
      setTitle("");
      setBody("");
      setCategory("");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create article");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Knowledge Base</h1>
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          {articles.map((a) => (
            <Card key={a.id} title={a.title}>
              {a.category && <p className="mb-2 text-xs capitalize text-nova-muted">{a.category.replace(/_/g, " ")}</p>}
              <p className="whitespace-pre-wrap text-sm text-nova-text">{a.body}</p>
            </Card>
          ))}
          {articles.length === 0 && <p className="text-sm text-nova-muted">No knowledge base articles yet.</p>}
        </div>

        {(user?.role === "admin" || user?.role === "technician") && (
          <Card title="New Article">
            <div className="space-y-3">
              <input
                placeholder="Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              />
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as TicketCategory)}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              >
                <option value="">No category</option>
                {TICKET_CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
              <textarea
                placeholder="Article body"
                rows={6}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              />
              <Button onClick={createArticle} disabled={submitting} className="w-full justify-center">
                {submitting ? "Saving…" : "Publish"}
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
