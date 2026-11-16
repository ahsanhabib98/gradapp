import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, query } from "../api";
import { Alert, Empty, ExternalLink, Loading, PageHeader, Pagination, ReviewBadge } from "../components/ui";
import { Icon } from "../icons";

const ACCEPTING = {
  true: { label: "Accepting students", className: "ok" },
  false: { label: "Not accepting students", className: "muted-badge" },
  null: { label: "Availability unknown", className: "muted-badge" },
};

export function FacultyCard({ member, compact = false }) {
  const accepting = ACCEPTING[String(member.accepting_students)];
  const matched = new Set((member.matched_areas || []).map((area) => area.toLowerCase()));
  return (
    <article className="info-card">
      <div className="info-card-top">
        <div className="avatar large" aria-hidden="true">{member.name.replace("Dr. ", "").charAt(0)}</div>
        <div>
          <h4>{member.name}</h4>
          <p className="muted small">{[member.title, member.department].filter(Boolean).join(", ")}</p>
          {!compact && <p className="muted small">{member.university.name}</p>}
          <ReviewBadge record={member} />
        </div>
        {member.match_score !== undefined && <span className="match-score" title="Share of your interests this person researches">{member.match_score}% match</span>}
      </div>
      <div className="chips">
        {member.research_area_list.map((area) => (
          <span key={area} className={matched.has(area.toLowerCase()) ? "chip matched" : "chip"}>{area}</span>
        ))}
      </div>
      {!compact && member.bio && <p className="small">{member.bio}</p>}
      <div className="info-card-footer">
        <span className={`badge ${accepting.className}`}>{accepting.label}</span>
        <div className="inline-links">
          {member.email && !member.email.endsWith(".example") && <a href={`mailto:${member.email}`} aria-label={`Email ${member.name}`}><Icon name="mail" size={16} /></a>}
          <ExternalLink href={member.profile_url}>Profile<Icon name="external" size={14} /></ExternalLink>
        </div>
      </div>
      {!compact && member.programs.length > 0 && (
        <p className="small muted">Programs: {member.programs.map((program, index) => (
          <span key={program.id}>{index > 0 && ", "}<Link to={`/programs/${program.id}`}>{program.name}</Link></span>
        ))}</p>
      )}
    </article>
  );
}

/** View Faculty Profiles use case, including advisor matching against the student's profile. */
export default function FacultyPage() {
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({ search: "", match_profile: "", accepting_students: "" });
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ results: [], count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    api(`/faculty/${query({ ...filters, page: page > 1 ? page : "" })}`)
      .then((result) => { if (!cancelled) setData(result); })
      .catch((err) => { if (!cancelled) { setError(err.message); setData({ results: [], count: 0 }); } })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [filters, page]);

  const update = (next) => { setFilters({ ...filters, ...next }); setPage(1); };

  return (
    <div className="page">
      <PageHeader eyebrow="Professors and advisors" title="Find potential advisors">
        Browse faculty research areas, or match faculty against the research interests in your profile.
      </PageHeader>
      <form className="toolbar" role="search" onSubmit={(e) => { e.preventDefault(); update({ search }); }}>
        <div className="toolbar-search">
          <Icon name="search" />
          <input aria-label="Search faculty" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name, research area or university" />
        </div>
        <button className="primary">Search</button>
        <label className="toggle">
          <input type="checkbox" checked={filters.match_profile === "true"} onChange={(e) => update({ match_profile: e.target.checked ? "true" : "" })} />
          <span>Match my research interests</span>
        </label>
        <label className="toggle">
          <input type="checkbox" checked={filters.accepting_students === "true"} onChange={(e) => update({ accepting_students: e.target.checked ? "true" : "" })} />
          <span>Accepting students</span>
        </label>
      </form>
      {error && (
        <Alert>
          {error} {error.includes("profile") && <Link to="/profile">Update your profile</Link>}
        </Alert>
      )}
      {loading ? <Loading label="Loading faculty…" /> : (
        <>
          <p className="muted small">{data.count} faculty member{data.count === 1 ? "" : "s"}{filters.match_profile ? " matching your interests, best match first" : ""}</p>
          {data.results.length === 0 && !error ? (
            <Empty icon="flask" title="No faculty found">Try a broader research area, or add more interests to your profile.</Empty>
          ) : (
            <div className="card-grid three">{data.results.map((member) => <FacultyCard key={member.id} member={member} />)}</div>
          )}
        </>
      )}
      <Pagination page={page} count={data.count} onChange={setPage} />
    </div>
  );
}
