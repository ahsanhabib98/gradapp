import { useState } from "react";
import { Alert, Field } from "../components/ui";
import { useAuth } from "../context";
import { Icon } from "../icons";

/** Password input with a show/hide toggle. */
function PasswordInput({ name, value, onChange, autoComplete }) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="password-input">
      <input type={visible ? "text" : "password"} name={name} value={value} onChange={onChange} required autoComplete={autoComplete} />
      <button
        type="button"
        className="password-toggle"
        onClick={() => setVisible(!visible)}
        aria-label={visible ? "Hide password" : "Show password"}
        aria-pressed={visible}
      >
        <Icon name={visible ? "eyeOff" : "eye"} size={18} />
      </button>
    </div>
  );
}

const EMPTY = { username: "", email: "", first_name: "", last_name: "", password: "", password_confirm: "" };

export default function AuthPage() {
  const { login, register, sessionExpired } = useAuth();
  const [mode, setMode] = useState("login");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState(EMPTY);

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (mode === "register") await register(form);
      else await login(form.username, form.password);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const isLogin = mode === "login";
  return (
    <main className="auth-page">
      <section className="auth-intro">
        <div className="brand brand-light"><span className="brand-mark"><Icon name="school" /></span>GradApp</div>
        <div className="intro-copy">
          <span className="eyebrow">Your graduate journey starts here</span>
          <h1>Find the right program for your future.</h1>
          <p>Discover programs, get personalized recommendations, find potential advisors and funding, and track every deadline in one place.</p>
          <div className="feature-row">
            <span><Icon name="sparkle" /> AI-assisted search</span>
            <span><Icon name="flask" /> Advisor matching</span>
            <span><Icon name="award" /> Funding discovery</span>
          </div>
        </div>
      </section>
      <section className="auth-panel">
        <form className="auth-card" onSubmit={submit}>
          <div className="mobile-brand brand"><span className="brand-mark"><Icon name="school" /></span>GradApp</div>
          <h2>{isLogin ? "Welcome back" : "Create your account"}</h2>
          <p>{isLogin ? "Sign in to continue exploring programs." : "Start building your graduate school plan."}</p>
          {sessionExpired && isLogin && !error && <Alert tone="info">Your session expired. Please sign in again.</Alert>}
          <Alert>{error}</Alert>
          {!isLogin && (
            <div className="form-grid compact">
              <Field label="First name"><input name="first_name" value={form.first_name} onChange={update} required autoComplete="given-name" /></Field>
              <Field label="Last name"><input name="last_name" value={form.last_name} onChange={update} required autoComplete="family-name" /></Field>
              <Field label="Email" full><input type="email" name="email" value={form.email} onChange={update} required autoComplete="email" /></Field>
            </div>
          )}
          <Field label="Username"><input name="username" value={form.username} onChange={update} required autoComplete="username" /></Field>
          <Field label="Password"><PasswordInput name="password" value={form.password} onChange={update} autoComplete={isLogin ? "current-password" : "new-password"} /></Field>
          {!isLogin && (
            <Field label="Confirm password"><PasswordInput name="password_confirm" value={form.password_confirm} onChange={update} autoComplete="new-password" /></Field>
          )}
          <button className="primary wide" disabled={loading}>
            {loading ? "Please wait…" : isLogin ? "Sign in" : "Create account"}<Icon name="arrow" />
          </button>
          <div className="switch">
            {isLogin ? "New to GradApp?" : "Already have an account?"}{" "}
            <button type="button" onClick={() => { setMode(isLogin ? "register" : "login"); setError(""); }}>
              {isLogin ? "Create account" : "Sign in"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
