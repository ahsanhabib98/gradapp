import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Alert, Empty, ExternalLink, Loading, PageHeader, daysLabel, formatDate } from "../components/ui";
import { Icon } from "../icons";

const KIND = {
  application: { label: "Application", icon: "school" },
  personal: { label: "My target", icon: "user" },
  funding: { label: "Funding", icon: "award" },
};

const GROUPS = [
  ["past", "Passed"],
  ["urgent", "Within 2 weeks"],
  ["soon", "Within 45 days"],
  ["later", "Later"],
];

/** Track Application Deadlines use case. */
export default function DeadlinesPage() {
  const [data, setData] = useState(null);
  const [includePast, setIncludePast] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setData(null);
    api(`/deadlines/${includePast ? "?include_past=true" : ""}`)
      .then((result) => { if (!cancelled) setData(result); })
      .catch((err) => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [includePast]);

  return (
    <div className="page narrow">
      <PageHeader
        eyebrow="Application timeline"
        title="Upcoming deadlines"
        actions={
          <label className="toggle">
            <input type="checkbox" checked={includePast} onChange={(e) => setIncludePast(e.target.checked)} />
            <span>Show passed deadlines</span>
          </label>
        }
      >
        Application deadlines and your own target dates for saved programs, plus related funding deadlines.
      </PageHeader>
      <Alert>{error}</Alert>
      {!data && !error && <Loading label="Loading deadlines…" />}
      {data && data.results.length === 0 && (
        <Empty icon="calendar" title="No upcoming deadlines" action={<Link className="primary" to="/">Find programs to save</Link>}>
          Save programs to see their application and funding deadlines here.
        </Empty>
      )}
      {data && GROUPS.map(([urgency, title]) => {
        const items = data.results.filter((item) => item.urgency === urgency);
        if (!items.length) return null;
        return (
          <section key={urgency} className="timeline-group">
            <h2 className={`timeline-heading ${urgency}`}>{title}</h2>
            <ol className="timeline">
              {items.map((item) => (
                <li key={`${item.kind}-${item.saved_program_id || item.funding_id}-${item.date}`} className={`timeline-item ${urgency} ${item.completed ? "completed" : ""}`}>
                  <div className="date-tile">
                    <strong>{formatDate(item.date).split(",")[0]}</strong>
                    <small>{daysLabel(item.days_left)}</small>
                  </div>
                  <div className="timeline-body">
                    <span className="kind"><Icon name={KIND[item.kind].icon} size={14} />{KIND[item.kind].label}</span>
                    <h3>{item.program_id ? <Link to={`/programs/${item.program_id}`}>{item.title}</Link> : item.title}</h3>
                    <p className="muted small">
                      {item.university_name}
                      {item.status_display && <> · <span className={`status-pill ${item.status}`}>{item.status_display}</span></>}
                    </p>
                  </div>
                  <ExternalLink className="icon-button" href={item.url} hideIfSample aria-label="Open official page"><Icon name="external" size={17} /></ExternalLink>
                </li>
              ))}
            </ol>
          </section>
        );
      })}
      {data?.saved_without_deadline.length > 0 && (
        <section className="panel">
          <h3>Saved programs without a listed deadline</h3>
          <ul className="link-list">
            {data.saved_without_deadline.map((item) => (
              <li key={item.program_id}><Link to={`/programs/${item.program_id}`}>{item.program_name}</Link><small>{item.university_name}</small></li>
            ))}
          </ul>
          <p className="muted small">Set a personal target date on the <Link to="/saved">Saved programs</Link> page, or check the official site.</p>
        </section>
      )}
    </div>
  );
}
