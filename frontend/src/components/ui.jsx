import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useCompare, useSaved } from "../context";
import { Icon } from "../icons";

/* ------------------------------------------------------------ formatting */

export function formatMoney(value) {
  if (value === null || value === undefined || value === "") return null;
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

/** Format an ISO date (YYYY-MM-DD) without timezone shifts. */
export function formatDate(iso) {
  if (!iso) return null;
  const [year, month, day] = String(iso).slice(0, 10).split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function formatDateTime(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" });
}

export function daysUntil(iso) {
  if (!iso) return null;
  const [year, month, day] = String(iso).slice(0, 10).split("-").map(Number);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((new Date(year, month - 1, day) - today) / 86400000);
}

export function daysLabel(days) {
  if (days === null || days === undefined) return "";
  if (days < 0) return `${Math.abs(days)} day${days === -1 ? "" : "s"} ago`;
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  return `in ${days} days`;
}

export function degreeLabel(level) {
  return { masters: "Master’s", doctoral: "Doctoral", other: "Other graduate" }[level] || level;
}

/* ------------------------------------------------------------ links */

/** Sample data uses reserved ".example" domains that never resolve to a real website. */
export function isSampleUrl(url) {
  if (!url) return false;
  try {
    return new URL(url).hostname.endsWith(".example");
  } catch {
    return false;
  }
}

/**
 * Link to an outside website. For fictional sample records it renders a
 * clearly-labelled, non-clickable marker instead of a link that cannot load.
 * - ``hideIfSample``: render nothing for sample URLs (icon-only buttons).
 * - ``sampleLabel``: text to show instead of ``children`` for sample URLs.
 */
export function ExternalLink({ href, className = "", children, hideIfSample = false, sampleLabel, ...rest }) {
  if (!href) return null;
  if (isSampleUrl(href)) {
    if (hideIfSample) return null;
    return (
      <span className={`${className} sample-link`} title="Sample data: this fictional record has no real website." aria-disabled="true">
        {sampleLabel || children}
        {!sampleLabel && <small>sample</small>}
      </span>
    );
  }
  return <a className={className} href={href} target="_blank" rel="noreferrer" {...rest}>{children}</a>;
}

/* ------------------------------------------------------------ primitives */

export function Field({ label, children, full = false, hint }) {
  return (
    <label className={full ? "field full" : "field"}>
      <span>{label}</span>
      {children}
      {hint && <small className="hint">{hint}</small>}
    </label>
  );
}

export function Alert({ children, tone = "error" }) {
  if (!children) return null;
  return <div className={`alert ${tone}`} role={tone === "error" ? "alert" : "status"}>{children}</div>;
}

export function Loading({ label = "Loading…" }) {
  return <div className="loading" role="status"><span className="spinner" aria-hidden="true" />{label}</div>;
}

export function Empty({ icon = "search", title, children, action }) {
  return (
    <div className="empty">
      <Icon name={icon} size={32} />
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}

export function PageHeader({ eyebrow, title, children, actions }) {
  return (
    <section className="page-header">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        {children && <p>{children}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </section>
  );
}

export function Pagination({ page, count, pageSize = 20, onChange }) {
  const pages = Math.ceil(count / pageSize);
  if (pages <= 1) return null;
  return (
    <nav className="pagination" aria-label="Pagination">
      <button className="secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}><Icon name="chevronLeft" size={16} />Previous</button>
      <span>Page {page} of {pages}</span>
      <button className="secondary" disabled={page >= pages} onClick={() => onChange(page + 1)}>Next<Icon name="chevronRight" size={16} /></button>
    </nav>
  );
}

/** Modal dialog that closes on Escape and on backdrop click. */
export function Modal({ title, onClose, children, wide = false }) {
  useEffect(() => {
    const onKey = (event) => { if (event.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <section className={wide ? "modal wide" : "modal"} role="dialog" aria-modal="true" aria-label={title} onMouseDown={(e) => e.stopPropagation()}>
        <button className="icon-button modal-close" onClick={onClose} aria-label="Close"><Icon name="close" /></button>
        {children}
      </section>
    </div>
  );
}

/* ------------------------------------------------------------ programs */

export function SaveButton({ programId, compact = false }) {
  const { isSaved, toggle } = useSaved();
  const [busy, setBusy] = useState(false);
  const saved = isSaved(programId);
  async function onClick() {
    setBusy(true);
    await toggle(programId);
    setBusy(false);
  }
  return (
    <button
      type="button"
      className={`chip-button ${saved ? "active" : ""}`}
      onClick={onClick}
      disabled={busy}
      aria-pressed={saved}
      title={saved ? "Remove from saved programs" : "Save program"}
    >
      <Icon name={saved ? "bookmarkFilled" : "bookmark"} size={16} />
      {!compact && (saved ? "Saved" : "Save")}
    </button>
  );
}

export function CompareButton({ program }) {
  const { has, toggle, full } = useCompare();
  const selected = has(program.id);
  return (
    <button
      type="button"
      className={`chip-button ${selected ? "active" : ""}`}
      onClick={() => toggle(program)}
      disabled={!selected && full}
      aria-pressed={selected}
      title={!selected && full ? "You can compare up to 4 programs" : "Add to comparison"}
    >
      <Icon name="compare" size={16} />{selected ? "Comparing" : "Compare"}
    </button>
  );
}

export function ProgramCard({ program, extra }) {
  const days = daysUntil(program.application_deadline);
  return (
    <article className="program-card">
      <div className="program-top">
        <div className="school-logo">{program.university.name.charAt(0)}</div>
        <div className="program-heading">
          <span className="degree-pill">{degreeLabel(program.degree_level)}</span>
          <h3><Link to={`/programs/${program.id}`}>{program.name}</Link></h3>
          <p className="university">{program.university.name}</p>
          <ReviewBadge record={program} />
        </div>
        <SaveButton programId={program.id} compact />
      </div>
      {extra}
      <div className="program-meta">
        <span><Icon name="location" />{program.university.city}, {program.university.state_or_region}</span>
        <span><Icon name="money" />{formatMoney(program.tuition_per_year) ? `${formatMoney(program.tuition_per_year)}/year` : "Tuition not listed"}</span>
        <span className={days !== null && days < 0 ? "past" : ""}>
          <Icon name="calendar" />
          {program.application_deadline ? `${formatDate(program.application_deadline)}${days < 0 ? " (passed)" : ""}` : "Deadline not listed"}
        </span>
      </div>
      <div className="card-footer">
        <span className={program.funding_available || program.funding_count ? "funding yes" : "funding"}>
          {program.funding_available || program.funding_count ? "Funding available" : "Funding not listed"}
        </span>
        <div className="card-actions">
          <CompareButton program={program} />
          <Link className="text-link" to={`/programs/${program.id}`}>View program <Icon name="arrow" size={17} /></Link>
        </div>
      </div>
    </article>
  );
}

/** Shown on records the AI found on the web that an administrator has not reviewed yet. */
export function ReviewBadge({ record }) {
  if (!record?.needs_review) return null;
  return (
    <span className="badge warn" title="Found automatically by web search. Check the official source before relying on it.">
      <Icon name="alert" size={14} />From web search · not yet reviewed
    </span>
  );
}

/** Small "last verified" badge for retrieved program information. */
export function VerifiedBadge({ program }) {
  if (!program.source_retrieved_at) {
    return <span className="badge warn"><Icon name="info" size={14} />Not yet verified from official site</span>;
  }
  return (
    <span className={`badge ${program.is_stale ? "warn" : "ok"}`}>
      <Icon name={program.is_stale ? "alert" : "shield"} size={14} />
      {program.is_stale ? "Verified over 90 days ago" : "Verified"} {formatDate(program.source_retrieved_at.slice(0, 10))}
    </span>
  );
}
