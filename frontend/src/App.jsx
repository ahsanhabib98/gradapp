import React, { useEffect, useMemo, useState } from "react";
import { api, clearSession, getSavedUser, saveSession } from "./api";
import { Icon } from "./icons";

const emptyProfile = {
  intended_degree_level: "masters",
  previous_degree: "",
  previous_field_of_study: "",
  gpa: "",
  academic_interests: "",
  research_interests: "",
  career_goals: "",
  preferred_programs: "",
  preferred_locations: "",
  tuition_budget: "",
  funding_requirement: true,
};

function Field({ label, children, full = false }) {
  return <label className={full ? "field full" : "field"}><span>{label}</span>{children}</label>;
}

function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ username: "", email: "", first_name: "", last_name: "", password: "", password_confirm: "" });

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  async function submit(event) {
    event.preventDefault();
    setLoading(true); setError("");
    try {
      if (mode === "register") {
        await api("/auth/register/", { method: "POST", body: JSON.stringify(form) });
      }
      const data = await api("/auth/login/", { method: "POST", body: JSON.stringify({ username: form.username, password: form.password }) });
      saveSession(data); onLogin(data.user);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  return <main className="auth-page">
    <section className="auth-intro">
      <div className="brand brand-light"><span className="brand-mark"><Icon name="school" /></span>GradApp</div>
      <div className="intro-copy">
        <span className="eyebrow">Your graduate journey starts here</span>
        <h1>Find the right program for your future.</h1>
        <p>Explore graduate programs, compare costs and funding, and make a confident decision in one simple place.</p>
        <div className="feature-row"><span><Icon name="check" /> Easy discovery</span><span><Icon name="check" /> Clear information</span><span><Icon name="check" /> Personal profile</span></div>
      </div>
    </section>
    <section className="auth-panel">
      <form className="auth-card" onSubmit={submit}>
        <div className="mobile-brand brand"><span className="brand-mark"><Icon name="school" /></span>GradApp</div>
        <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
        <p>{mode === "login" ? "Sign in to continue exploring programs." : "Start building your graduate school plan."}</p>
        {error && <div className="alert">{error}</div>}
        {mode === "register" && <div className="form-grid compact">
          <Field label="First name"><input name="first_name" value={form.first_name} onChange={update} required /></Field>
          <Field label="Last name"><input name="last_name" value={form.last_name} onChange={update} required /></Field>
          <Field label="Email" full><input type="email" name="email" value={form.email} onChange={update} required /></Field>
        </div>}
        <Field label="Username"><input name="username" value={form.username} onChange={update} required autoComplete="username" /></Field>
        <Field label="Password"><input type="password" name="password" value={form.password} onChange={update} required autoComplete={mode === "login" ? "current-password" : "new-password"} /></Field>
        {mode === "register" && <Field label="Confirm password"><input type="password" name="password_confirm" value={form.password_confirm} onChange={update} required /></Field>}
        <button className="primary wide" disabled={loading}>{loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}<Icon name="arrow" /></button>
        <div className="switch">{mode === "login" ? "New to GradApp?" : "Already have an account?"} <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>{mode === "login" ? "Create account" : "Sign in"}</button></div>
      </form>
    </section>
  </main>;
}

function ProgramCard({ program, onOpen }) {
  return <article className="program-card">
    <div className="program-top"><div className="school-logo">{program.university.name.charAt(0)}</div><div><span className="degree-pill">{program.degree_level === "masters" ? "Master’s" : "Doctoral"}</span><h3>{program.name}</h3><p className="university">{program.university.name}</p></div></div>
    <div className="program-meta"><span><Icon name="location" />{program.university.city}, {program.university.state_or_region}</span><span><Icon name="money" />{program.tuition_per_year ? `$${Number(program.tuition_per_year).toLocaleString()}/year` : "Contact university"}</span><span><Icon name="calendar" />{program.application_deadline || "Deadline not listed"}</span></div>
    <div className="card-footer"><span className={program.funding_available ? "funding yes" : "funding"}>{program.funding_available ? "Funding available" : "Funding not listed"}</span><button onClick={() => onOpen(program)}>View program <Icon name="arrow" size={17} /></button></div>
  </article>;
}

function ProgramModal({ program, onClose }) {
  if (!program) return null;
  return <div className="modal-backdrop" onMouseDown={onClose}><section className="modal" onMouseDown={(e) => e.stopPropagation()}>
    <button className="icon-button modal-close" onClick={onClose} aria-label="Close"><Icon name="close" /></button>
    <span className="degree-pill">{program.degree_level === "masters" ? "Master’s degree" : "Doctoral degree"}</span>
    <h2>{program.name}</h2><p className="modal-school">{program.university.name} · {program.university.city}, {program.university.state_or_region}</p>
    <div className="modal-facts"><div><Icon name="money" /><span>Estimated tuition<strong>{program.tuition_per_year ? `$${Number(program.tuition_per_year).toLocaleString()} / year` : "Not listed"}</strong></span></div><div><Icon name="calendar" /><span>Application deadline<strong>{program.application_deadline || "Not listed"}</strong></span></div></div>
    <h4>About this program</h4><p>{program.description || "Program description is not available yet."}</p>
    <h4>Admission requirements</h4><p>{program.admission_requirements || "Visit the official program website for current requirements."}</p>
    {program.funding_available && <div className="funding-box"><Icon name="check" /><div><strong>Funding available</strong><p>{program.funding_details || "Funding opportunities may be available through the department."}</p></div></div>}
    <a className="primary link-button" href={program.program_url} target="_blank" rel="noreferrer">Visit official program <Icon name="arrow" /></a>
  </section></div>;
}

function Profile({ onClose }) {
  const [profile, setProfile] = useState(emptyProfile);
  const [status, setStatus] = useState("");
  useEffect(() => { api("/auth/profile/").then((data) => setProfile({ ...emptyProfile, ...data })).catch((e) => setStatus(e.message)); }, []);
  const update = (e) => setProfile({ ...profile, [e.target.name]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  async function save(e) {
    e.preventDefault(); setStatus("Saving…");
    const payload = { ...profile, gpa: profile.gpa || null, tuition_budget: profile.tuition_budget || null };
    delete payload.id; delete payload.user; delete payload.created_at; delete payload.updated_at;
    try { const data = await api("/auth/profile/", { method: "PATCH", body: JSON.stringify(payload) }); setProfile({ ...emptyProfile, ...data }); setStatus("Profile saved successfully."); }
    catch (err) { setStatus(err.message); }
  }
  return <div className="modal-backdrop"><section className="modal profile-modal"><button className="icon-button modal-close" onClick={onClose}><Icon name="close" /></button><h2>Your student profile</h2><p>Tell us what you are looking for. You can update this anytime.</p>
    <form className="form-grid" onSubmit={save}>
      <Field label="Intended degree"><select name="intended_degree_level" value={profile.intended_degree_level} onChange={update}><option value="masters">Master’s</option><option value="doctoral">Doctoral</option><option value="other">Other</option></select></Field>
      <Field label="Current GPA"><input type="number" min="0" max="4" step="0.01" name="gpa" value={profile.gpa ?? ""} onChange={update} /></Field>
      <Field label="Previous degree"><input name="previous_degree" value={profile.previous_degree} onChange={update} placeholder="B.S. Computer Science" /></Field>
      <Field label="Previous field"><input name="previous_field_of_study" value={profile.previous_field_of_study} onChange={update} /></Field>
      <Field label="Academic interests" full><textarea name="academic_interests" value={profile.academic_interests} onChange={update} placeholder="AI, data science, software engineering…" /></Field>
      <Field label="Career goals" full><textarea name="career_goals" value={profile.career_goals} onChange={update} /></Field>
      <Field label="Preferred locations"><input name="preferred_locations" value={profile.preferred_locations} onChange={update} placeholder="Texas, California…" /></Field>
      <Field label="Annual tuition budget"><input type="number" min="0" name="tuition_budget" value={profile.tuition_budget ?? ""} onChange={update} /></Field>
      <label className="checkbox full"><input type="checkbox" name="funding_requirement" checked={profile.funding_requirement} onChange={update} /><span>I need funding opportunities</span></label>
      <div className="form-actions full"><span className="save-status">{status}</span><button className="primary">Save profile</button></div>
    </form>
  </section></div>;
}

function Dashboard({ user, onLogout }) {
  const [programs, setPrograms] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState({ search: "", degree_level: "", funding_available: "", max_tuition: "" });

  async function loadPrograms() {
    setLoading(true); setError("");
    const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value !== ""));
    try { const data = await api(`/programs/?${query}`); setPrograms(Array.isArray(data) ? data : data.results || []); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadPrograms(); }, []);
  const greeting = useMemo(() => user?.first_name || user?.username || "Student", [user]);

  return <div className="app-shell">
    <header><div className="brand"><span className="brand-mark"><Icon name="school" /></span>GradApp</div><nav><button className="nav-active">Discover</button><button onClick={() => setShowProfile(true)}>My profile</button></nav><div className="user-menu"><span className="avatar">{greeting.charAt(0).toUpperCase()}</span><span>{greeting}</span><button className="icon-button" onClick={onLogout} title="Sign out"><Icon name="logout" /></button></div></header>
    <main className="dashboard">
      <section className="hero"><span className="eyebrow">Graduate program discovery</span><h1>Find a program that fits <em>you.</em></h1><p>Search by program, location, funding, and tuition to narrow your options.</p>
        <form className="search-bar" onSubmit={(e) => { e.preventDefault(); loadPrograms(); }}><Icon name="search" /><input value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} placeholder="Search programs, fields, or universities" /><button>Search</button></form>
      </section>
      <section className="content">
        <aside className="filters"><div className="filter-heading"><h3>Filters</h3><button onClick={() => setFilters({ search: "", degree_level: "", funding_available: "", max_tuition: "" })}>Clear</button></div>
          <Field label="Degree level"><select value={filters.degree_level} onChange={(e) => setFilters({ ...filters, degree_level: e.target.value })}><option value="">All degrees</option><option value="masters">Master’s</option><option value="doctoral">Doctoral</option></select></Field>
          <Field label="Funding"><select value={filters.funding_available} onChange={(e) => setFilters({ ...filters, funding_available: e.target.value })}><option value="">Any</option><option value="true">Funding available</option><option value="false">No funding listed</option></select></Field>
          <Field label="Maximum annual tuition"><input type="number" placeholder="$40,000" value={filters.max_tuition} onChange={(e) => setFilters({ ...filters, max_tuition: e.target.value })} /></Field>
          <button className="secondary wide" onClick={loadPrograms}>Apply filters</button>
        </aside>
        <section className="results"><div className="results-heading"><div><h2>Graduate programs</h2><p>{loading ? "Loading programs…" : `${programs.length} program${programs.length === 1 ? "" : "s"} found`}</p></div><button className="profile-prompt" onClick={() => setShowProfile(true)}><Icon name="user" /><span><strong>Improve your results</strong>Complete your profile</span><Icon name="arrow" /></button></div>
          {error && <div className="alert">{error}</div>}
          {!loading && !error && programs.length === 0 && <div className="empty"><Icon name="search" size={32} /><h3>No programs found</h3><p>Try changing your search or filters.</p></div>}
          <div className="program-list">{programs.map((program) => <ProgramCard key={program.id} program={program} onOpen={setSelected} />)}</div>
        </section>
      </section>
    </main>
    <footer><div className="brand"><span className="brand-mark"><Icon name="school" /></span>GradApp</div><p>Making graduate program discovery simpler.</p><span>DevCave</span></footer>
    <ProgramModal program={selected} onClose={() => setSelected(null)} />
    {showProfile && <Profile onClose={() => setShowProfile(false)} />}
  </div>;
}

export default function App() {
  const [user, setUser] = useState(() => getSavedUser());
  function logout() { clearSession(); setUser(null); }
  return user ? <Dashboard user={user} onLogout={logout} /> : <Auth onLogin={setUser} />;
}
