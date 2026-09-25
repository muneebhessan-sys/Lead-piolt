export function FloatingCard() {
  return (
    <div className="floating-card floating-card--mini">
      <div className="mini-chart" aria-hidden="true">
        <span className="bar bar-1" />
        <span className="bar bar-2" />
        <span className="bar bar-3" />
        <span className="bar bar-4" />
        <span className="bar bar-5" />
      </div>
      <div>
        <small>Monthly growth</small>
        <strong>+18.4%</strong>
      </div>
    </div>
  );
}
