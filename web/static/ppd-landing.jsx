// PPD Explorer — Landing Page (real PPD data, no hardcoded numbers)

function LandingPage({ navigate }) {
  const {
    LANDING_DATA, SUB_ALLOC, TOTAL_AUM, TOTAL_AUM_EXACT, SYSTEM_COUNT, ANALYTIC_OBS,
    AGG_OMEGA, CONSULTANT_COUNT, YEARS,
  } = window.PPDData;
  const {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
    CartesianGrid, ReferenceLine,
  } = Recharts;

  const fyFirst = YEARS[0];
  const fyLast  = YEARS[YEARS.length - 1];
  const omegaStart = AGG_OMEGA[0];
  const omegaEnd   = AGG_OMEGA[AGG_OMEGA.length - 1];
  const omegaGrowth = (omegaEnd - omegaStart).toFixed(1);

  // Sub-allocation sparkline data — built from real per-year SUB_ALLOC bake.
  const subAllocData = YEARS.map((year, i) => ({
    year: String(year),
    realAssets:    SUB_ALLOC.realAssets[i],
    privateEquity: SUB_ALLOC.privateEquity[i],
    hedgeFunds:    SUB_ALLOC.hedgeFunds[i],
  }));

  const navItems = [
    { page: 'system',      icon: '◉', label: 'System Deep Dive',
      desc: `Drill into any of ${SYSTEM_COUNT} funds — allocations, returns, funding trajectories, and peer comparison.` },
    { page: 'consultant',  icon: '◈', label: 'Consultant Analysis',
      desc: 'Compare investment advisors by client AUM, count, and average alternative allocations.' },
    { page: 'state',       icon: '◫', label: 'State & Regional',
      desc: 'Rank states by omega, compare funding health, and chart geographic adoption patterns.' },
    { page: 'methodology', icon: '≡', label: 'Methodology',
      desc: 'Variable definitions, sample construction, and data source documentation.' },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 8px' }}>

      {/* Eyebrow */}
      <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', marginBottom: 10 }}>
        ◈ &nbsp; Research Tool &nbsp;·&nbsp; Begenau, Liang &amp; Siriwardane (2026, RFS)
      </div>

      {/* Title */}
      <h1 style={{ fontFamily: window.mono, color: window.C.textPrimary, fontSize: 30, fontWeight: 700, margin: '0 0 8px', letterSpacing: '-0.01em', lineHeight: 1.15 }}>
        American Public<br />Pension Explorer
      </h1>
      <p style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 14, margin: '0 0 28px', lineHeight: 1.7, maxWidth: 600 }}>
        U.S. public defined-benefit pension funds steadily shifted their risky portfolios toward
        alternatives over {fyFirst}–{fyLast}. Explore that transformation across {SYSTEM_COUNT} systems
        — allocation trends, funding trajectories, consultant relationships, and state-level comparisons.
      </p>

      {/* Hero Chart */}
      <div style={{
        background: window.C.card, border: `1px solid ${window.C.border}`,
        padding: '22px 24px 16px', marginBottom: 20,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
          <div>
            <div style={{ fontFamily: window.mono, color: window.C.textPrimary, fontSize: 13, fontWeight: 600, letterSpacing: '0.03em' }}>
              Alternative-to-Risky Share (Omega, ω)
            </div>
            <div style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 12, marginTop: 3 }}>
              AUM-weighted aggregate, FY {fyFirst}–{fyLast} &nbsp;·&nbsp; Figure 2c in paper
            </div>
          </div>
          <div style={{ fontFamily: window.mono, textAlign: 'right' }}>
            <div style={{ color: window.C.blue, fontSize: 24, fontWeight: 700, lineHeight: 1 }}>{omegaEnd.toFixed(1)}%</div>
            <div style={{ color: window.C.textMuted, fontSize: 10, marginTop: 3 }}>{fyLast} aggregate</div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={230}>
          <AreaChart data={LANDING_DATA} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="omegaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={window.C.blue} stopOpacity={0.28} />
                <stop offset="95%" stopColor={window.C.blue} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} interval={2} />
            <YAxis tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} domain={[10, 45]} width={38} />
            <Tooltip content={<window.CustomTooltip fmt={v => v.toFixed(1) + '%'} />} />
            <ReferenceLine x="2012" stroke={window.C.border} strokeDasharray="4 4"
              label={{ value: 'low-yield era begins', fill: window.C.textMuted, fontSize: 9, fontFamily: window.mono, position: 'insideTopRight' }} />
            <Area type="monotone" dataKey="avgOmega" name="Avg. Omega"
              stroke={window.C.blue} strokeWidth={2.5} fill="url(#omegaGrad)"
              dot={false} activeDot={{ r: 4, fill: window.C.blue, stroke: window.C.bg }} />
          </AreaChart>
        </ResponsiveContainer>
        <div style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 11, marginTop: 10, paddingTop: 10, borderTop: `1px solid ${window.C.border}`, lineHeight: 1.6 }}>
          AUM-weighted alternative share rose <span style={{ color: window.C.textPrimary }}>+{omegaGrowth} pp</span> from {fyFirst} to {fyLast}.
          Post-2012 acceleration coincides with the prolonged low-yield environment.
        </div>
      </div>

      {/* Sub-allocation strip — sparklines built from real per-year SUB_ALLOC */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 20 }}>
        {[
          { key: 'realAssets',    label: 'Real Assets',    color: window.C.green  },
          { key: 'privateEquity', label: 'Private Equity', color: window.C.purple },
          { key: 'hedgeFunds',    label: 'Hedge Funds',    color: window.C.sky    },
        ].map(({ key, label, color }) => {
          const series = SUB_ALLOC[key];
          const startVal = series[0];
          const endVal   = series[series.length - 1];
          return (
            <div key={key} style={{ background: window.C.card, border: `1px solid ${window.C.border}`, padding: '14px 16px' }}>
              <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>{label} — share of total AUM</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
                <span style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 12 }}>{startVal.toFixed(1)}%</span>
                <span style={{ fontFamily: window.mono, color: color, fontSize: 18, fontWeight: 600 }}>{endVal.toFixed(1)}%</span>
              </div>
              <ResponsiveContainer width="100%" height={44}>
                <AreaChart data={subAllocData} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id={`sg${key}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={color} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey={key} stroke={color} strokeWidth={1.5} fill={`url(#sg${key})`} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          );
        })}
      </div>

      {/* KPI strip */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 32 }}>
        <window.KPITile
          label={`Sample AUM (${fyLast})`}
          value={window.dollars(TOTAL_AUM_EXACT)}
          sub={`${SYSTEM_COUNT} systems in the panel`}
          accent={window.C.blue}
        />
        <window.KPITile
          label="System-Years"
          value={ANALYTIC_OBS.toLocaleString()}
          sub={`${SYSTEM_COUNT} systems × FY ${fyFirst}–${fyLast} balanced panel`}
          accent={window.C.sky}
        />
        <window.KPITile
          label="Omega Growth"
          value={`+${omegaGrowth}pp`}
          sub={`${omegaStart.toFixed(1)}% (${fyFirst}) → ${omegaEnd.toFixed(1)}% (${fyLast})`}
          accent={window.C.green}
        />
        <window.KPITile
          label="Consultants"
          value={String(CONSULTANT_COUNT)}
          sub="Distinct general investment consultants in panel"
          accent={window.C.purple}
        />
      </div>

      {/* Nav cards */}
      <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 14, paddingBottom: 8, borderBottom: `1px solid ${window.C.border}` }}>
        Explore the Data
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 36 }}>
        {navItems.map(n => (
          <button key={n.page} onClick={() => navigate(n.page)} style={{
            background: window.C.card, border: `1px solid ${window.C.border}`,
            padding: '18px 22px', textAlign: 'left', cursor: 'pointer',
            transition: 'border-color 0.15s, box-shadow 0.15s', display: 'block', width: '100%',
          }}
          onMouseEnter={e => { e.currentTarget.style.borderColor = window.C.blue; e.currentTarget.style.boxShadow = window.C.glowBlue; }}
          onMouseLeave={e => { e.currentTarget.style.borderColor = window.C.border; e.currentTarget.style.boxShadow = 'none'; }}
          >
            <div style={{ fontFamily: window.mono, color: window.C.blue, fontSize: 16, marginBottom: 6 }}>{n.icon}</div>
            <div style={{ fontFamily: window.mono, color: window.C.textPrimary, fontSize: 13, fontWeight: 600, marginBottom: 6 }}>{n.label}</div>
            <div style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 12, lineHeight: 1.55 }}>{n.desc}</div>
          </button>
        ))}
      </div>

      {/* Attribution */}
      <div style={{ paddingTop: 18, borderTop: `1px solid ${window.C.border}`, fontFamily: window.sans, color: window.C.textMuted, fontSize: 11, lineHeight: 1.8 }}>
        Data: <span style={{ color: window.C.textPrimary }}>Public Plans Database</span> (Center for Retirement Research, Boston College) ·
        Research: <span style={{ color: window.C.textPrimary }}>Begenau, Liang &amp; Siriwardane (2026)</span>, <em>The Rise of Alternatives</em>, <em>Review of Financial Studies</em> ·
        Consultant data: Andonov, Bonetti &amp; Stefanescu (2025).
      </div>
    </div>
  );
}

Object.assign(window, { LandingPage });
