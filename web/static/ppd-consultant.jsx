// PPD Explorer — Consultant Analysis Page

function ConsultantPage() {
  const { CONSULTANTS, SYSTEMS, AGG_OMEGA, YEARS } = window.PPDData;
  const [selectedId, setSelectedId] = React.useState(CONSULTANTS[0].id);
  const [metric, setMetric] = React.useState('omega');
  const {
    BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
    ResponsiveContainer, CartesianGrid, Legend, Cell
  } = Recharts;

  const consultant = CONSULTANTS.find(c => c.id === selectedId) || CONSULTANTS[0];

  const METRIC_LABELS = {
    omega: 'Alt. Share (Omega)',
    fundedRatio: 'Funded Ratio',
    netReturn: 'Net Return',
    assumedReturn: 'Assumed Return',
  };

  // Metric comparison: consultant clients vs all-system average by year
  const metricData = YEARS.map((year, i) => {
    const clientVals = consultant.clients.map(s => s.years[i][metric]).filter(v => v != null);
    const allVals = SYSTEMS.map(s => s.years[i][metric]).filter(v => v != null);
    const clientAvg = clientVals.length ? clientVals.reduce((a, b) => a + b, 0) / clientVals.length : null;
    const allAvg = allVals.length ? allVals.reduce((a, b) => a + b, 0) / allVals.length : null;
    return { year: String(year), clients: clientAvg != null ? Math.round(clientAvg * 10) / 10 : null, allSystems: allAvg != null ? Math.round(allAvg * 10) / 10 : null };
  });

  // Client table
  const clientTableData = consultant.clients.map(s => {
    const latest = s.years[s.years.length - 1];
    const earliest = s.years[0];
    return {
      'System': s.name,
      'State': s.stateName,
      'AUM ($B)': s.aumB,
      'Omega 2021': window.pct(latest.omega),
      'Omega 2001': window.pct(earliest.omega),
      'Funded Ratio': window.pct(latest.fundedRatio),
      'Net Return (2021)': window.pct(latest.netReturn),
    };
  }).sort((a, b) => b['AUM ($B)'] - a['AUM ($B)']);

  // Omega distribution among clients vs all systems (2021)
  const omegaBuckets = ['< 15%','15–20%','20–25%','25–30%','30–35%','35–40%','40–45%','≥ 45%'];
  const getBucket = v => {
    if (v < 15) return 0; if (v < 20) return 1; if (v < 25) return 2; if (v < 30) return 3;
    if (v < 35) return 4; if (v < 40) return 5; if (v < 45) return 6; return 7;
  };
  const clientCounts = new Array(8).fill(0);
  const allCounts = new Array(8).fill(0);
  consultant.clients.forEach(s => { clientCounts[getBucket(s.years[20].omega)]++; });
  SYSTEMS.forEach(s => { allCounts[getBucket(s.years[20].omega)]++; });
  const distData = omegaBuckets.map((label, i) => ({
    bucket: label,
    clients: clientCounts[i],
    allSystems: parseFloat(((allCounts[i] / SYSTEMS.length) * (consultant.clients.length || 1)).toFixed(1)),
  }));

  const consultantAvgOmega = Math.round(consultant.clients.reduce((a, s) => a + s.years[20].omega, 0) / Math.max(1, consultant.clients.length) * 10) / 10;
  const allAvgOmega = AGG_OMEGA[20];
  const diffStr = (consultantAvgOmega - allAvgOmega).toFixed(1);

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 8px' }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 6 }}>Consultant Analysis</div>
        <h1 style={{ fontFamily: window.mono, color: window.C.textPrimary, fontSize: 22, fontWeight: 700, margin: 0 }}>Investment Consultant Explorer</h1>
      </div>

      {/* Consultant selector */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Select Consultant</div>
        <select
          value={selectedId}
          onChange={e => setSelectedId(e.target.value)}
          style={{
            background: window.C.card, border: `1px solid ${window.C.blue}`,
            color: window.C.textPrimary, fontFamily: window.mono, fontSize: 13,
            padding: '11px 16px', width: '100%', outline: 'none', cursor: 'pointer',
            boxShadow: window.C.glowBlue, appearance: 'none',
          }}
        >
          {CONSULTANTS.map(c => (
            <option key={c.id} value={c.id} style={{ background: window.C.card }}>
              {c.name} — ${c.totalAUM}B AUM · {c.clientCount} {c.clientCount === 1 ? 'client' : 'clients'}
            </option>
          ))}
        </select>
      </div>

      {/* KPIs */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 32 }}>
        <window.KPITile label="Total Client AUM" value={`$${consultant.totalAUM}B`} sub="Sum of assets under advisement, FY 2021" accent={window.C.blue} />
        <window.KPITile label="Client Systems" value={String(consultant.clientCount)} sub="Pension funds in the PPD sample (2021)" accent={window.C.sky} />
        <window.KPITile label="Avg Client Omega" value={window.pct(consultantAvgOmega)} sub={`${parseFloat(diffStr) >= 0 ? '+' : ''}${diffStr}pp vs ${window.pct(allAvgOmega)} all-system avg`} accent={parseFloat(diffStr) >= 0 ? window.C.green : window.C.red} />
      </div>

      {/* Metric comparison chart */}
      <window.SectionHeader>Metric Comparison</window.SectionHeader>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.08em' }}>Metric:</span>
        {Object.entries(METRIC_LABELS).map(([k, label]) => (
          <button key={k} onClick={() => setMetric(k)} style={{
            background: metric === k ? 'rgba(59,130,246,0.18)' : 'transparent',
            border: `1px solid ${metric === k ? window.C.blue : window.C.border}`,
            color: metric === k ? window.C.blue : window.C.textMuted,
            fontFamily: window.mono, fontSize: 11, padding: '5px 12px', cursor: 'pointer',
            transition: 'all 0.15s',
          }}>{label}</button>
        ))}
      </div>
      <window.ChartShell
        title={`${METRIC_LABELS[metric]} — ${consultant.name} Clients vs All Systems`}
        insight={`${consultant.name} clients averaged ${window.pct(metricData[20].clients)} in ${METRIC_LABELS[metric].toLowerCase()} in 2021, compared to the all-system average of ${window.pct(metricData[20].allSystems)}.`}
        height={240}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={metricData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} interval={4} />
            <YAxis tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} tickFormatter={v => v != null ? v.toFixed(1) + '%' : ''} width={42} />
            <Tooltip content={<window.CustomTooltip fmt={v => v != null ? v.toFixed(1) + '%' : '—'} />} />
            <Legend wrapperStyle={{ fontFamily: window.mono, fontSize: 10, color: window.C.textMuted }} />
            <Line type="monotone" dataKey="clients" name={consultant.name} stroke={window.C.blue} strokeWidth={2.5} dot={false} connectNulls />
            <Line type="monotone" dataKey="allSystems" name="All Systems" stroke={window.C.sky} strokeWidth={1.5} strokeDasharray="5 4" dot={false} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </window.ChartShell>

      {/* Distribution chart */}
      <window.SectionHeader>Omega Distribution (2021)</window.SectionHeader>
      <window.ChartShell
        title="Client Fund Count by Alternative Share Bucket"
        insight={`${consultant.name} client funds cluster in the ${consultant.clients.length ? omegaBuckets[getBucket(consultantAvgOmega)] : '—'} omega range. Distribution shown as count of client systems vs proportional all-system benchmark.`}
        height={220}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={distData} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="bucket" tick={{ fill: window.C.textMuted, fontSize: 9, fontFamily: window.mono }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} width={30} />
            <Tooltip content={<window.CustomTooltip fmt={v => v} />} />
            <Legend wrapperStyle={{ fontFamily: window.mono, fontSize: 10, color: window.C.textMuted }} />
            <Bar dataKey="clients" name="Client Count" fill={window.C.blue} fillOpacity={0.85} radius={[2, 2, 0, 0]} />
            <Bar dataKey="allSystems" name="Expected (All-System)" fill={window.C.sky} fillOpacity={0.4} radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </window.ChartShell>

      {/* Client table */}
      <window.SectionHeader>Client Systems — {consultant.name}</window.SectionHeader>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 10 }}>
        <window.DownloadCSV data={clientTableData} filename={`${consultant.id}_clients.csv`} label={`EXPORT CLIENT LIST`} />
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: window.mono, fontSize: 12 }}>
          <thead>
            <tr>
              {Object.keys(clientTableData[0] || {}).map(h => (
                <th key={h} style={{ padding: '10px 14px', textAlign: h === 'System' ? 'left' : 'right', color: window.C.textMuted, fontWeight: 500, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.08em', borderBottom: `1px solid ${window.C.border}`, whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {clientTableData.map((row, i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? window.C.surface : window.C.card }}>
                {Object.entries(row).map(([k, v]) => (
                  <td key={k} style={{ padding: '10px 14px', textAlign: k === 'System' ? 'left' : 'right', color: k === 'System' ? window.C.textPrimary : window.C.textMuted, borderBottom: `1px solid ${window.C.border}`, whiteSpace: k === 'System' ? 'normal' : 'nowrap' }}>{v}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

Object.assign(window, { ConsultantPage });
