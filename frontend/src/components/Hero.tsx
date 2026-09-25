export function Hero() {
  return (
    <section className="hero-shell">
      <div className="hero-copy">
        <p className="eyebrow hero-eyebrow">Banking Reimagined with Purpose</p>
        <h1>
          Banking <span>Reimagined</span>
          <br />
          with Purpose
        </h1>
        <p className="hero-subtitle">
          Premium digital banking for people who want clarity, control, and thoughtful growth.
        </p>
        <div className="hero-actions">
          <button type="button" className="primary-action">Get started</button>
          <button type="button" className="secondary-action">Learn more</button>
        </div>
        <div className="trust-row">
          {['256-bit Encryption', 'Shariah Certified', 'PCI-DSS Compliant'].map(item => (
            <div key={item} className="trust-badge">
              <span>✓</span>
              {item}
            </div>
          ))}
        </div>
      </div>
      <div className="hero-visual" aria-hidden="true">
        <div className="floating-card">
          <div className="card-topline">
            <span className="chip">LeadPilot</span>
            <span className="chip muted">Premium</span>
          </div>
          <div className="card-number">•••• 1842</div>
          <div className="card-meta">
            <div>
              <small>Cardholder</small>
              <strong>ARHAM K.</strong>
            </div>
            <div>
              <small>Valid thru</small>
              <strong>09/29</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
