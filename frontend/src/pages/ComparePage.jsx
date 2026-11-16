import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Alert, Empty, ExternalLink, Loading, PageHeader, SaveButton, daysLabel, degreeLabel, formatDate, formatMoney } from "../components/ui";
import { useCompare } from "../context";
import { Icon } from "../icons";

function lowest(results, key) {
  const values = results.map((item) => item[key]).filter((value) => value !== null && value !== undefined).map(Number);
  return values.length > 1 ? Math.min(...values) : null;
}

/** Compare Programs use case: side-by-side table of 2-4 programs. */
export default function ComparePage() {
  const { items, remove, clear } = useCompare();
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const ids = items.map((item) => item.id).join(",");

  useEffect(() => {
    if (items.length < 2) { setResults(null); return; }
    let cancelled = false;
    setError("");
    api(`/programs/compare/?ids=${ids}`)
      .then((data) => { if (!cancelled) setResults(data.results); })
      .catch((err) => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids]);

  if (items.length < 2) {
    return (
      <div className="page">
        <PageHeader eyebrow="Compare programs" title="Side-by-side comparison" />
        <Empty icon="compare" title="Select at least two programs" action={<Link className="primary" to="/">Browse programs</Link>}>
          Use the Compare button on any program card or details page. You can compare up to four programs.
        </Empty>
      </div>
    );
  }

  const cheapest = results ? lowest(results, "tuition_per_year") : null;
  const rows = results && [
    ["University", (p) => p.university.name],
    ["Location", (p) => `${p.university.city}, ${p.university.state_or_region}, ${p.university.country}`],
    ["Degree", (p) => degreeLabel(p.degree_level)],
    ["Field", (p) => p.field_of_study],
    ["Tuition / year", (p) => (
      <span className={cheapest !== null && Number(p.tuition_per_year) === cheapest ? "best" : ""}>
        {formatMoney(p.tuition_per_year) || "Not listed"}{cheapest !== null && Number(p.tuition_per_year) === cheapest && " · lowest"}
      </span>
    )],
    ["Minimum GPA", (p) => p.minimum_gpa || "Not listed"],
    ["Application deadline", (p) => p.application_deadline ? <>{formatDate(p.application_deadline)}<small className={p.days_until_deadline < 0 ? "past" : ""}>{daysLabel(p.days_until_deadline)}</small></> : "Not listed"],
    ["Funding", (p) => p.funding_opportunities.length ? (
      <ul className="plain-list">{p.funding_opportunities.map((f) => <li key={f.id}>{f.name}{f.amount ? ` (${formatMoney(f.amount)})` : ""}</li>)}</ul>
    ) : p.funding_available ? "Available (see details)" : "None listed"],
    ["Faculty", (p) => `${p.faculty_count} listed`],
    ["Research areas", (p) => p.top_research_areas.length ? p.top_research_areas.join(", ") : "—"],
    ["Admission requirements", (p) => <span className="small">{p.admission_requirements || "See official site"}</span>],
    ["Last verified", (p) => p.source_retrieved_at ? formatDate(p.source_retrieved_at.slice(0, 10)) : "Not yet verified"],
  ];

  return (
    <div className="page wide-page">
      <PageHeader
        eyebrow="Compare programs"
        title="Side-by-side comparison"
        actions={<button className="secondary" onClick={clear}>Clear comparison</button>}
      >
        Comparing {items.length} programs. Confirm costs and deadlines on each official site before deciding.
      </PageHeader>
      <Alert>{error}</Alert>
      {!results && !error && <Loading label="Building comparison…" />}
      {results && (
        <div className="table-wrap">
          <table className="compare-table">
            <thead>
              <tr>
                <th scope="col"><span className="sr-only">Attribute</span></th>
                {results.map((program) => (
                  <th scope="col" key={program.id}>
                    <Link to={`/programs/${program.id}`}>{program.name}</Link>
                    <div className="compare-head-actions">
                      <SaveButton programId={program.id} compact />
                      <ExternalLink className="icon-button" href={program.program_url} hideIfSample aria-label="Official site"><Icon name="external" size={16} /></ExternalLink>
                      <button className="icon-button" onClick={() => remove(program.id)} aria-label={`Remove ${program.name}`}><Icon name="close" size={16} /></button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(([label, render]) => (
                <tr key={label}>
                  <th scope="row">{label}</th>
                  {results.map((program) => <td key={program.id}>{render(program)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
