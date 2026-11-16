import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import {
  Alert,
  CompareButton,
  Loading,
  SaveButton,
  VerifiedBadge,
  daysLabel,
  daysUntil,
  degreeLabel,
  formatDate,
  formatDateTime,
  formatMoney,
  ExternalLink,
  ReviewBadge,
} from "../components/ui";
import { FacultyCard } from "./FacultyPage";
import { FundingCard } from "./FundingPage";
import { useAuth } from "../context";
import { Icon } from "../icons";

const FIELD_LABELS = {
  tuition_per_year: "Tuition",
  application_deadline: "Application deadline",
  minimum_gpa: "Minimum GPA",
  funding_available: "Funding available",
  funding_details: "Funding details",
  admission_requirements: "Admission requirements",
  description: "Description",
};

/** Retrieve Program Information (administrators only). */
function SourcePanel({ program, onUpdated }) {
  const [sources, setSources] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState({ text: "", tone: "info" });

  const load = useCallback(() => {
    api(`/programs/${program.id}/sources/`).then(setSources).catch(() => setSources([]));
  }, [program.id]);
  useEffect(load, [load]);

  async function retrieve() {
    setBusy(true);
    setMessage({ text: "", tone: "info" });
    try {
      const result = await api(`/programs/${program.id}/retrieve/`, { method: "POST", body: {} });
      if (result.snapshot.status !== "success") {
        setMessage({ tone: "error", text: `Retrieval ${result.snapshot.status}: ${result.snapshot.error}` });
      } else {
        const applied = result.snapshot.applied_fields.map((field) => FIELD_LABELS[field] || field);
        setMessage({ tone: "success", text: applied.length ? `Updated: ${applied.join(", ")}.` : "Page retrieved. No changes were found." });
      }
      onUpdated(result.program);
    } catch (err) {
      setMessage({ tone: "error", text: `Retrieval failed: ${err.message}` });
    } finally {
      setBusy(false);
      load();
    }
  }

  return (
    <section className="panel admin-panel">
      <div className="panel-heading">
        <h3><Icon name="refresh" size={18} />Retrieve program information</h3>
        <button className="secondary" onClick={retrieve} disabled={busy}>{busy ? "Retrieving…" : "Retrieve from official site"}</button>
      </div>
      <p className="muted small">Fetches {program.program_url}, extracts tuition, deadline, GPA and funding details, and records a dated snapshot. Visible to administrators only.</p>
      <Alert tone={message.tone}>{message.text}</Alert>
      {sources.length > 0 && (
        <ul className="snapshot-list">
          {sources.map((snapshot) => (
            <li key={snapshot.id}>
              <span className={`badge ${snapshot.status === "success" ? "ok" : "warn"}`}>{snapshot.status}</span>
              <span>{formatDateTime(snapshot.fetched_at)}</span>
              <span className="muted">{snapshot.extraction_method && `${snapshot.extraction_method} extraction`}</span>
              <span className="muted">{snapshot.applied_fields.length ? `changed ${snapshot.applied_fields.length} field(s)` : snapshot.error}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** View Program Details use case. */
export default function ProgramDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [program, setProgram] = useState(null);
  const [faculty, setFaculty] = useState([]);
  const [funding, setFunding] = useState([]);
  const [similar, setSimilar] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setProgram(null);
    setError("");
    Promise.all([
      api(`/programs/${id}/`),
      api(`/faculty/?program=${id}&page_size=50`),
      api(`/funding/?program=${id}&page_size=50`),
      api(`/programs/${id}/similar/`),
    ])
      .then(([programData, facultyData, fundingData, similarData]) => {
        if (cancelled) return;
        setProgram(programData);
        setFaculty(facultyData.results);
        setFunding(fundingData.results);
        setSimilar(similarData);
      })
      .catch((err) => { if (!cancelled) setError(err.status === 404 ? "This program could not be found." : err.message); });
    return () => { cancelled = true; };
  }, [id]);

  if (error) return <div className="page"><Alert>{error}</Alert><Link to="/" className="text-link"><Icon name="back" size={16} />Back to programs</Link></div>;
  if (!program) return <div className="page"><Loading label="Loading program…" /></div>;

  const days = daysUntil(program.application_deadline);
  const { university } = program;

  return (
    <div className="page">
      <Link to="/" className="text-link back-link"><Icon name="back" size={16} />All programs</Link>
      <section className="detail-hero">
        <div className="school-logo large">{university.name.charAt(0)}</div>
        <div className="detail-title">
          <span className="degree-pill">{degreeLabel(program.degree_level)} degree</span>
          <h1>{program.name}</h1>
          <p className="muted">{university.name} · {university.city}, {university.state_or_region}, {university.country}</p>
          <div className="badge-row"><VerifiedBadge program={program} /><ReviewBadge record={program} /></div>
        </div>
        <div className="detail-actions">
          <SaveButton programId={program.id} />
          <CompareButton program={program} />
          <ExternalLink className="primary" href={program.program_url} sampleLabel="Sample program · no official site">Official site<Icon name="external" size={17} /></ExternalLink>
        </div>
      </section>

      {program.origin === "sample" && (
        <Alert tone="info">
          This is a fictional sample program used to demonstrate GradApp. Its university, numbers and links are not real.
          Ask AI about a real university to have GradApp find and save real programs.
        </Alert>
      )}

      <div className="facts-grid">
        <div className="fact"><Icon name="money" /><span>Estimated tuition<strong>{formatMoney(program.tuition_per_year) ? `${formatMoney(program.tuition_per_year)} / year` : "Not listed"}</strong></span></div>
        <div className={`fact ${days !== null && days < 0 ? "past" : days !== null && days <= 14 ? "urgent" : ""}`}>
          <Icon name="calendar" />
          <span>Application deadline<strong>{program.application_deadline ? formatDate(program.application_deadline) : "Not listed"}</strong>{days !== null && <em>{daysLabel(days)}</em>}</span>
        </div>
        <div className="fact"><Icon name="check" /><span>Minimum GPA<strong>{program.minimum_gpa || "Not listed"}</strong></span></div>
        <div className="fact"><Icon name="award" /><span>Funding<strong>{program.funding_available || funding.length ? `${funding.length || "Some"} opportunit${funding.length === 1 ? "y" : "ies"}` : "Not listed"}</strong></span></div>
      </div>

      <div className="detail-grid">
        <div className="detail-main">
          <section className="panel">
            <h3>About this program</h3>
            {program.department && <p className="muted small">{program.department}</p>}
            <p>{program.description || "Program description is not available yet."}</p>
            <h3>Admission requirements</h3>
            <p>{program.admission_requirements || "Visit the official program website for current requirements."}</p>
            {program.funding_details && <><h3>Funding details</h3><p>{program.funding_details}</p></>}
            <p className="muted small"><Icon name="info" size={14} /> Always confirm requirements, costs and deadlines on the official program website.</p>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <h3><Icon name="flask" size={18} />Faculty and potential advisors</h3>
              <Link className="text-link" to="/faculty">Find advisors for your interests<Icon name="arrow" size={16} /></Link>
            </div>
            {faculty.length === 0 ? <p className="muted">No faculty are linked to this program yet.</p> : (
              <div className="card-grid">{faculty.map((member) => <FacultyCard key={member.id} member={member} compact />)}</div>
            )}
          </section>

          <section className="panel">
            <div className="panel-heading">
              <h3><Icon name="award" size={18} />Funding opportunities</h3>
              <Link className="text-link" to="/funding">Search all funding<Icon name="arrow" size={16} /></Link>
            </div>
            {funding.length === 0 ? <p className="muted">No open funding opportunities are listed for this program.</p> : (
              <div className="card-grid">{funding.map((item) => <FundingCard key={item.id} item={item} compact />)}</div>
            )}
          </section>

          {user?.is_staff && <SourcePanel program={program} onUpdated={setProgram} />}
        </div>

        <aside className="detail-side">
          <section className="panel">
            <h3>Location</h3>
            <p><Icon name="location" size={16} /> {university.city}, {university.state_or_region}, {university.country}</p>
            <ExternalLink className="text-link" href={university.website_url} sampleLabel="Fictional sample university">University website<Icon name="external" size={15} /></ExternalLink>
          </section>
          <section className="panel">
            <h3>Similar programs</h3>
            {similar.length === 0 ? <p className="muted small">No similar programs found.</p> : (
              <ul className="link-list">
                {similar.map((item) => (
                  <li key={item.id}>
                    <Link to={`/programs/${item.id}`}>{item.name}</Link>
                    <small>{item.university.name}{formatMoney(item.tuition_per_year) ? ` · ${formatMoney(item.tuition_per_year)}/yr` : ""}</small>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section className="panel">
            <h3>Have a question?</h3>
            <p className="muted small">Ask GradApp's assistant about this program, its funding or faculty.</p>
            <Link className="secondary wide" to={`/ask?q=${encodeURIComponent(`Tell me about the ${program.name} program at ${university.name}`)}`}>
              <Icon name="chat" size={17} />Ask AI
            </Link>
          </section>
        </aside>
      </div>
    </div>
  );
}
