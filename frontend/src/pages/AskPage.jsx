import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { Alert, Loading, isSampleUrl } from "../components/ui";
import { Icon } from "../icons";

const SUGGESTIONS = [
  "Which programs offer funding for machine learning research?",
  "Find professors who work on robotics and are accepting students",
  "What scholarships are open to international students?",
  "Tell me about the MS in Computer Science at the University of Houston",
];

const RECORD_LINK = { program: (s) => `/programs/${s.id}` };

function timeAgo(iso) {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? "yesterday" : `${days} days ago`;
}

/** Render answer text, turning references like [P3] or [W1] into links. */
function AnswerText({ text, sources }) {
  const byRef = Object.fromEntries(sources.map((source) => [source.ref, source]));
  return text.split("\n").filter((line) => line.trim() !== "").map((line, lineIndex) => (
    <p key={lineIndex}>
      {line.split(/(\[[PFGW]\d+\])/g).map((part, index) => {
        const ref = part.match(/^\[([PFGW]\d+)\]$/)?.[1];
        if (!ref) return part;
        const source = byRef[ref];
        if (source && RECORD_LINK[source.type]) return <Link key={index} className="ref" to={RECORD_LINK[source.type](source)}>{ref}</Link>;
        if (source?.url && !isSampleUrl(source.url)) return <a key={index} className={`ref ${source.type === "web" ? "web" : ""}`} href={source.url} target="_blank" rel="noreferrer" title={source.title}>{ref}</a>;
        return <span key={index} className="ref">{ref}</span>;
      })}
    </p>
  ));
}

function Sources({ sources }) {
  const web = sources.filter((source) => source.type === "web");
  const records = sources.filter((source) => source.type !== "web");
  const saved = records.filter((source) => source.saved);
  return (
    <>
      {web.length > 0 && (
        <div className="web-sources">
          <span className="sources-label"><Icon name="external" size={13} />Web sources</span>
          <ol>
            {web.map((source) => (
              <li key={source.ref}>
                <span className="ref web">{source.ref}</span>
                <a href={source.url} target="_blank" rel="noreferrer">{source.title}</a>
                <small>{new URL(source.url).hostname.replace(/^www\./, "")}</small>
              </li>
            ))}
          </ol>
        </div>
      )}
      {saved.length > 0 && (
        <div className="saved-note">
          <Icon name="check" size={15} />
          <span>
            Saved to GradApp for future searches ({saved.filter((s) => s.created).length} new, not yet reviewed):{" "}
            {saved.map((source, index) => (
              <span key={source.ref}>
                {index > 0 && ", "}
                {RECORD_LINK[source.type] ? <Link to={RECORD_LINK[source.type](source)}>{source.title}</Link> : source.title}
              </span>
            ))}
          </span>
        </div>
      )}
      {records.length > 0 && saved.length === 0 && (
        <details className="sources">
          <summary>{records.length} GradApp record{records.length === 1 ? "" : "s"}</summary>
          <ul>
            {records.map((source) => (
              <li key={source.ref}>
                <span className="ref">{source.ref}</span>
                {RECORD_LINK[source.type] ? <Link to={RECORD_LINK[source.type](source)}>{source.title}</Link>
                  : source.url && !isSampleUrl(source.url) ? <a href={source.url} target="_blank" rel="noreferrer">{source.title}</a> : source.title}
                <small>{source.type}</small>
              </li>
            ))}
          </ul>
        </details>
      )}
    </>
  );
}

function AssistantMessage({ message, onSearchWeb, canSearchWeb, busy }) {
  const label = message.web_searched ? "Web search" : message.ai_powered ? "GradApp AI" : "Matching records";
  const icon = message.web_searched ? "search" : message.ai_powered ? "sparkle" : "search";
  return (
    <div className="bubble assistant">
      <span className={`bubble-label ${message.web_searched ? "web" : ""}`}><Icon name={icon} size={14} />{label}</span>
      <AnswerText text={message.content} sources={message.sources || []} />
      <Sources sources={message.sources || []} />
      {canSearchWeb && !message.web_searched && onSearchWeb && (
        <button className="text-button" onClick={onSearchWeb} disabled={busy}>
          <Icon name="search" size={14} />Not what you needed? Search the web
        </button>
      )}
    </div>
  );
}

/** Ask AI Questions use case, with saved conversations. */
export default function AskPage() {
  const { conversationId } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [question, setQuestion] = useState(params.get("q") || "");
  const [useProfile, setUseProfile] = useState(true);
  const [sending, setSending] = useState(false);
  const [pending, setPending] = useState(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState({ ai_enabled: null, web_search_enabled: false });
  const [showHistory, setShowHistory] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const endRef = useRef(null);
  const activeId = conversationId ? Number(conversationId) : null;

  const loadConversations = useCallback(() => {
    api("/conversations/?page_size=100")
      .then((data) => setConversations(data.results))
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    api("/ai/status/").then(setStatus).catch(() => setStatus({ ai_enabled: false, web_search_enabled: false }));
    loadConversations();
  }, [loadConversations]);

  // Load the selected conversation's saved messages.
  useEffect(() => {
    setError("");
    setShowHistory(false);
    if (!activeId) { setMessages([]); return; }
    let cancelled = false;
    setLoadingConversation(true);
    api(`/conversations/${activeId}/`)
      .then((data) => { if (!cancelled) setMessages(data.messages); })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 404) navigate("/ask", { replace: true });
        else setError(err.message);
      })
      .finally(() => { if (!cancelled) setLoadingConversation(false); });
    return () => { cancelled = true; };
  }, [activeId, navigate]);

  useEffect(() => { endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" }); }, [messages, pending]);

  // ``retry`` = the "Search the web" button under an answer (the question is already on screen).
  async function send(text, { searchWeb = false, retry = false } = {}) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setSending(true);
    setError("");
    setPending({ question: trimmed, searchWeb, retry });
    if (!retry) setQuestion("");
    try {
      let id = activeId;
      if (!id) {
        const created = await api("/conversations/", { method: "POST", body: {} });
        id = created.id;
      }
      const result = await api(`/conversations/${id}/messages/`, {
        method: "POST",
        body: { question: trimmed, use_profile: useProfile, search_web: searchWeb },
      });
      if (id !== activeId) {
        setMessages(result.messages);
        navigate(`/ask/${id}`, { replace: !activeId });
      } else {
        setMessages((current) => [...current, ...result.messages]);
      }
      setConversations((current) => [result.conversation, ...(current || []).filter((c) => c.id !== id)]);
    } catch (err) {
      setError(err.message);
      if (!retry) setQuestion(trimmed);
    } finally {
      setSending(false);
      setPending(null);
    }
  }

  async function remove(conversation) {
    try {
      await api(`/conversations/${conversation.id}/`, { method: "DELETE" });
      setConversations((current) => current.filter((c) => c.id !== conversation.id));
      setConfirmDelete(null);
      if (conversation.id === activeId) navigate("/ask");
    } catch (err) {
      setError(err.message);
    }
  }

  // Find the student's question that produced a given assistant message.
  const questionBefore = (index) => {
    for (let i = index - 1; i >= 0; i -= 1) if (messages[i].role === "user") return messages[i].content;
    return "";
  };

  const activeTitle = conversations?.find((c) => c.id === activeId)?.title;

  return (
    <div className="chat-layout">
      <aside className={`chat-sidebar ${showHistory ? "open" : ""}`} aria-label="Conversations">
        <button className="primary wide" onClick={() => navigate("/ask")}><Icon name="chat" size={17} />New chat</button>
        <h3>Your chats</h3>
        {!conversations && <Loading label="Loading…" />}
        {conversations?.length === 0 && <p className="muted small">No saved chats yet. Your conversations are saved automatically.</p>}
        <ul className="conversation-list">
          {conversations?.map((conversation) => (
            <li key={conversation.id} className={conversation.id === activeId ? "active" : ""}>
              <Link to={`/ask/${conversation.id}`}>
                <strong>{conversation.title}</strong>
                <small>{timeAgo(conversation.updated_at)} · {conversation.message_count / 2 | 0} question{conversation.message_count === 2 ? "" : "s"}</small>
              </Link>
              {confirmDelete === conversation.id ? (
                <span className="confirm-delete">
                  <button onClick={() => remove(conversation)}>Delete</button>
                  <button onClick={() => setConfirmDelete(null)}>Keep</button>
                </span>
              ) : (
                <button className="icon-button" onClick={() => setConfirmDelete(conversation.id)} aria-label={`Delete chat ${conversation.title}`}>
                  <Icon name="trash" size={15} />
                </button>
              )}
            </li>
          ))}
        </ul>
      </aside>

      <section className="chat-main">
        <div className="chat-header">
          <div>
            <span className="eyebrow">AI assistant</span>
            <h1>{activeId ? activeTitle || "Conversation" : "Ask about programs, faculty and funding"}</h1>
            {!activeId && (
              <p>
                Answers come from GradApp's records first. If they can't answer, the assistant searches the web,
                links its sources, and saves what it finds to GradApp.
              </p>
            )}
          </div>
          <button className="secondary history-toggle" onClick={() => setShowHistory(!showHistory)}>
            <Icon name="chat" size={16} />Chats
          </button>
        </div>

        {status.ai_enabled === false && (
          <Alert tone="info">AI answers and web search are not enabled on this server (no OpenAI API key). You'll still get the best-matching GradApp records.</Alert>
        )}

        <div className="chat" aria-live="polite">
          {loadingConversation && <Loading label="Loading conversation…" />}
          {!activeId && messages.length === 0 && !pending && (
            <div className="chat-empty">
              <Icon name="sparkle" size={30} />
              <p>Try one of these:</p>
              <div className="suggestions">
                {SUGGESTIONS.map((text) => <button key={text} onClick={() => send(text)}>{text}</button>)}
              </div>
            </div>
          )}
          {messages.map((message, index) => (
            message.role === "user"
              ? <div key={message.id} className="bubble user"><p>{message.content}</p></div>
              : (
                <AssistantMessage
                  key={message.id}
                  message={message}
                  busy={sending}
                  canSearchWeb={status.web_search_enabled}
                  onSearchWeb={() => send(questionBefore(index), { searchWeb: true, retry: true })}
                />
              )
          ))}
          {pending && (
            <>
              {!pending.retry && <div className="bubble user"><p>{pending.question}</p></div>}
              <div className="bubble assistant">
                <span className="typing" aria-label="Thinking"><i /><i /><i /></span>
                <small className="muted">
                  {pending.searchWeb ? "Searching the web…" : "Checking GradApp's records (and the web if needed)…"}
                </small>
              </div>
            </>
          )}
          <div ref={endRef} />
        </div>

        <Alert>{error}</Alert>
        <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(question); }}>
          <textarea
            aria-label="Your question"
            value={question}
            maxLength={1000}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(question); } }}
            placeholder={activeId ? "Continue the conversation…" : "Ask a question… (Enter to send, Shift+Enter for a new line)"}
          />
          <div className="chat-input-row">
            <label className="toggle">
              <input type="checkbox" checked={useProfile} onChange={(e) => setUseProfile(e.target.checked)} />
              <span>Use my profile for context</span>
            </label>
            <div className="chat-input-actions">
              {status.web_search_enabled && (
                <button type="button" className="secondary" disabled={sending || !question.trim()} onClick={() => send(question, { searchWeb: true })}>
                  <Icon name="search" size={16} />Search web
                </button>
              )}
              <button className="primary" disabled={sending || !question.trim()}>Send<Icon name="send" size={17} /></button>
            </div>
          </div>
        </form>
        <p className="muted small center">
          The assistant describes fit; it cannot predict admission decisions. Information found on the web is saved as
          “not yet reviewed”. Always verify details on official websites.
        </p>
      </section>
    </div>
  );
}
