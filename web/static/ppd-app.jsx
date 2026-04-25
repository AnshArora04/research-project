// PPD Explorer — Methodology + App Shell

function MethodologyPage() {
  const sections = [
    {
      title: 'Data Source',
      body: `This dashboard draws on the Public Plans Database (PPD), a comprehensive panel of U.S. state and local government pension systems maintained by the Center for Retirement Research at Boston College. The underlying paper — Begenau, Liang & Siriwardane (2026, Review of Financial Studies) — constructs a balanced panel of 174 systems with continuous coverage across fiscal years 2001–2021, yielding approximately 3,128 system-year observations.`
    },
    {
      title: 'Key Variable: Omega (ω)',
      body: `Omega is defined as the share of the risky portfolio allocated to alternative investments. The risky portfolio excludes cash and short-duration fixed income; it includes public equities, private equity, hedge funds, real assets (real estate, infrastructure, commodities), and other alternatives. Formally: ω = (Private Equity + Hedge Funds + Real Assets) ÷ (Total Risky Assets). Values range from approximately 8% to 55% across systems and years.`
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
      body: `Each system sets an actuarial assumed rate of return (ARR) used to discount future liabilities. The median ARR declined from approximately 8.0% in 2001 to 7.0% by 2021, reflecting both lower capital market expectations and pressure from actuaries. Higher ARRs mechanically reduce reported liabilities and improve funded ratios; the paper analyzes how ARR choices interact with alternative allocations.`
    },
    {
      title: 'Investment Consultants',
      body: `Investment consultants advise pension boards on asset allocation, manager selection, and risk management. The PPD includes consultant identifiers for a subset of systems. The paper examines whether consultant relationships correlate with higher omega — controlling for fund size, governance quality, and state-level factors. Roughly 57 distinct consultants appear in the full sample; the largest (Callan, NEPC, Meketa, Mercer) collectively advise the majority of AUM.`
    },
    {
      title: 'Net Returns',
      body: `Annual net investment returns are reported net of all fees (management fees, carried interest, administration). Returns are time-weighted and reported in nominal terms. The panel captures full market cycles including the 2001–2002 dot-com bust, the 2008 GFC, and the 2020 COVID shock. Cross-sectional variance in net returns reflects differences in allocation, manager selection, and fee structures.`
    },
    {
      title: 'Sample Construction',
      body: `The 174 systems in the balanced panel were selected to have complete data on omega, funded ratio, and returns across all 21 fiscal years. Systems with missing fiscal year coverage, mid-period mergers, or incomplete alternative allocation disclosures were excluded. The sample skews toward larger, more sophisticated systems — smaller funds are underrepresented. Total sample AUM is approximately $4.5 trillion in FY 2021.`
    },
    {
      title: 'Note on Mock Data',
      body: `All data displayed in this dashboard are synthetic, generated to match the statistical properties reported in Begenau, Liang & Siriwardane (2026): aggregate omega growth from ~15% (2001) to ~35% (2021), funded ratio trends consistent with the 2008 crisis, and return distributions calibrated to plausible capital market outcomes. No actual pension fund data is reproduced. For the real dataset, refer to the PPD at publicplansdata.org or the paper's replication archive.`
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
            159 systems · FY 2001–2021<br />
            Mock data only
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
              Use the sidebar to navigate pages.<br />All data is synthetic mock data.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
