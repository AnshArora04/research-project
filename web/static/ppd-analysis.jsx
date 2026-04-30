// PPD Explorer — Analysis Page (Steps 4 + 6)
// Four test types: Univariate, OLS, Event Study, Correlation.
// All non-component identifiers are namespaced under `_PA_` to avoid global
// collisions with sibling jsx scripts evaluated in the same realm.
// Component names start capital so JSX treats them as components, not tags.

const _PA_TEST_TYPES = [
  { id: 'univariate',        label: 'Univariate',        sub: 'Y over time, optionally split' },
  { id: 'ols',               label: 'OLS',               sub: 'Regression with controls + FE' },
  { id: 'group_comparison',  label: 'Group Comparison',  sub: 'Two-group AUM-weighted time series + difference' },
  { id: 'correlation',       label: 'Correlation',       sub: 'Pairwise matrix + scatter' },
];

const _PA_WEIGHTS_OPTIONS = [
  { value: 'equal', label: 'Equal-weighted', sub: 'every system-year counts the same' },
  { value: 'aum',   label: 'AUM-weighted',   sub: 'paper-style WLS by MktAssets_net' },
];

const _PA_CLUSTER_OPTIONS = [
  { value: 'entity',  label: 'Entity cluster',     sub: 'pub_id only' },
  { value: 'twoway',  label: 'Two-way cluster',    sub: 'pub_id × fy (Cameron-Gelbach-Miller)' },
];

const _PA_GROUP_OPTIONS = [
  { value: '',              label: '— No grouping (overall) —' },
  { value: 'aum_tercile',   label: 'AUM tercile (within year)' },
  { value: 'StateAbbrev',   label: 'State' },
  { value: 'consultant_id', label: 'Investment consultant' },
];

const _PA_FE_OPTIONS = [
  { value: 'pub_id',        label: 'System (entity) FE' },
  { value: 'fy',            label: 'Year (time) FE' },
  { value: 'StateAbbrev',   label: 'State FE' },
  { value: 'consultant_id', label: 'Consultant FE' },
];

const _PA_EVENT_DIMS = [
  { value: 'StateAbbrev',   label: 'State' },
  { value: 'consultant_id', label: 'Consultant' },
];

function _PA_isPctVar(meta) {
  return !!meta && typeof meta.units === 'string' && meta.units.startsWith('ratio');
}

function _PA_fmtFor(meta) {
  if (_PA_isPctVar(meta)) return v => v == null ? '—' : (v * 100).toFixed(1) + '%';
  return v => v == null ? '—' : (Math.abs(v) >= 1000 ? v.toLocaleString() : v.toFixed(2));
}

function _PA_yLabel(vars, key) {
  const m = (vars || []).find(v => v.key === key);
  return m ? m.label : key;
}

// Heatmap cell color from correlation in [-1, 1].
function _PA_heatColor(rho) {
  if (rho == null || isNaN(rho)) return 'transparent';
  const a = Math.min(Math.abs(rho), 1) * 0.6;
  return rho >= 0
    ? `rgba(59,130,246,${a.toFixed(3)})`   // blue for positive
    : `rgba(248,113,113,${a.toFixed(3)})`; // red for negative
}

// ── Shared layout primitives ────────────────────────────────────────────────

const _PA_selectStyle = {
  width: '100%',
  background: '#0A1020',
  border: `1px solid ${window.C.border}`,
  color: window.C.textPrimary,
  fontFamily: window.mono,
  fontSize: 12,
  padding: '8px 10px',
  cursor: 'pointer',
};

const _PA_multiSelectStyle = {
  ..._PA_selectStyle,
  height: 110,
  cursor: 'default',
};

const _PA_cardStyle = {
  background: window.C.card,
  border: `1px solid ${window.C.border}`,
  padding: '18px 22px',
  marginBottom: 24,
};

function PASpecField({ label, hint, children }) {
  return (
    <div>
      <div style={{
        fontFamily: window.mono, color: window.C.textMuted, fontSize: 10,
        textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6,
      }}>{label}</div>
      {children}
      {hint && (
        <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, marginTop: 4, opacity: 0.8 }}>
          {hint}
        </div>
      )}
    </div>
  );
}

// Multi-select helper — renders a native <select multiple> with grouped options.
// Used by the picker forms (Group Comparison values, Correlation vars) where
// list size can be 50+ items.
function PAMultiSelect({ value, onChange, options, height = 110 }) {
  function handle(e) {
    const picks = Array.from(e.target.selectedOptions).map(o => o.value);
    onChange(picks);
  }
  return (
    <select multiple value={value} onChange={handle} style={{ ..._PA_multiSelectStyle, height }}>
      {options.map(o => (
        o.optgroup ? (
          <optgroup key={o.optgroup} label={o.optgroup}>
            {o.items.map(it => <option key={it.value} value={it.value}>{it.label}</option>)}
          </optgroup>
        ) : (
          <option key={o.value} value={o.value}>{o.label}</option>
        )
      ))}
    </select>
  );
}

// Checkbox-list multi-select — friendlier than native <select multiple> for the
// known-small variable picker (3 groups × ~5 items). Click anywhere on a row to
// toggle; selected rows highlight blue. Used by OLS X and Controls fields.
function PACheckboxList({ value, onChange, options, height = 220 }) {
  const selected = new Set(value || []);
  function toggle(v) {
    const next = new Set(selected);
    next.has(v) ? next.delete(v) : next.add(v);
    onChange([...next]);
  }
  const allItems = options.flatMap(o => o.optgroup ? o.items : [o]);
  const allSelected = allItems.length > 0 && allItems.every(it => selected.has(it.value));
  function selectAll() { onChange(allItems.map(it => it.value)); }
  function clearAll() { onChange([]); }

  function Row({ it }) {
    const on = selected.has(it.value);
    return (
      <label
        onMouseEnter={e => { if (!on) e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; }}
        onMouseLeave={e => { if (!on) e.currentTarget.style.background = 'transparent'; }}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          padding: '6px 10px', cursor: 'pointer',
          background: on ? 'rgba(59,130,246,0.12)' : 'transparent',
          color: on ? window.C.textPrimary : window.C.textMuted,
          borderLeft: on ? `2px solid ${window.C.blue}` : '2px solid transparent',
          fontSize: 12, lineHeight: 1.3,
        }}>
        <input type="checkbox" checked={on} onChange={() => toggle(it.value)}
               style={{ accentColor: window.C.blue, margin: 0 }} />
        <span>{it.label}</span>
      </label>
    );
  }

  return (
    <div>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        fontFamily: window.mono, fontSize: 10, color: window.C.textMuted,
        marginBottom: 4, paddingRight: 2,
      }}>
        <span>{selected.size} selected</span>
        <span>
          <button onClick={allSelected ? clearAll : selectAll}
                  style={{
                    background: 'transparent', border: 'none', color: window.C.blue,
                    fontFamily: window.mono, fontSize: 10, cursor: 'pointer',
                    padding: '0 4px', textTransform: 'uppercase', letterSpacing: '0.06em',
                  }}>
            {allSelected ? 'Clear' : 'All'}
          </button>
        </span>
      </div>
      <div style={{
        height, overflowY: 'auto',
        background: '#0A1020',
        border: `1px solid ${window.C.border}`,
        fontFamily: window.mono,
      }}>
        {options.map(o => o.optgroup ? (
          <div key={o.optgroup}>
            <div style={{
              color: window.C.textMuted, fontSize: 9, fontWeight: 600,
              textTransform: 'uppercase', letterSpacing: '0.12em',
              padding: '6px 10px 4px',
              background: '#0D1526',
              borderBottom: `1px solid ${window.C.border}`,
            }}>{o.optgroup}</div>
            {o.items.map(it => <Row key={it.value} it={it} />)}
          </div>
        ) : (
          <Row key={o.value} it={o} />
        ))}
      </div>
    </div>
  );
}

// Stat pill row (sample-stats footer).
function PAStatPills({ items }) {
  return (
    <div style={{
      display: 'flex', gap: 10, marginTop: 8, flexWrap: 'wrap',
      fontFamily: window.mono, fontSize: 11, color: window.C.textMuted,
    }}>
      {items.filter(Boolean).map((s, i) => (
        <React.Fragment key={i}>
          {i > 0 && <span>·</span>}
          <span>{s}</span>
        </React.Fragment>
      ))}
    </div>
  );
}

// Build the {outcome,allocation,control} grouped option list for Y/X selects.
function _PA_yxOptions(vars) {
  return ['outcome', 'allocation', 'control'].map(g => ({
    optgroup: g.toUpperCase(),
    items: (vars || []).filter(v => v.group === g).map(v => ({ value: v.key, label: v.label })),
  }));
}

// ── UNIVARIATE ───────────────────────────────────────────────────────────────

function PAUnivariateForm({ spec, setSpec, vars }) {
  const opts = _PA_yxOptions(vars);
  return (
    <div style={{ ..._PA_cardStyle, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'end' }}>
      <PASpecField label="Y variable">
        <select value={spec.y} onChange={e => setSpec({ ...spec, y: e.target.value })} style={_PA_selectStyle}>
          {opts.map(g => (
            <optgroup key={g.optgroup} label={g.optgroup}>
              {g.items.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </optgroup>
          ))}
        </select>
      </PASpecField>
      <PASpecField label="Group by (optional)">
        <select value={spec.group_by || ''} onChange={e => setSpec({ ...spec, group_by: e.target.value })} style={_PA_selectStyle}>
          {_PA_GROUP_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </PASpecField>
    </div>
  );
}

function PAUnivariateResult({ result, vars, spec }) {
  const { LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer } = Recharts;
  const yMeta = (vars || []).find(v => v.key === spec.y);
  const isPct = _PA_isPctVar(yMeta);
  const fmt = _PA_fmtFor(yMeta);
  const seriesCount = result.series.length;
  const tooManySeries = seriesCount > 8;
  const hasPlottable = result.sample.n > 0 && result.series.some(s => s.points.some(p => p.value != null));

  const chartData = React.useMemo(() => {
    const years = [...new Set(result.series.flatMap(s => s.points.map(p => p.year)))].sort((a, b) => a - b);
    return years.map(year => {
      const row = { year };
      result.series.forEach(s => {
        const pt = s.points.find(p => p.year === year);
        row[s.group] = pt && pt.value != null ? pt.value : null;
      });
      return row;
    });
  }, [result]);

  if (!hasPlottable) return <PANoData />;
  return (
    <>
      {tooManySeries && (
        <window.InsightBox text={`${seriesCount} series rendered — chart may be cluttered. Consider filtering by a smaller dimension or use the CSV export.`} />
      )}
      <window.ChartShell title={`${yMeta ? yMeta.label : spec.y} — by fiscal year${spec.group_by ? ' × ' + spec.group_by : ''}`} height={320}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} interval={2} />
            <YAxis tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false}
                   tickFormatter={v => isPct ? (v * 100).toFixed(0) + '%' : (Math.abs(v) >= 1000 ? (v / 1000).toFixed(0) + 'K' : v.toFixed(1))}
                   width={48} />
            <Tooltip content={<window.CustomTooltip fmt={fmt} />} />
            {!tooManySeries && <Legend wrapperStyle={{ fontFamily: window.mono, fontSize: 10, color: window.C.textMuted }} />}
            {result.series.map((s, i) => (
              <Line key={s.group} type="monotone" dataKey={s.group} name={s.group}
                    stroke={window.C.chartColors[i % window.C.chartColors.length]}
                    strokeWidth={result.series.length === 1 ? 2.5 : 1.6}
                    dot={false} activeDot={{ r: 3 }} connectNulls />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </window.ChartShell>
      <PAStatPills items={[
        `N = ${result.sample.n.toLocaleString()} obs`,
        `${result.sample.n_systems} systems`,
        `FY ${result.sample.fy_min}–${result.sample.fy_max}`,
        `${seriesCount} series`,
      ]} />
    </>
  );
}

// ── OLS ──────────────────────────────────────────────────────────────────────

function PAPillRadio({ value, options, onChange }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, paddingTop: 4 }}>
      {options.map(o => {
        const on = value === o.value;
        return (
          <label key={o.value} title={o.sub} style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '6px 10px', cursor: 'pointer',
            border: `1px solid ${on ? window.C.blue : window.C.border}`,
            background: on ? 'rgba(59,130,246,0.1)' : 'transparent',
            fontFamily: window.mono, fontSize: 11, color: on ? window.C.textPrimary : window.C.textMuted,
          }}>
            <input type="radio" checked={on} onChange={() => onChange(o.value)} style={{ accentColor: window.C.blue }} />
            {o.label}
          </label>
        );
      })}
    </div>
  );
}

function PAOlsForm({ spec, setSpec, vars }) {
  const opts = _PA_yxOptions(vars);
  function setXs(xs) { setSpec({ ...spec, xs }); }
  function setControls(controls) { setSpec({ ...spec, controls }); }
  function toggleFE(v) {
    const cur = new Set(spec.fe || []);
    cur.has(v) ? cur.delete(v) : cur.add(v);
    setSpec({ ...spec, fe: [...cur] });
  }
  return (
    <div style={{ ..._PA_cardStyle, display: 'grid', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <PASpecField label="Y variable">
          <select value={spec.y} onChange={e => setSpec({ ...spec, y: e.target.value })} style={_PA_selectStyle}>
            {opts.map(g => (
              <optgroup key={g.optgroup} label={g.optgroup}>
                {g.items.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </optgroup>
            ))}
          </select>
        </PASpecField>
        <PASpecField label="Fixed effects">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, paddingTop: 4 }}>
            {_PA_FE_OPTIONS.map(o => {
              const on = (spec.fe || []).includes(o.value);
              return (
                <label key={o.value} style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                  padding: '6px 10px', cursor: 'pointer',
                  border: `1px solid ${on ? window.C.blue : window.C.border}`,
                  background: on ? 'rgba(59,130,246,0.1)' : 'transparent',
                  fontFamily: window.mono, fontSize: 11, color: on ? window.C.textPrimary : window.C.textMuted,
                }}>
                  <input type="checkbox" checked={on} onChange={() => toggleFE(o.value)} style={{ accentColor: window.C.blue }} />
                  {o.label}
                </label>
              );
            })}
          </div>
        </PASpecField>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <PASpecField label="X variables (regressors of interest)" hint="Click any row to toggle">
          <PACheckboxList value={spec.xs || []} onChange={setXs} options={opts} height={220} />
        </PASpecField>
        <PASpecField label="Controls (optional)" hint="Estimated but de-emphasized in summary">
          <PACheckboxList value={spec.controls || []} onChange={setControls} options={opts} height={220} />
        </PASpecField>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <PASpecField label="Weighting" hint="AUM-weighted matches the paper's Table-1-style WLS">
          <PAPillRadio value={spec.weights || 'equal'} options={_PA_WEIGHTS_OPTIONS}
                       onChange={v => setSpec({ ...spec, weights: v })} />
        </PASpecField>
        <PASpecField label="SE clustering" hint="Two-way absorbs both within-fund and within-year correlation">
          <PAPillRadio value={spec.cluster || 'entity'} options={_PA_CLUSTER_OPTIONS}
                       onChange={v => setSpec({ ...spec, cluster: v })} />
        </PASpecField>
      </div>
    </div>
  );
}

function PAOlsResult({ result, vars, spec }) {
  const { BarChart, Bar, ErrorBar, ScatterChart, Scatter, XAxis, YAxis, Tooltip, CartesianGrid,
          Legend, ResponsiveContainer, ReferenceLine, Cell } = Recharts;

  // Coefficient bar-chart data
  const coefData = result.coefficients.map(c => ({
    name: c.name, beta: c.beta,
    err: [Math.max(c.beta - c.ci_lo, 0), Math.max(c.ci_hi - c.beta, 0)],
    p: c.p,
  }));
  const yMeta = (vars || []).find(v => v.key === spec.y);
  const yIsPct = _PA_isPctVar(yMeta);

  return (
    <>
      {/* Coefficients table */}
      <window.SectionHeader>Coefficients (clustered SE by pub_id)</window.SectionHeader>
      <div style={{ overflowX: 'auto', marginBottom: 24 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: window.mono, fontSize: 11 }}>
          <thead>
            <tr style={{ color: window.C.textMuted, textTransform: 'uppercase', fontSize: 10, letterSpacing: '0.08em', textAlign: 'right' }}>
              <th style={{ textAlign: 'left',  padding: '8px 10px', borderBottom: `1px solid ${window.C.border}` }}>Name</th>
              <th style={{ padding: '8px 10px', borderBottom: `1px solid ${window.C.border}` }}>β</th>
              <th style={{ padding: '8px 10px', borderBottom: `1px solid ${window.C.border}` }}>SE</th>
              <th style={{ padding: '8px 10px', borderBottom: `1px solid ${window.C.border}` }}>t</th>
              <th style={{ padding: '8px 10px', borderBottom: `1px solid ${window.C.border}` }}>p</th>
              <th style={{ padding: '8px 10px', borderBottom: `1px solid ${window.C.border}` }}>95% CI</th>
            </tr>
          </thead>
          <tbody>
            {result.coefficients.map(c => {
              const sig = c.p < 0.01 ? '***' : c.p < 0.05 ? '**' : c.p < 0.1 ? '*' : '';
              const sigColor = c.p < 0.05 ? window.C.green : window.C.textMuted;
              return (
                <tr key={c.name} style={{ color: window.C.textPrimary }}>
                  <td style={{ padding: '8px 10px', borderBottom: `1px solid ${window.C.border}` }}>{c.name}</td>
                  <td style={{ padding: '8px 10px', textAlign: 'right', borderBottom: `1px solid ${window.C.border}` }}>{c.beta.toFixed(4)}</td>
                  <td style={{ padding: '8px 10px', textAlign: 'right', borderBottom: `1px solid ${window.C.border}`, color: window.C.textMuted }}>{c.se.toFixed(4)}</td>
                  <td style={{ padding: '8px 10px', textAlign: 'right', borderBottom: `1px solid ${window.C.border}` }}>{c.t.toFixed(2)}</td>
                  <td style={{ padding: '8px 10px', textAlign: 'right', borderBottom: `1px solid ${window.C.border}`, color: sigColor }}>
                    {c.p < 0.001 ? '<0.001' : c.p.toFixed(3)} {sig && <span style={{ marginLeft: 4 }}>{sig}</span>}
                  </td>
                  <td style={{ padding: '8px 10px', textAlign: 'right', borderBottom: `1px solid ${window.C.border}`, color: window.C.textMuted }}>
                    [{c.ci_lo.toFixed(4)}, {c.ci_hi.toFixed(4)}]
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Coefficient bar chart with 95% CI whiskers */}
      <window.ChartShell title="Coefficient estimates (β with 95% CI)" height={Math.max(180, 60 + 36 * coefData.length)}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={coefData} layout="vertical" margin={{ top: 8, right: 24, bottom: 8, left: 80 }}>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="name" tick={{ fill: window.C.textMuted, fontSize: 11, fontFamily: window.mono }} axisLine={false} tickLine={false} width={140} />
            <ReferenceLine x={0} stroke={window.C.textMuted} />
            <Tooltip content={<window.CustomTooltip fmt={v => typeof v === 'number' ? v.toFixed(4) : v} />} />
            <Bar dataKey="beta" fill={window.C.blue} barSize={18}>
              {coefData.map((c, i) => (
                <Cell key={i} fill={c.p < 0.05 ? window.C.blue : window.C.border} />
              ))}
              <ErrorBar dataKey="err" width={6} strokeWidth={1.5} stroke={window.C.textMuted} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </window.ChartShell>

      {/* Scatter for first X vs Y. With controls/FE this is a partial-regression
          plot whose slope = the multivariate β shown in the table (FWL identity). */}
      {result.scatter && (
        <window.ChartShell
          title={
            (result.scatter.is_partial ? 'Partial-regression: ' : '') +
            `${result.scatter.x_label} vs ${_PA_yLabel(vars, result.scatter.y_label)}` +
            (result.scatter.is_partial ? ' (residualized)' : '')
          }
          insight={result.scatter.fit_note}
          height={300}
        >
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" />
              <XAxis type="number" dataKey="x" name={result.scatter.x_label}
                     tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }}
                     axisLine={false} tickLine={false} />
              <YAxis type="number" dataKey="y" name={result.scatter.y_label}
                     tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }}
                     axisLine={false} tickLine={false}
                     tickFormatter={v => yIsPct ? (v * 100).toFixed(0) + '%' : v.toFixed(2)} width={48} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }}
                       content={<window.CustomTooltip fmt={v => typeof v === 'number' ? (yIsPct && Math.abs(v) <= 1 ? (v*100).toFixed(1)+'%' : v.toFixed(3)) : v} />} />
              <Scatter name="points" data={result.scatter.points} fill={window.C.blue} fillOpacity={0.35} />
              <Scatter name="fit" data={result.scatter.fit_line} line={{ stroke: window.C.red, strokeWidth: 2 }}
                       lineType="joint" shape={() => null} legendType="none" />
            </ScatterChart>
          </ResponsiveContainer>
        </window.ChartShell>
      )}

      <PAStatPills items={[
        `N = ${result.sample.n.toLocaleString()} obs`,
        `${result.sample.n_systems} systems`,
        `FY ${result.sample.fy_min}–${result.sample.fy_max}`,
        `R² = ${result.sample.r2.toFixed(3)}`,
        result.sample.r2_within != null ? `R²ᵥ = ${result.sample.r2_within.toFixed(3)}` : null,
      ]} />
    </>
  );
}

// ── GROUP COMPARISON (two-group AUM-weighted time series + difference) ──────

function PAGroupBuilder({ label, group, setGroup }) {
  const stateOptions = (window.PPDData?.STATES || [])
    .map(s => ({ value: s.code, label: `${s.code} — ${s.name}` }))
    .sort((a, b) => a.value.localeCompare(b.value));
  const consultantOptions = (window.PPDData?.CONSULTANTS || [])
    .map(c => ({ value: String(c.id), label: `${c.name} (${c.clientCount} clients)` }));
  const opts = group.by === 'StateAbbrev' ? stateOptions : consultantOptions;

  function setBy(by) {
    // Reset values when dimension changes (state codes ≠ consultant ids).
    setGroup({ by, values: [] });
  }
  function setValues(values) { setGroup({ ...group, values }); }

  return (
    <div style={{ display: 'grid', gap: 10 }}>
      <PASpecField label={`${label} — dimension`}>
        <select value={group.by} onChange={e => setBy(e.target.value)} style={_PA_selectStyle}>
          {_PA_EVENT_DIMS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </PASpecField>
      <PASpecField label={`${label} — values (≥1)`} hint="Cmd/Ctrl-click to select multiple">
        <PAMultiSelect value={group.values || []} onChange={setValues} options={opts} height={150} />
      </PASpecField>
    </div>
  );
}

function PAGroupComparisonForm({ spec, setSpec, vars }) {
  const opts = _PA_yxOptions(vars);
  return (
    <div style={{ ..._PA_cardStyle, display: 'grid', gap: 16 }}>
      <PASpecField label="Y variable" hint="Descriptive comparison only — not a formal event study (no event date, no DiD).">
        <select value={spec.y} onChange={e => setSpec({ ...spec, y: e.target.value })} style={_PA_selectStyle}>
          {opts.map(g => (
            <optgroup key={g.optgroup} label={g.optgroup}>
              {g.items.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </optgroup>
          ))}
        </select>
      </PASpecField>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <PAGroupBuilder label="Group A" group={spec.group_a} setGroup={g => setSpec({ ...spec, group_a: g })} />
        <PAGroupBuilder label="Group B" group={spec.group_b} setGroup={g => setSpec({ ...spec, group_b: g })} />
      </div>
    </div>
  );
}

function PAGroupComparisonResult({ result, vars, spec }) {
  const { ComposedChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ResponsiveContainer } = Recharts;
  const yMeta = (vars || []).find(v => v.key === spec.y);
  const isPct = _PA_isPctVar(yMeta);
  const fmt = _PA_fmtFor(yMeta);

  // Build wide-format data: [{year, A, B, Diff}]
  const data = React.useMemo(() => {
    const years = [...new Set(result.series.flatMap(s => s.points.map(p => p.year)))].sort((a, b) => a - b);
    const map = { A: {}, B: {}, 'A−B': {} };
    result.series.forEach(s => s.points.forEach(p => { map[s.group][p.year] = p.value; }));
    return years.map(y => ({ year: y, A: map.A[y] ?? null, B: map.B[y] ?? null, Diff: map['A−B'][y] ?? null }));
  }, [result]);
  const hasPlottable = data.some(d => d.A != null || d.B != null);
  if (!hasPlottable) return <PANoData />;

  return (
    <>
      <window.ChartShell title={`${yMeta ? yMeta.label : spec.y}: Group A vs B (with A−B difference, right axis)`} height={340}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 56, bottom: 0, left: 0 }}>
            <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="year" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false} interval={2} />
            <YAxis yAxisId="left" tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false}
                   tickFormatter={v => isPct ? (v * 100).toFixed(0) + '%' : v.toFixed(2)} width={48} />
            <YAxis yAxisId="right" orientation="right"
                   tick={{ fill: window.C.purple, fontSize: 10, fontFamily: window.mono }} axisLine={false} tickLine={false}
                   tickFormatter={v => isPct ? (v * 100).toFixed(0) + '%' : v.toFixed(2)} width={48} />
            <Tooltip content={<window.CustomTooltip fmt={fmt} />} />
            <Legend wrapperStyle={{ fontFamily: window.mono, fontSize: 10, color: window.C.textMuted }} />
            <Line yAxisId="left"  type="monotone" dataKey="A"    name="Group A"   stroke={window.C.blue}   strokeWidth={2}   dot={false} connectNulls />
            <Line yAxisId="left"  type="monotone" dataKey="B"    name="Group B"   stroke={window.C.sky}    strokeWidth={2}   dot={false} strokeDasharray="5 4" connectNulls />
            <Line yAxisId="right" type="monotone" dataKey="Diff" name="A − B"     stroke={window.C.purple} strokeWidth={1.6} dot={false} strokeDasharray="2 3" connectNulls />
          </ComposedChart>
        </ResponsiveContainer>
      </window.ChartShell>
      <PAStatPills items={[
        `N_A = ${result.sample.n_a.toLocaleString()} obs / ${result.sample.n_systems_a} systems`,
        `N_B = ${result.sample.n_b.toLocaleString()} obs / ${result.sample.n_systems_b} systems`,
        result.sample.fy_min != null ? `FY ${result.sample.fy_min}–${result.sample.fy_max}` : null,
      ]} />
    </>
  );
}

// ── CORRELATION ──────────────────────────────────────────────────────────────

function PACorrelationForm({ spec, setSpec, vars }) {
  const opts = _PA_yxOptions(vars);
  function setVars(vs) {
    // If current scatter pair is no longer fully covered, clear it.
    const stillValid = (spec.scatter_pair || []).every(v => vs.includes(v));
    setSpec({ ...spec, vars: vs, scatter_pair: stillValid ? spec.scatter_pair : null });
  }
  return (
    <div style={{ ..._PA_cardStyle, display: 'grid', gap: 16 }}>
      <PASpecField label="Variables (≥2)" hint="Cmd/Ctrl-click to select multiple. Click any cell in the matrix to scatter that pair.">
        <PAMultiSelect value={spec.vars || []} onChange={setVars} options={opts} height={170} />
      </PASpecField>
    </div>
  );
}

function PACorrelationResult({ result, vars, spec, onScatterPairClick }) {
  const { ScatterChart, Scatter, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } = Recharts;
  const [method, setMethod] = React.useState('pearson');
  const labelFor = key => _PA_yLabel(vars, key);
  const matrix = result.matrices[method];
  const vlist = result.matrices.vars;

  return (
    <>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
        <span style={{ fontFamily: window.mono, fontSize: 10, color: window.C.textMuted, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Method:</span>
        {['pearson', 'spearman'].map(m => (
          <button key={m} onClick={() => setMethod(m)} style={{
            background: method === m ? 'rgba(59,130,246,0.12)' : 'transparent',
            border: `1px solid ${method === m ? window.C.blue : window.C.border}`,
            color: method === m ? window.C.textPrimary : window.C.textMuted,
            fontFamily: window.mono, fontSize: 11, padding: '5px 12px', cursor: 'pointer',
            letterSpacing: '0.06em', textTransform: 'uppercase',
          }}>{m}</button>
        ))}
      </div>

      <div style={{ overflowX: 'auto', marginBottom: 24 }}>
        <table style={{ borderCollapse: 'collapse', fontFamily: window.mono, fontSize: 11 }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 10px' }}></th>
              {vlist.map(v => (
                <th key={v} title={labelFor(v)} style={{
                  padding: '6px 10px', color: window.C.textMuted, fontWeight: 500,
                  borderBottom: `1px solid ${window.C.border}`, fontSize: 10,
                  textOrientation: 'mixed', writingMode: 'horizontal-tb', textAlign: 'center',
                }}>{v}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {vlist.map((vRow, i) => (
              <tr key={vRow}>
                <th title={labelFor(vRow)} style={{
                  padding: '6px 10px', color: window.C.textMuted, fontWeight: 500,
                  borderRight: `1px solid ${window.C.border}`, textAlign: 'right', fontSize: 10,
                }}>{vRow}</th>
                {vlist.map((vCol, j) => {
                  const rho = matrix[i][j];
                  const onDiag = i === j;
                  return (
                    <td key={vCol}
                        onClick={() => !onDiag && onScatterPairClick(vCol, vRow)}
                        title={`${vRow} × ${vCol}: ρ = ${rho?.toFixed(3)}`}
                        style={{
                          padding: '8px 12px', textAlign: 'center',
                          background: _PA_heatColor(rho),
                          color: Math.abs(rho) > 0.5 ? '#fff' : window.C.textPrimary,
                          cursor: onDiag ? 'default' : 'pointer',
                          border: `1px solid ${window.C.border}`,
                          minWidth: 56,
                        }}>
                      {rho == null ? '—' : rho.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {result.scatter && (
        <window.ChartShell title={`Scatter: ${labelFor(result.scatter.x_label)} vs ${labelFor(result.scatter.y_label)}`} height={300}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
              <CartesianGrid stroke={window.C.border} strokeDasharray="3 3" />
              <XAxis type="number" dataKey="x" name={result.scatter.x_label}
                     tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }}
                     axisLine={false} tickLine={false} />
              <YAxis type="number" dataKey="y" name={result.scatter.y_label}
                     tick={{ fill: window.C.textMuted, fontSize: 10, fontFamily: window.mono }}
                     axisLine={false} tickLine={false} width={48} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }}
                       content={<window.CustomTooltip fmt={v => typeof v === 'number' ? v.toFixed(3) : v} />} />
              <Scatter data={result.scatter.points} fill={window.C.blue} fillOpacity={0.35} />
            </ScatterChart>
          </ResponsiveContainer>
        </window.ChartShell>
      )}

      <PAStatPills items={[
        `N = ${result.sample.n.toLocaleString()} obs`,
        `${result.sample.n_systems} systems`,
        `FY ${result.sample.fy_min}–${result.sample.fy_max}`,
        `${vlist.length} variables`,
      ]} />
    </>
  );
}

// ── No-data fallback ─────────────────────────────────────────────────────────

function PANoData() {
  return (
    <div style={{
      border: `1px dashed ${window.C.border}`,
      padding: '32px 24px', textAlign: 'center',
      fontFamily: window.mono, color: window.C.textMuted, fontSize: 12, lineHeight: 1.7,
    }}>
      <div style={{ color: window.C.textPrimary, fontSize: 13, marginBottom: 6 }}>No plottable data</div>
      <div>The selected spec produced no observations. Try different inputs.</div>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

function AnalysisPage() {
  const [vars, setVars] = React.useState(window.__ppdVars || null);
  const [varsErr, setVarsErr] = React.useState(null);
  const [testType, setTestType] = React.useState('univariate');

  // Per-test specs — kept independently so switching tabs preserves the user's setup
  const [uniSpec, setUniSpec]   = React.useState({ y: 'omega', group_by: '' });
  const [olsSpec, setOlsSpec]   = React.useState({
    y: 'omega', xs: ['log_aum'], controls: [], fe: ['fy'],
    weights: 'equal', cluster: 'entity',
  });
  const [groupSpec, setGroupSpec] = React.useState({
    y: 'omega',
    group_a: { by: 'StateAbbrev', values: ['CA'] },
    group_b: { by: 'StateAbbrev', values: ['TX'] },
  });
  const [corrSpec, setCorrSpec] = React.useState({
    vars: ['omega', 'ActFundedRatio_GASB', 'InvestmentReturnAssumption_GASB', 'log_aum'],
    scatter_pair: null,
  });

  const [result, setResult] = React.useState(null);
  const [resultTest, setResultTest] = React.useState(null);  // which test produced `result`
  const [loading, setLoading] = React.useState(false);
  const [runErr, setRunErr] = React.useState(null);

  React.useEffect(() => {
    if (vars) return;
    fetch('/api/analysis/variables')
      .then(r => r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status)))
      .then(d => { window.__ppdVars = d; setVars(d); })
      .catch(e => setVarsErr(String(e)));
  }, []);

  function buildSpec(t, override) {
    if (override) return override;
    if (t === 'univariate') return { y: uniSpec.y, group_by: uniSpec.group_by || null };
    if (t === 'ols')        return {
      y: olsSpec.y, xs: olsSpec.xs, controls: olsSpec.controls, fe: olsSpec.fe,
      weights: olsSpec.weights, cluster: olsSpec.cluster,
    };
    if (t === 'group_comparison') return { y: groupSpec.y, group_a: groupSpec.group_a, group_b: groupSpec.group_b };
    if (t === 'correlation') return { vars: corrSpec.vars, scatter_pair: corrSpec.scatter_pair };
  }

  function handleRun(specOverride) {
    setLoading(true); setRunErr(null); setResult(null);
    const spec = buildSpec(testType, specOverride);
    const t = testType;
    fetch('/api/analysis/run', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test: t, spec }),
    })
      .then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          throw new Error(body.detail || `HTTP ${r.status}`);
        }
        return r.json();
      })
      .then(d => { setResult(d); setResultTest(t); })
      .catch(e => setRunErr(String(e.message || e)))
      .finally(() => setLoading(false));
  }

  // Correlation cell click → re-run with scatter_pair set
  function handleScatterPairClick(vx, vy) {
    setCorrSpec({ ...corrSpec, scatter_pair: [vx, vy] });
    handleRun({ vars: corrSpec.vars, scatter_pair: [vx, vy] });
  }

  // CSV rows depend on test type
  const csvData = React.useMemo(() => {
    if (!result) return [];
    if (resultTest === 'univariate' || resultTest === 'group_comparison') {
      const out = [];
      result.series.forEach(s => s.points.forEach(p => out.push({ group: s.group, year: p.year, value: p.value, n: p.n })));
      return out;
    }
    if (resultTest === 'ols') {
      return result.coefficients.map(c => ({ name: c.name, beta: c.beta, se: c.se, t: c.t, p: c.p, ci_lo: c.ci_lo, ci_hi: c.ci_hi }));
    }
    if (resultTest === 'correlation') {
      const out = [];
      const vlist = result.matrices.vars;
      vlist.forEach((r, i) => vlist.forEach((c, j) => out.push({
        row: r, col: c, pearson: result.matrices.pearson[i][j], spearman: result.matrices.spearman[i][j],
      })));
      return out;
    }
    return [];
  }, [result, resultTest]);

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{ maxWidth: 1080, margin: '0 auto', padding: '0 8px' }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontFamily: window.mono, color: window.C.textMuted, fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 6 }}>
          Interactive Tests
        </div>
        <h1 style={{ fontFamily: window.mono, color: window.C.textPrimary, fontSize: 22, fontWeight: 700, margin: '0 0 10px' }}>
          Analysis
        </h1>
        <p style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 13, margin: 0, lineHeight: 1.7 }}>
          Run paper-style time-series and panel tests against the Public Plans Database.
          Univariate trends, OLS with controls and fixed effects, two-group event studies, and pairwise correlations — all served live from the FastAPI backend.
        </p>
      </div>

      {/* Test-type chips */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 18, flexWrap: 'wrap' }}>
        {_PA_TEST_TYPES.map(t => {
          const active = t.id === testType;
          return (
            <span key={t.id} title={t.sub} style={{ display: 'inline-flex' }}>
              <button onClick={() => setTestType(t.id)} style={{
                background: active ? 'rgba(59,130,246,0.12)' : 'transparent',
                border: `1px solid ${active ? window.C.blue : window.C.border}`,
                color: active ? window.C.textPrimary : window.C.textMuted,
                fontFamily: window.mono, fontSize: 11, padding: '8px 14px',
                cursor: 'pointer', letterSpacing: '0.05em', transition: 'all 0.15s',
              }}>
                {t.label.toUpperCase()}
              </button>
            </span>
          );
        })}
      </div>

      {/* Spec form */}
      {varsErr && (
        <div style={{ color: window.C.red, fontFamily: window.mono, fontSize: 12, marginBottom: 12 }}>
          Could not load variable list: {varsErr}
        </div>
      )}
      {!vars && !varsErr && (
        <div style={{ color: window.C.textMuted, fontFamily: window.mono, fontSize: 12, marginBottom: 12 }}>
          Loading variables…
        </div>
      )}
      {vars && (
        <>
          {testType === 'univariate'        && <PAUnivariateForm        spec={uniSpec}   setSpec={setUniSpec}   vars={vars} />}
          {testType === 'ols'               && <PAOlsForm               spec={olsSpec}   setSpec={setOlsSpec}   vars={vars} />}
          {testType === 'group_comparison'  && <PAGroupComparisonForm   spec={groupSpec} setSpec={setGroupSpec} vars={vars} />}
          {testType === 'correlation'       && <PACorrelationForm       spec={corrSpec}  setSpec={setCorrSpec}  vars={vars} />}

          <div style={{ marginBottom: 24 }}>
            <button
              onClick={() => handleRun()}
              disabled={loading}
              style={{
                background: window.C.blue, border: 'none', color: '#fff',
                fontFamily: window.mono, fontSize: 12,
                padding: '10px 26px', cursor: loading ? 'wait' : 'pointer',
                letterSpacing: '0.08em', fontWeight: 600,
                opacity: loading ? 0.6 : 1, boxShadow: window.C.glowBlue,
              }}>
              {loading ? 'RUNNING…' : 'RUN ▸'}
            </button>
          </div>
        </>
      )}

      {runErr && (
        <div style={{
          borderLeft: `3px solid ${window.C.red}`,
          background: 'rgba(248,113,113,0.07)',
          padding: '10px 16px', marginBottom: 20,
          color: window.C.red, fontFamily: window.mono, fontSize: 12,
        }}>{runErr}</div>
      )}

      {/* Result */}
      {result && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 12, flexWrap: 'wrap' }}>
            <div style={{ fontFamily: window.sans, color: window.C.textMuted, fontSize: 12, lineHeight: 1.6 }}>
              {result.summary}
            </div>
            <window.DownloadCSV
              data={csvData}
              filename={`analysis_${resultTest}.csv`}
              label="DOWNLOAD CSV"
            />
          </div>

          {resultTest === 'univariate'        && <PAUnivariateResult        result={result} vars={vars} spec={uniSpec}   />}
          {resultTest === 'ols'               && <PAOlsResult               result={result} vars={vars} spec={olsSpec}   />}
          {resultTest === 'group_comparison'  && <PAGroupComparisonResult   result={result} vars={vars} spec={groupSpec} />}
          {resultTest === 'correlation'       && <PACorrelationResult       result={result} vars={vars} spec={corrSpec} onScatterPairClick={handleScatterPairClick} />}
        </div>
      )}
    </div>
  );
}
