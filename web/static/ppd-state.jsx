// PPD Explorer — State & Regional Page

function StateRegionalPage() {
  const { STATES, YEARS } = window.PPDData;
  const fyFirst = YEARS[0];
  const fyLast  = YEARS[YEARS.length - 1];
  const lastIdx = YEARS.length - 1;
  // Default selected states: top 5 by total AUM in latest year
  const top5 = React.useMemo(
    () => [...STATES].sort((a, b) => b.totalAUM - a.totalAUM).slice(0, 5).map(s => s.code),
    [STATES]
  );
  const [mode, setMode] = React.useState('rank');
  const [selectedCodes, setSelectedCodes] = React.useState(top5);
  const {
    BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Legend, Cell
  } = Recharts;

  const PALETTE = [window.C.blue, window.C.sky, window.C.green, window.C.purple, window.C.red, '#FB923C', '#FBBF24', '#EC4899'];

  // Ranking data (all states, sorted by latest-year omega)
  const rankData = [...STATES]
    .sort((a, b) => b.latestOmega - a.latestOmega)
    .map(st => ({ state: st.code, name: st.name, omega: st.latestOmega, aum: st.totalAUM }));

  // Trend data (selected states over time) — uses bake's per-state-year averages
  const trendData = YEARS.map((year, i) => {
    const row = { year: String(year) };
    selectedCodes.forEach(code => {
      const st = STATES.find(s => s.code === code);
      if (st) row[code] = st.avgByYear[i].avgOmega;
    });
    return row;
  });

  // Derive top-AUM caption from real data, not hardcoded list
  const topByAumCaption = top5.join(', ');

  function toggleState(code) {
    setSelectedCodes(prev =>
      prev.includes(code)
        ? prev.length > 1 ? prev.filter(c => c !== code) : prev
        : prev.length < 8 ? [...prev, code] : prev
    );
  }

  const topOmegaState = rankData[0];
  const bottomOmegaState = rankData[rankData.length - 1];
  const spread = (topOmegaState.omega - bottomOmegaState.omega).toFixed(1);

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 8px' }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 6 }}>State & Regional</div>
        <h1 style={{ fontFamily: window.mono, color: window.C.textPrimary, fontSize: 22, fontWeight: 700, margin: 0 }}>Geographic Comparison</h1>
      </div>

      {/* Mode toggle */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 28, borderBottom: `1px solid ${window.C.border}` }}>
        {[['rank','Rank All States'],['compare','Compare States']].map(([m, label]) => (
          <button key={m} onClick={() => setMode(m)} style={{
            background: 'transparent',
            borderBottom: mode === m ? `2px solid ${window.C.blue}` : '2px solid transparent',
            border: 'none',
            borderBottom: mode === m ? `2px solid ${window.C.blue}` : '2px solid transparent',
            color: mode === m ? window.C.textPrimary : window.C.textMuted,
            fontFamily: window.mono, fontSize: 12, padding: '10px 22px',
            cursor: 'pointer', letterSpacing: '0.06em',
            transition: 'all 0.15s', marginBottom: -1,
          }}>{label}</button>
        ))}
      </div>

      {mode === 'rank' && (
        <>
          <window.SectionHeader>All States Ranked by Alternative Share ({fyLast})</window.SectionHeader>
          <window.InsightBox text={`${topOmegaState.name} leads with ${window.pct(topOmegaState.omega)} omega, while ${bottomOmegaState.name} trails at ${window.pct(bottomOmegaState.omega)} — a ${spread}pp spread across states in ${fyLast}.`} />
          <div style={{ width: '100%', height: Math.max(480, rankData.length * 22) }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rankData} layout="vertical" margin={{ top: 4, right: 60, bottom: 0, left: 40 }}>
                <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} />
                <YAxis type="category" dataKey="state" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} width={28} />
                <Tooltip content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null;
                  const st = STATES.find(s => s.code === label);
                  return (
                    <div style={{ background: '#0A1020', border: `1px solid ${window.C.border}`, padding: '10px 14px', fontFamily: window.mono, fontSize: 11 }}>
                      <div style={{ color: window.C.textPrimary, marginBottom: 4 }}>{st ? st.name : label}</div>
                      <div style={{ color: window.C.blue }}>Omega: {payload[0].value.toFixed(1)}%</div>
                      {st && <div style={{ color: window.C.textMuted, marginTop: 2 }}>AUM: ${st.totalAUM}B · {st.systemCount} systems</div>}
                    </div>
                  );
                }} />
                <Bar dataKey="omega" name={`Omega ${fyLast}`} radius={[0, 3, 3, 0]}>
                  {rankData.map((d, i) => {
                    const t = i / (rankData.length - 1);
                    const r = Math.round(59 + t * (239 - 59));
                    const g = Math.round(130 + t * (68 - 130));
                    const b = Math.round(246 + t * (68 - 246));
                    return <Cell key={i} fill={`rgb(${r},${g},${b})`} fillOpacity={0.85} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {mode === 'compare' && (
        <>
          {/* State selector */}
          <div style={{ marginBottom: 22 }}>
            <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>
              Select States (up to 8) — click to toggle
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {STATES.sort((a,b) => a.code.localeCompare(b.code)).map((st, i) => {
                const active = selectedCodes.includes(st.code);
                const colorIdx = selectedCodes.indexOf(st.code);
                return (
                  <button key={st.code} onClick={() => toggleState(st.code)} style={{
                    background: active ? `rgba(${active ? '59,130,246' : '30,50,84'},0.15)` : 'transparent',
                    border: `1px solid ${active ? (PALETTE[colorIdx] || window.C.blue) : window.C.border}`,
                    color: active ? (PALETTE[colorIdx] || window.C.blue) : window.C.textMuted,
                    fontFamily: window.mono, fontSize: 11, padding: '5px 10px',
                    cursor: 'pointer', transition: 'all 0.15s',
                    boxShadow: active ? `0 0 8px ${PALETTE[colorIdx] || window.C.blue}44` : 'none',
                  }}>{st.code}</button>
                );
              })}
            </div>
            <div style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 11, marginTop: 8 }}>
              Default: top 5 by AUM ({topByAumCaption}). Select any combination to compare.
            </div>
          </div>

          {/* KPI row for selected states */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 28, flexWrap: 'wrap' }}>
            {selectedCodes.map((code, i) => {
              const st = STATES.find(s => s.code === code);
              if (!st) return null;
              return (
                <div key={code} style={{
                  background: window.C.card, borderLeft: `3px solid ${PALETTE[i]}`,
                  padding: '12px 16px', flex: '1 0 140px', minWidth: 0,
                }}>
                  <div style={{ fontFamily: window.mono, color: PALETTE[i], fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>{st.name}</div>
                  <div style={{ fontFamily: window.mono, color: window.C.textPrimary, fontSize: 20, fontWeight: 600 }}>{window.pct(st.latestOmega)}</div>
                  <div style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 11, marginTop: 3 }}>${st.totalAUM}B · {st.systemCount} systems</div>
                </div>
              );
            })}
          </div>

          <window.SectionHeader>Alternative Share Over Time — Selected States</window.SectionHeader>
          <window.ChartShell
            title={`Average Omega by State (FY ${fyFirst}–${fyLast})`}
            insight={`Among the selected states, ${(() => { const sorted = selectedCodes.map(c => ({ code: c, v: STATES.find(s=>s.code===c)?.latestOmega || 0 })).sort((a,b)=>b.v-a.v); return sorted[0] ? STATES.find(s=>s.code===sorted[0].code)?.name : '' })()} leads with the highest alternative share in ${fyLast}.`}
            height={280}
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="year" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} interval={4} />
                <YAxis tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} width={38} />
                <Tooltip content={<window.CustomTooltip fmt={v => v != null ? v.toFixed(1) + '%' : '—'} />} />
                <Legend wrapperStyle={{ fontFamily: window.mono, fontSize: 10, color: window.C.textMuted }}
                  formatter={(value) => { const st = STATES.find(s => s.code === value); return st ? st.name : value; }} />
                {selectedCodes.map((code, i) => (
                  <Line key={code} type="monotone" dataKey={code} name={code}
                    stroke={PALETTE[i % PALETTE.length]} strokeWidth={2}
                    dot={false} activeDot={{ r: 4 }} connectNulls />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </window.ChartShell>
        </>
      )}

      {/* Scatter: omega vs funded ratio */}
      {mode === 'compare' && (
        <>
          <window.SectionHeader>Omega vs Funded Ratio ({fyLast})</window.SectionHeader>
          <window.ChartShell
            title={`Alternative Share vs Funding Health — All States, FY ${fyLast}`}
            insight={`Each marker is a state in ${fyLast}, sized by total AUM. Selected states (sidebar) are highlighted.`}
            height={300}
          >
            <ResponsiveContainer width="100%" height="100%">
              <Recharts.ScatterChart margin={{ top: 10, right: 30, bottom: 10, left: 0 }}>
                <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" />
                <XAxis type="number" dataKey="omega" name="Omega" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} label={{ value: `Omega ${fyLast} (%)`, fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono, position: 'insideBottom', offset: -2 }} />
                <YAxis type="number" dataKey="funded" name="Funded Ratio" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v + '%'} width={42} label={{ value: 'Funded Ratio (%)', fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono, angle: -90, position: 'insideLeft' }} />
                <Tooltip content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  const d = payload[0].payload;
                  return (
                    <div style={{ background: '#0A1020', border: `1px solid ${window.C.border}`, padding: '10px 14px', fontFamily: window.mono, fontSize: 11 }}>
                      <div style={{ color: window.C.textPrimary, marginBottom: 4 }}>{d.name}</div>
                      <div style={{ color: window.C.blue }}>Omega: {d.omega.toFixed(1)}%</div>
                      <div style={{ color: window.C.sky }}>Funded: {d.funded.toFixed(1)}%</div>
                      <div style={{ color: window.C.textMuted, fontSize: 10, marginTop: 2 }}>${d.aum}B · {d.count} systems</div>
                    </div>
                  );
                }} />
                <Recharts.Scatter
                  data={STATES.map(st => ({
                    omega: st.latestOmega,
                    funded: st.avgByYear[lastIdx].avgFunded,
                    name: st.name,
                    code: st.code,
                    aum: st.totalAUM,
                    count: st.systemCount,
                  }))}
                  fill={window.C.blue}
                  fillOpacity={0.7}
                  shape={({ cx, cy, payload }) => {
                    const isSelected = selectedCodes.includes(payload.code);
                    return (
                      <g>
                        <circle cx={cx} cy={cy} r={isSelected ? 8 : 5}
                          fill={isSelected ? window.C.blue : window.C.sky}
                          fillOpacity={isSelected ? 0.9 : 0.4}
                          stroke={isSelected ? window.C.blue : 'none'}
                          strokeWidth={isSelected ? 1.5 : 0} />
                        {isSelected && (
                          <text x={cx + 9} y={cy + 4} fill={window.C.textMuted} fontSize={9} fontFamily={window.mono}>{payload.code}</text>
                        )}
                      </g>
                    );
                  }}
                />
              </Recharts.ScatterChart>
            </ResponsiveContainer>
          </window.ChartShell>
        </>
      )}

      {/* Download */}
      <div style={{ marginTop: 16, paddingTop: 16, borderTop: `1px solid ${window.C.border}`, display: 'flex', justifyContent: 'flex-end' }}>
        <window.DownloadCSV
          data={rankData.map(d => ({ state: d.state, name: d.name, [`omega${fyLast}`]: d.omega, totalAumB: d.aum }))}
          filename={`state_rankings_${fyLast}.csv`}
          label="EXPORT STATE RANKINGS"
        />
      </div>
    </div>
  );
}

Object.assign(window, { StateRegionalPage });
