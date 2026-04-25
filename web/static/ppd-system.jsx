// PPD Explorer — System Deep Dive Page

function SystemDeepDivePage() {
  const { SYSTEMS, AGG_OMEGA, YEARS } = window.PPDData;
  const [query, setQuery] = React.useState('');
  // Default to the largest fund by AUM so first paint shows a real, named system
  const defaultId = React.useMemo(
    () => [...SYSTEMS].sort((a, b) => b.aumB - a.aumB)[0]?.id || SYSTEMS[0]?.id,
    [SYSTEMS]
  );
  const [selectedId, setSelectedId] = React.useState(defaultId);
  const [showDropdown, setShowDropdown] = React.useState(false);
  const fyFirst = YEARS[0];
  const fyLast  = YEARS[YEARS.length - 1];
  const {
    AreaChart, Area, LineChart, Line, BarChart, Bar,
    ComposedChart, XAxis, YAxis, Tooltip, Legend,
    ResponsiveContainer, CartesianGrid, Cell
  } = Recharts;

  const system = SYSTEMS.find(s => s.id === selectedId) || SYSTEMS[0];
  const consultant = window.PPDData.CONSULTANTS.find(c => c.id === system.consultantId);

  // Filter systems for dropdown
  const filtered = React.useMemo(() => {
    const q = query.toLowerCase();
    if (!q) return SYSTEMS;
    return SYSTEMS.filter(s =>
      s.name.toLowerCase().includes(q) ||
      s.stateCode.toLowerCase().includes(q) ||
      s.stateName.toLowerCase().includes(q)
    );
  }, [query]);

  // Group filtered by state
  const grouped = React.useMemo(() => {
    const map = {};
    filtered.forEach(s => {
      if (!map[s.stateCode]) map[s.stateCode] = { name: s.stateName, systems: [] };
      map[s.stateCode].systems.push(s);
    });
    return Object.entries(map).sort((a, b) => a[0].localeCompare(b[0]));
  }, [filtered]);

  const latestYear = system.years[system.years.length - 1];
  const firstYear = system.years[0];

  // Peer comparison data
  const peerData = YEARS.map((year, i) => ({
    year: String(year),
    omega: system.years[i].omega,
    peer: AGG_OMEGA[i],
  }));

  // Allocation over time
  const allocData = system.years.map(y => ({
    year: String(y.year),
    'Public Equity': y.allocation.publicEquity,
    'Fixed Income': y.allocation.fixedIncome,
    'Private Equity': y.allocation.privateEquity,
    'Hedge Funds': y.allocation.hedgeFunds,
    'Real Assets': y.allocation.realAssets,
  }));

  // Funding + assumed return
  const fundingData = system.years.map(y => ({
    year: String(y.year),
    fundedRatio: y.fundedRatio,
    assumedReturn: y.assumedReturn,
  }));

  // Annual net returns
  const returnData = system.years.map(y => ({
    year: String(y.year),
    netReturn: y.netReturn,
  }));

  const peerAvgOmegaLatest = AGG_OMEGA[AGG_OMEGA.length - 1];
  const omegaDelta = latestYear.omega - firstYear.omega;
  const aboveBelow = latestYear.omega >= peerAvgOmegaLatest ? 'above' : 'below';

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 8px' }}>
      {/* Page header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 6 }}>System Deep Dive</div>
        <h1 style={{ fontFamily: window.mono, color: window.C.textPrimary, fontSize: 22, fontWeight: 700, margin: 0 }}>Single-Fund Explorer</h1>
      </div>

      {/* Search selector */}
      <div style={{ marginBottom: 28, position: 'relative' }}>
        <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Select Pension System</div>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            value={query || system.name}
            onChange={e => { setQuery(e.target.value); setShowDropdown(true); }}
            onFocus={() => { setQuery(''); setShowDropdown(true); }}
            onBlur={() => setTimeout(() => setShowDropdown(false), 180)}
            placeholder="Search by system name or state..."
            style={{
              width: '100%', boxSizing: 'border-box',
              background: window.C.card, border: `1px solid ${window.C.blue}`,
              color: window.C.textPrimary, fontFamily: window.mono, fontSize: 13,
              padding: '11px 16px', outline: 'none',
              boxShadow: window.C.glowBlue,
            }}
          />
          {showDropdown && (
            <div style={{
              position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 100,
              background: '#090E1A', border: `1px solid ${window.C.border}`,
              maxHeight: 320, overflowY: 'auto',
              boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
            }}>
              {grouped.slice(0, 20).map(([code, grp]) => (
                <div key={code}>
                  <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, padding: '6px 14px 4px', textTransform: 'uppercase', letterSpacing: '0.08em', background: window.C.surface, borderBottom: `1px solid ${window.C.border}` }}>
                    {grp.name}
                  </div>
                  {grp.systems.map(s => (
                    <div key={s.id}
                      onMouseDown={() => { setSelectedId(s.id); setQuery(''); setShowDropdown(false); }}
                      style={{
                        padding: '9px 16px', fontFamily: window.sans, fontSize: 13,
                        color: s.id === selectedId ? window.C.blue : window.C.textPrimary,
                        background: s.id === selectedId ? 'rgba(59,130,246,0.1)' : 'transparent',
                        cursor: 'pointer', borderBottom: `1px solid ${window.C.border}`,
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(59,130,246,0.07)'}
                      onMouseLeave={e => e.currentTarget.style.background = s.id === selectedId ? 'rgba(59,130,246,0.1)' : 'transparent'}
                    >
                      <span>{s.name}</span>
                      <span style={{ color: window.C.textMuted, fontSize: 11, marginLeft: 10 }}>${s.aumB}B</span>
                    </div>
                  ))}
                </div>
              ))}
              {grouped.length === 0 && (
                <div style={{ padding: '14px 16px', color: window.C.textMuted, fontFamily: window.sans, fontSize: 13 }}>No systems match your search.</div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* KPI Tiles */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 32 }}>
        <window.KPITile
          label={`Latest Omega (${fyLast})`}
          value={window.pct(latestYear.omega)}
          sub={`Alt. share of risky portfolio — ${aboveBelow} peer avg of ${window.pct(peerAvgOmegaLatest)}`}
          accent={window.C.blue}
        />
        <window.KPITile
          label={`Funded Ratio (${fyLast})`}
          value={window.pct(latestYear.fundedRatio)}
          sub="Actuarial assets ÷ actuarial liabilities (GASB basis)"
          accent={latestYear.fundedRatio >= 80 ? window.C.green : latestYear.fundedRatio >= 65 ? window.C.sky : window.C.red}
        />
        <window.KPITile
          label="Investment Consultant"
          value={consultant ? consultant.name.split(' ')[0] : 'None'}
          sub={consultant ? `${consultant.clientCount} clients · $${consultant.totalAUM}B AUM` : 'No external investment consultant'}
          accent={window.C.purple}
        />
      </div>

      {/* Allocation stacked area */}
      <window.SectionHeader>Target Allocation Over Time</window.SectionHeader>
      <window.ChartShell
        title="Portfolio Allocation by Asset Class"
        insight={`${system.name.split(' ').slice(0, 2).join(' ')} expanded its alternatives share from ${window.pct(firstYear.omega)} in ${fyFirst} to ${window.pct(latestYear.omega)} in ${fyLast} — a ${omegaDelta > 0 ? '+' : ''}${omegaDelta.toFixed(1)}pp shift ${aboveBelow} the ${window.pct(peerAvgOmegaLatest)} peer average.`}
        height={260}
      >
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={allocData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <defs>
              {['#3B82F6','#38BDF8','#A78BFA','#34D399','#FB923C'].map((col, i) => (
                <linearGradient key={i} id={`ag${i}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={col} stopOpacity={0.7} />
                  <stop offset="95%" stopColor={col} stopOpacity={0.4} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} interval={4} />
            <YAxis tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} width={38} />
            <Tooltip content={<window.CustomTooltip fmt={v => v.toFixed(1) + '%'} />} />
            <Legend wrapperStyle={{ fontFamily: window.mono, fontSize: 10, color: window.C.textMuted }} />
            {['Public Equity','Fixed Income','Private Equity','Hedge Funds','Real Assets'].map((k, i) => (
              <Area key={k} type="monotone" dataKey={k} stackId="1"
                stroke={window.C.chartColors[i]} fill={`url(#ag${i})`} strokeWidth={1.5} dot={false} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </window.ChartShell>

      {/* Omega vs peer */}
      <window.SectionHeader>Alternative Share vs Peer Average</window.SectionHeader>
      <window.ChartShell
        title="Omega (ω) — System vs All-Fund Average"
        insight={`The fund's alternative share has grown ${omegaDelta > 0 ? 'faster' : 'slower'} than the peer average since ${fyFirst}, ending ${Math.abs(latestYear.omega - peerAvgOmegaLatest).toFixed(1)}pp ${aboveBelow} the cross-sectional mean in ${fyLast}.`}
        height={240}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={peerData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} interval={4} />
            <YAxis tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} width={38} />
            <Tooltip content={<window.CustomTooltip fmt={v => v.toFixed(1) + '%'} />} />
            <Legend wrapperStyle={{ fontFamily: window.mono, fontSize: 10, color: window.C.textMuted }} />
            <Line type="monotone" dataKey="omega" name="This Fund" stroke={window.C.blue} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
            <Line type="monotone" dataKey="peer" name="Peer Avg" stroke={window.C.sky} strokeWidth={1.5} strokeDasharray="5 4" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </window.ChartShell>

      {/* Funded ratio + assumed return */}
      <window.SectionHeader>Funding Status</window.SectionHeader>
      <window.ChartShell
        title="Funded Ratio & Assumed Return"
        insight={`Funded ratio moved from ${window.pct(firstYear.fundedRatio)} (${fyFirst}) to ${window.pct(latestYear.fundedRatio)} (${fyLast}), while the assumed return moved from ${window.pct(firstYear.assumedReturn)} to ${window.pct(latestYear.assumedReturn)} as boards adjusted expectations post-GFC.`}
        height={240}
      >
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={fundingData} margin={{ top: 4, right: 48, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} interval={4} />
            <YAxis yAxisId="left" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} width={38} domain={[40, 110]} />
            <YAxis yAxisId="right" orientation="right" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} width={38} domain={[6, 9]} />
            <Tooltip content={<window.CustomTooltip fmt={v => v.toFixed(1) + '%'} />} />
            <Legend wrapperStyle={{ fontFamily: window.mono, fontSize: 10, color: window.C.textMuted }} />
            <Area yAxisId="left" type="monotone" dataKey="fundedRatio" name="Funded Ratio" stroke={window.C.sky} fill="rgba(56,189,248,0.12)" strokeWidth={2} dot={false} />
            <Line yAxisId="right" type="monotone" dataKey="assumedReturn" name="Assumed Return" stroke={window.C.purple} strokeWidth={1.8} strokeDasharray="4 3" dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </window.ChartShell>

      {/* Net returns */}
      <window.SectionHeader>Annual Performance</window.SectionHeader>
      <window.ChartShell
        title="Annual Net Return (%)"
        insight={(() => {
          const valid = returnData.filter(d => d.netReturn != null);
          if (!valid.length) return 'Net returns not available for this fund.';
          const worst = valid.reduce((a, b) => b.netReturn < a.netReturn ? b : a);
          const best  = valid.reduce((a, b) => b.netReturn > a.netReturn ? b : a);
          return `Returns track market cycles. Worst year in window: ${worst.year} at ${window.pct(worst.netReturn)}; best year: ${best.year} at ${window.pct(best.netReturn)}. Bars are net of fees.`;
        })()}
        height={220}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={returnData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} interval={2} />
            <YAxis tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} width={42} />
            <Tooltip content={<window.CustomTooltip fmt={v => v.toFixed(1) + '%'} />} />
            <Bar dataKey="netReturn" name="Net Return" radius={[2, 2, 0, 0]}>
              {returnData.map((d, i) => (
                <Cell key={i} fill={d.netReturn >= 0 ? window.C.green : window.C.red} fillOpacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </window.ChartShell>

      {/* Download */}
      <div style={{ marginTop: 8, paddingTop: 16, borderTop: `1px solid ${window.C.border}`, display: 'flex', justifyContent: 'flex-end' }}>
        <window.DownloadCSV
          data={system.years.map(y => ({ system: system.name, state: system.stateName, year: y.year, omega: y.omega, fundedRatio: y.fundedRatio, netReturn: y.netReturn, assumedReturn: y.assumedReturn }))}
          filename={`${system.id}_timeseries.csv`}
          label={`EXPORT ${system.id} DATA`}
        />
      </div>
    </div>
  );
}

Object.assign(window, { SystemDeepDivePage });
