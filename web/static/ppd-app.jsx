// PPD Explorer — Methodology + App Shell

function MethodologyPage() {
  const {
    SYSTEM_COUNT, CONSULTANT_COUNT, ANALYTIC_OBS, TOTAL_AUM_EXACT,
    YEARS, ARR_TREND, OMEGA_RANGE, TOP_CONSULTANTS,
  } = window.PPDData;
  const fyFirst = YEARS[0];
  const fyLast  = YEARS[YEARS.length - 1];
  const nYears  = YEARS.length;
  const totalAumStr = TOTAL_AUM_EXACT >= 1000
    ? `$${(TOTAL_AUM_EXACT / 1000).toFixed(2)} trillion`
    : `$${TOTAL_AUM_EXACT.toFixed(0)} billion`;
  const topConsultantsStr = TOP_CONSULTANTS.slice(0, 4).join(', ');

  const sections = [
    {
      title: 'Data Source',
      body: `This dashboard draws on the Public Plans Database (PPD), a comprehensive panel of U.S. state and local government pension systems maintained by the Center for Retirement Research at Boston College. The underlying paper — Begenau, Liang & Siriwardane (2026, Review of Financial Studies) — uses fiscal years ${fyFirst}–${fyLast}. The panel exposed by this dashboard contains ${SYSTEM_COUNT} systems and ${ANALYTIC_OBS.toLocaleString()} system-year observations with non-zero target-allocation reporting.`
    },
    {
      title: 'Key Variable: Omega (ω)',
      body: `Omega is defined as the share of the risky portfolio allocated to alternative investments. The risky portfolio excludes cash and short-duration fixed income; it includes public equities, private equity, hedge funds, real assets (real estate, infrastructure, commodities), and other alternatives. Formally: ω = (Private Equity + Hedge Funds + Real Assets) ÷ (Total Risky Assets). In this panel, ω ranges from ${OMEGA_RANGE.min.toFixed(1)}% to ${OMEGA_RANGE.max.toFixed(1)}% across all system-years.`
    },
    {
      title: 'Asset Allocation Categories',
      body: `Target allocations are reported in annual CAFRs (Comprehensive Annual Financial Reports) and PPD filings. Five categories are tracked: Public Equity (domestic + international equity), Fixed Income (investment-grade bonds, TIPS, cash equivalents), Private Equity (buyouts, venture capital, growth equity), Hedge Funds (absolute return, multi-strategy, macro), Real Assets (real estate, infrastructure, commodities, natural resources). Categories sum to 100% of total assets.`
    },
    {
      title: 'Funded Ratio',
      body: `The actuarial funded ratio is reported under GASB accounting standards: Actuarial Assets ÷ Actuarial Liabilities. Values above 100% indicate a surplus; values below 80% are commonly considered underfunded. The 2008 Global Financial Crisis caused a sharp, near-universal decline in funded ratios. Many systems have not fully recovered to pre-crisis levels. Note that the GASB 67/68 standards (adopted 2014–2015) changed liability discount rate rules, creating a structural break in some series.`
    },
    {
      title: 'Assumed Rate of Return',
      body: `Each system sets an actuarial assumed rate of return (ARR) used to discount future liabilities. In this panel, the AUM-weighted average ARR declined from ${ARR_TREND.firstValue.toFixed(2)}% in ${ARR_TREND.firstFy} to ${ARR_TREND.lastValue.toFixed(2)}% in ${ARR_TREND.lastFy}, reflecting lower capital market expectations and actuarial pressure. Higher ARRs mechanically reduce reported liabilities and improve funded ratios; the paper analyzes how ARR choices interact with alternative allocations.`
    },
    {
      title: 'Investment Consultants',
      body: `Investment consultants advise pension boards on asset allocation, manager selection, and risk management. The PPD includes consultant identifiers for a subset of systems. The paper examines whether consultant relationships correlate with higher omega — controlling for fund size, governance quality, and state-level factors. ${CONSULTANT_COUNT} distinct general investment consultants appear in this panel; the largest by client AUM are ${topConsultantsStr}.`
    },
    {
      title: 'Net Returns',
      body: `Annual net investment returns are reported net of all fees (management fees, carried interest, administration). Returns are time-weighted and reported in nominal terms. The panel captures full market cycles including the 2001–2002 dot-com bust, the 2008 GFC, and the 2020 COVID shock. Cross-sectional variance in net returns reflects differences in allocation, manager selection, and fee structures.`
    },
    {
      title: 'Sample Construction',
      body: `${SYSTEM_COUNT} systems are tracked across ${nYears} fiscal years (${fyFirst}–${fyLast}). The cleaning pipeline drops plan-level rows whose target/actual weight sums diverge from 1 by more than 5pp, requires non-missing target allocations, and aggregates to the system level (AUM-weighted). Total panel AUM in ${fyLast} is approximately ${totalAumStr}.`
    },
    {
      title: 'Data Provenance',
      body: `All values shown in this dashboard come from the cleaned Public Plans Database parquet (output_python/ppd_plan_level_clean.parquet) via the dashboard.lib.aggregations layer. Per-system-year metrics are AUM-weighted aggregations of the underlying plan rows. Numbers are computed at server start by web/bake_data.py and served as a single static JS bundle — no synthetic data is generated.`
    },
  ];

  return (
    <div style={{ maxWidth: 780, margin: '0 auto', padding: '0 8px' }}>
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 6 }}>Documentation</div>
        <h1 style={{ fontFamily: window.mono, color: window.C.textPrimary, fontSize: 22, fontWeight: 700, margin: '0 0 10px' }}>Methodology & Data Sources</h1>
        <p style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 13, margin: 0, lineHeight: 1.7 }}>
          Reference guide for variables, data sources, and sample construction behind the PPD Explorer.
          Cite as: Begenau, J., Liang, J., & Siriwardane, E. (2026). The Rise of Alternatives. <em>Review of Financial Studies</em>.
        </p>
      </div>

      {sections.map((s, i) => (
        <div key={i} style={{ marginBottom: 32 }}>
          <div style={{
            fontFamily: window.mono, color: window.C.blue, fontSize: 12, fontWeight: 600,
            textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10,
            paddingBottom: 8, borderBottom: `1px solid ${window.C.border}`,
          }}>
            <span style={{ color: window.C.textMuted, marginRight: 10 }}>{String(i + 1).padStart(2, '0')}</span>
            {s.title}
          </div>
          <p style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 13, lineHeight: 1.8, margin: 0 }}>
            {s.body}
          </p>
        </div>
      ))}

      <div style={{ marginTop: 40, padding: '20px 22px', background: window.C.card, border: `1px solid ${window.C.border}`, borderLeft: `3px solid ${window.C.blue}` }}>
        <div style={{ fontFamily: window.mono, color: window.C.blue, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Citation</div>
        <p style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 12, lineHeight: 1.7, margin: 0 }}>
          Begenau, J., Liang, J., &amp; Siriwardane, E. (2026). The Rise of Alternatives.
          <em style={{ color: window.C.textPrimary }}> Review of Financial Studies</em>.
          Public Plans Database: publicplansdata.org
        </p>
      </div>
    </div>
  );
}

// ─── Main App Shell ───────────────────────────────────────────────────────────

function App() {
  const [page, setPage] = React.useState('landing');
  const [tweaksOpen, setTweaksOpen] = React.useState(false);
  const [glowEnabled, setGlowEnabled] = React.useState(true);
  const [compactMode, setCompactMode] = React.useState(false);
  const { SYSTEM_COUNT, YEARS } = window.PPDData;
  const fyFirst = YEARS[0];
  const fyLast  = YEARS[YEARS.length - 1];

  React.useEffect(() => {
    window.addEventListener('message', e => {
      if (e.data?.type === '__activate_edit_mode') setTweaksOpen(true);
      if (e.data?.type === '__deactivate_edit_mode') setTweaksOpen(false);
    });
    window.parent.postMessage({ type: '__edit_mode_available' }, '*');
  }, []);

  const navItems = [
    { id: 'landing', label: 'Overview', sub: 'Rise of Alternatives' },
    { id: 'system', label: 'System Deep Dive', sub: 'Single-fund explorer' },
    { id: 'consultant', label: 'Consultant Analysis', sub: 'Advisor comparison' },
    { id: 'state', label: 'State & Regional', sub: 'Geographic view' },
    { id: 'methodology', label: 'Methodology', sub: 'Data & definitions' },
  ];

  const pages = { landing: LandingPage, system: SystemDeepDivePage, consultant: ConsultantPage, state: StateRegionalPage, methodology: MethodologyPage };
  const PageComponent = pages[page] || LandingPage;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: window.C.bg, color: window.C.textPrimary }}>
      {/* Sidebar */}
      <nav style={{
        width: 220, flexShrink: 0, background: window.C.surface,
        borderRight: `1px solid ${window.C.border}`,
        display: 'flex', flexDirection: 'column',
        position: 'sticky', top: 0, height: '100vh', overflowY: 'auto',
      }}>
        {/* Logo */}
        <div style={{ padding: '24px 20px 20px', borderBottom: `1px solid ${window.C.border}` }}>
          <div style={{ fontFamily: window.mono, color: window.C.blue, fontSize: 18, fontWeight: 700, letterSpacing: '-0.01em', lineHeight: 1 }}>
            PPD
          </div>
          <div style={{ fontFamily: window.mono, color: window.C.blue, fontSize: 18, fontWeight: 700, letterSpacing: '-0.01em' }}>
            Explorer
          </div>
          <div style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 10, marginTop: 6, lineHeight: 1.5 }}>
            Begenau, Liang &amp;<br />Siriwardane (2026)
          </div>
        </div>

        {/* Nav */}
        <div style={{ padding: '12px 0', flex: 1 }}>
          {navItems.map(n => {
            const active = page === n.id;
            return (
              <button key={n.id} onClick={() => setPage(n.id)} style={{
                display: 'block', width: '100%', textAlign: 'left',
                background: active ? 'rgba(59,130,246,0.1)' : 'transparent',
                borderLeft: active ? `3px solid ${window.C.blue}` : '3px solid transparent',
                boxShadow: active && glowEnabled ? `inset 0 0 20px rgba(59,130,246,0.08)` : 'none',
                border: 'none',
                padding: '11px 16px 11px 17px',
                cursor: 'pointer', transition: 'all 0.15s',
              }}
              onMouseEnter={e => { if (!active) e.currentTarget.style.background = 'rgba(59,130,246,0.05)'; }}
              onMouseLeave={e => { if (!active) e.currentTarget.style.background = 'transparent'; }}
              >
                <div style={{ fontFamily: window.mono, color: active ? window.C.textPrimary : window.C.textMuted, fontSize: 12, fontWeight: active ? 600 : 400, marginBottom: 2 }}>{n.label}</div>
                <div style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 10, opacity: 0.8 }}>{n.sub}</div>
              </button>
            );
          })}
        </div>

        {/* Footer */}
        <div style={{ padding: '16px 20px', borderTop: `1px solid ${window.C.border}` }}>
          <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 9, lineHeight: 1.6 }}>
            {SYSTEM_COUNT} systems · FY {fyFirst}–{fyLast}<br />
            Real PPD data
          </div>
        </div>
      </nav>

      {/* Main content */}
      <main style={{ flex: 1, padding: compactMode ? '28px 28px' : '36px 40px', overflowX: 'hidden', minWidth: 0 }}>
        <PageComponent navigate={setPage} />
      </main>

      {/* Tweaks Panel */}
      {tweaksOpen && (
        <div style={{
          position: 'fixed', bottom: 24, right: 24, width: 260,
          background: window.C.card, border: `1px solid ${window.C.blue}`,
          boxShadow: window.C.glowBlue, zIndex: 1000,
          fontFamily: window.mono,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: `1px solid ${window.C.border}` }}>
            <span style={{ color: window.C.textPrimary, fontSize: 12, fontWeight: 600 }}>Tweaks</span>
            <button onClick={() => { setTweaksOpen(false); window.parent.postMessage({ type: '__edit_mode_dismissed' }, '*'); }} style={{ background: 'none', border: 'none', color: window.C.textMuted, cursor: 'pointer', fontSize: 16 }}>×</button>
          </div>
          <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: window.C.textMuted, fontSize: 11, cursor: 'pointer' }}>
              <span>Glow effects</span>
              <input type="checkbox" checked={glowEnabled} onChange={e => setGlowEnabled(e.target.checked)} style={{ accentColor: window.C.blue }} />
            </label>
            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: window.C.textMuted, fontSize: 11, cursor: 'pointer' }}>
              <span>Compact padding</span>
              <input type="checkbox" checked={compactMode} onChange={e => setCompactMode(e.target.checked)} style={{ accentColor: window.C.blue }} />
            </label>
            <div style={{ color: window.C.textMuted, fontSize: 10, borderTop: `1px solid ${window.C.border}`, paddingTop: 10, lineHeight: 1.5 }}>
              Use the sidebar to navigate pages.<br />Data: real PPD parquet, baked at server start.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
