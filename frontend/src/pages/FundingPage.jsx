import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, query } from "../api";
import { Alert, Empty, ExternalLink, Field, Loading, PageHeader, Pagination, ReviewBadge, daysLabel, formatDate, formatMoney } from "../components/ui";
import { Icon } from "../icons";

export function FundingCard({ item, compact = false }) {
  const where = item.university?.name || item.provider || "External provider";
  return (
    <article className="info-card">
      <div className="info-card-top">
        <div className="icon-tile" aria-hidden="true"><Icon name="award" /></div>
        <div>
          <span className="degree-pill">{item.funding_type_display}</span>
          <h4>{item.name}</h4>
          {!compact && <p className="muted small">{where}</p>}
          <ReviewBadge record={item} />
        </div>
      </div>
      <p className="amount">
        {formatMoney(item.amount) || "Amount varies"} <small>{item.amount_note}</small>
      </p>
      <div className="chips">
        {item.covers_tuition && <span className="chip matched">Covers tuition</span>}
        <span className="chip">{item.international_eligible ? "International students eligible" : "Domestic students only"}</span>
        {item.program && <Link className="chip link" to={`/programs/${item.program.id}`}>{item.program.name}</Link>}
      </div>
      {!compact && item.eligibility && <p className="small"><strong>Eligibility:</strong> {item.eligibility}</p>}
      <div className="info-card-footer">
        <span className={`badge ${item.days_left !== null && item.days_left <= 14 ? "warn" : "neutral"}`}>
          <Icon name="calendar" size={14} />
          {item.deadline ? `${formatDate(item.deadline)} (${daysLabel(item.days_left)})` : "Rolling / no deadline"}
        </span>
        <ExternalLink href={item.url}>Details<Icon name="external" size={14} /></ExternalLink>
      </div>
    </article>
  );
}

const EMPTY = { search: "", funding_type: "", degree_level: "", international_eligible: "", covers_tuition: "", min_amount: "", open_only: "true", ordering: "" };

/** Search Funding use case. */
export default function FundingPage() {
  const [form, setForm] = useState(EMPTY);
  const [filters, setFilters] = useState(EMPTY);
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ results: [], count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    const params = { ...filters, open_only: filters.open_only || "false", page: page > 1 ? page : "" };
    api(`/funding/${query(params)}`)
      .then((result) => { if (!cancelled) setData(result); })
      .catch((err) => { if (!cancelled) { setError(err.message); setData({ results: [], count: 0 }); } })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [filters, page]);

  const set = (key) => (event) => setForm({ ...form, [key]: event.target.type === "checkbox" ? (event.target.checked ? "true" : "") : event.target.value });
  const apply = (event) => { event?.preventDefault(); setFilters(form); setPage(1); };

  return (
    <div className="page">
      <PageHeader eyebrow="Funding and scholarships" title="Search funding opportunities">
        Assistantships, fellowships, scholarships and grants from universities and outside organizations.
      </PageHeader>
      <div className="content tight">
        <form className="filters" onSubmit={apply} aria-label="Funding filters">
          <div className="filter-heading">
            <h3>Filters</h3>
            <button type="button" onClick={() => { setForm(EMPTY); setFilters(EMPTY); setPage(1); }}>Clear</button>
          </div>
          <Field label="Keywords"><input value={form.search} onChange={set("search")} placeholder="e.g. research, computing" /></Field>
          <Field label="Type">
            <select value={form.funding_type} onChange={set("funding_type")}>
              <option value="">All types</option>
              <option value="assistantship">Assistantship</option>
              <option value="fellowship">Fellowship</option>
              <option value="scholarship">Scholarship</option>
              <option value="grant">Grant</option>
              <option value="other">Other</option>
            </select>
          </Field>
          <Field label="Degree level">
            <select value={form.degree_level} onChange={set("degree_level")}>
              <option value="">Any</option>
              <option value="masters">Master’s</option>
              <option value="doctoral">Doctoral</option>
            </select>
          </Field>
          <Field label="Minimum amount"><input type="number" min="0" step="500" value={form.min_amount} onChange={set("min_amount")} placeholder="$5,000" /></Field>
          <Field label="Sort by">
            <select value={form.ordering} onChange={set("ordering")}>
              <option value="">Deadline</option>
              <option value="amount">Largest amount</option>
              <option value="name">Name</option>
            </select>
          </Field>
          <label className="checkbox"><input type="checkbox" checked={form.international_eligible === "true"} onChange={set("international_eligible")} /><span>Open to international students</span></label>
          <label className="checkbox"><input type="checkbox" checked={form.covers_tuition === "true"} onChange={set("covers_tuition")} /><span>Covers tuition</span></label>
          <label className="checkbox"><input type="checkbox" checked={form.open_only === "true"} onChange={set("open_only")} /><span>Only open deadlines</span></label>
          <button className="secondary wide">Apply filters</button>
        </form>
        <section className="results">
          <Alert>{error}</Alert>
          {loading ? <Loading label="Loading funding…" /> : (
            <>
              <p className="muted small">{data.count} opportunit{data.count === 1 ? "y" : "ies"} found</p>
              {data.results.length === 0 && !error ? (
                <Empty icon="award" title="No funding found">Try removing some filters or including closed deadlines.</Empty>
              ) : (
                <div className="card-grid">{data.results.map((item) => <FundingCard key={item.id} item={item} />)}</div>
              )}
            </>
          )}
          <Pagination page={page} count={data.count} onChange={setPage} />
        </section>
      </div>
    </div>
  );
}
