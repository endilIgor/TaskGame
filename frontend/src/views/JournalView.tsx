import { useMemo, useState } from "react";
import { apiGet, apiPatch, apiPost } from "../api/client";
import { DateInput, FormField, MonthInput, SelectInput, TextArea, TextInput } from "../components/FormControls";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { JournalEntry, JournalEntryCreatePayload, JournalEntrySummary, JournalEntryUpdate } from "../types";

function formatLocalIsoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function monthValue(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function readableDate(value: string): string {
  return value.split("-").reverse().join("/");
}

const initialForm = { title: "", entry_date: formatLocalIsoDate(new Date()), mood: "", content: "" };
type JournalFormState = typeof initialForm;

function payloadFromForm(form: JournalFormState): JournalEntryCreatePayload {
  return {
    title: form.title.trim() || null,
    entry_date: form.entry_date,
    mood: form.mood.trim() || null,
    content: form.content.trim(),
  };
}

export function JournalView() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [month, setMonth] = useState(monthValue(new Date()));
  const [form, setForm] = useState(initialForm);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const entries = useAsyncData(() => apiGet<JournalEntrySummary[]>(`/journal/entries?month=${month}`), [month, refreshKey]);
  const selected = useAsyncData(
    () => selectedId === null ? Promise.resolve<JournalEntry | null>(null) : apiGet<JournalEntry>(`/journal/entries/${selectedId}`),
    [selectedId, refreshKey],
  );

  const groupedEntries = useMemo(() => {
    if (entries.status !== "ready") return [];
    return entries.data;
  }, [entries]);

  async function publishEntry(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = payloadFromForm(form);
    if (!payload.content) {
      setError("Escreva algo sobre sua aventura antes de postar.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const created = await apiPost<JournalEntry, JournalEntryCreatePayload>("/journal/entries", payload);
      setForm({ ...initialForm, entry_date: form.entry_date });
      setSelectedId(created.id);
      setRefreshKey((key) => key + 1);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível postar no diário.");
    } finally {
      setBusy(false);
    }
  }

  async function renameSelected(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedId === null || !editingTitle.trim()) return;
    setBusy(true);
    try {
      await apiPatch<JournalEntry, JournalEntryUpdate>(`/journal/entries/${selectedId}`, { title: editingTitle.trim() });
      setEditingTitle("");
      setRefreshKey((key) => key + 1);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível atualizar o título.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="view-page journal-page" aria-labelledby="journal-heading">
      <header className="view-hero journal-hero">
        <span className="section-kicker">Diário de aventureiro</span>
        <h1 className="page-heading" id="journal-heading">Posts da jornada</h1>
        <p>Registre seu dia como um post: dias comuns viram capítulos, aventuras diferentes ganham título próprio.</p>
      </header>

      <div className="journal-layout">
        <form className="panel journal-composer" onSubmit={publishEntry}>
          <div className="section-heading">
            <div>
              <span className="section-kicker">Novo post</span>
              <h2 className="panel-heading">Contar aventura</h2>
            </div>
            <span className="section-count">✎</span>
          </div>
          <div className="journal-composer-grid">
            <FormField className="field-title" label="Título opcional" hint="Se deixar vazio, o título vira o dia automaticamente."><TextInput maxLength={140} placeholder="Aventura diferente" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></FormField>
            <FormField className="field-date" label="Dia"><DateInput required value={form.entry_date} onChange={(value) => setForm({ ...form, entry_date: value })} /></FormField>
            <FormField className="field-mood" label="Clima"><SelectInput value={form.mood} onChange={(event) => setForm({ ...form, mood: event.target.value })}><option value="">Sem clima</option><option value="focado">Focado</option><option value="vitorioso">Vitorioso</option><option value="cansado">Cansado</option><option value="aprendizado">Aprendizado</option></SelectInput></FormField>
          </div>
          <FormField className="field-journal-text" label="Texto do dia" hint="Escreva como um post: o que aconteceu, vitórias, falhas e próximos passos."><TextArea required value={form.content} placeholder="Hoje eu..." onChange={(event) => setForm({ ...form, content: event.target.value })} /></FormField>
          <div className="composer-footer"><span>Seu post fica salvo por dia, mês e ano.</span><button className="button primary" disabled={busy}>Postar no diário</button></div>
        </form>

        <aside className="panel journal-index" aria-label="Arquivo do diário">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Arquivo</span>
              <h2 className="panel-heading">Dias anteriores</h2>
            </div>
            <MonthInput value={month} aria-label="Mês do arquivo" onChange={(value) => { setMonth(value); setSelectedId(null); }} />
          </div>
          {entries.status === "loading" ? <LoadingPanel /> : null}
          {entries.status === "error" ? <ErrorPanel>{entries.error}</ErrorPanel> : null}
          {entries.status === "ready" ? groupedEntries.length ? (
            <div className="journal-timeline">
              {groupedEntries.map((entry) => (
                <button className={`journal-post-card${entry.id === selectedId ? " active" : ""}`} key={entry.id} type="button" onClick={() => setSelectedId(entry.id)}>
                  <time>{readableDate(entry.entry_date)}</time>
                  <strong>{entry.title}</strong>
                  <span>{entry.excerpt}</span>
                  {entry.mood ? <em>{entry.mood}</em> : null}
                </button>
              ))}
            </div>
          ) : <EmptyState>Nenhum post neste mês.</EmptyState> : null}
        </aside>
      </div>

      {error ? <ErrorPanel>{error}</ErrorPanel> : null}

      <section className="panel journal-reader" aria-label="Post selecionado">
        {selected.status === "loading" ? <LoadingPanel /> : null}
        {selected.status === "error" ? <ErrorPanel>{selected.error}</ErrorPanel> : null}
        {selected.status === "ready" && selected.data ? (
          <article className="journal-full-post">
            <div className="section-heading">
              <div>
                <span className="section-kicker">{readableDate(selected.data.entry_date)}</span>
                <h2 className="panel-heading">{selected.data.title}</h2>
              </div>
              {selected.data.mood ? <span className="hero-chip">{selected.data.mood}</span> : null}
            </div>
            <p>{selected.data.content}</p>
            <form className="rename-form" onSubmit={renameSelected}>
              <TextInput maxLength={140} placeholder="Renomear aventura" value={editingTitle} onChange={(event) => setEditingTitle(event.target.value)} />
              <button className="button" disabled={busy || !editingTitle.trim()}>Renomear</button>
            </form>
          </article>
        ) : <EmptyState>Selecione um post para reler sua aventura.</EmptyState>}
      </section>
    </section>
  );
}
