// PPD Explorer — Shared Components
// Exports to window: C (colors), InsightBox, KPITile, SectionHeader, ChartShell, CustomTooltip, DownloadCSV

const C = {
  bg: '#080C14',
  surface: '#0D1526',
  card: '#111D35',
  blue: '#3B82F6',
  sky: '#38BDF8',
  green: '#34D399',
  red: '#F87171',
  purple: '#A78BFA',
  textPrimary: '#E2EAF4',
  textMuted: '#7A9BBF',
  border: '#1E3254',
  glowBlue: '0 0 12px rgba(59,130,246,0.35)',
  chartColors: ['#3B82F6','#38BDF8','#34D399','#F87171','#A78BFA','#FB923C'],
};

const mono = 'IBM Plex Mono, monospace';
const sans = 'IBM Plex Sans, sans-serif';

function InsightBox({ text }) {
  return (
    <div style={{
      borderLeft: `3px solid ${C.blue}`,
      background: 'rgba(59,130,246,0.07)',
      padding: '10px 16px',
      marginBottom: 20,
      color: C.textMuted,
      fontSize: 13,
      fontFamily: sans,
      lineHeight: 1.6,
      borderRadius: '0 4px 4px 0',
    }}>{text}</div>
  );
}

function KPITile({ label, value, sub, accent }) {
  const col = accent || C.blue;
  return (
    <div style={{
      background: C.card,
      borderLeft: `3px solid ${col}`,
      padding: '18px 22px',
      boxShadow: `0 0 14px rgba(59,130,246,0.18)`,
      flex: 1,
      minWidth: 0,
    }}>
      <div style={{ color: C.textMuted, fontSize: 10, fontFamily: mono, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>{label}</div>
      <div style={{ color: C.textPrimary, fontSize: 26, fontFamily: mono, fontWeight: 600, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ color: C.textMuted, fontSize: 12, fontFamily: sans, marginTop: 6, lineHeight: 1.4 }}>{sub}</div>}
    </div>
  );
}

function SectionHeader({ children }) {
  return (
    <div style={{
      color: C.textMuted,
      fontFamily: mono,
      fontSize: 10,
      textTransform: 'uppercase',
      letterSpacing: '0.14em',
      marginBottom: 14,
      marginTop: 32,
      paddingBottom: 8,
      borderBottom: `1px solid ${C.border}`,
    }}>{children}</div>
  );
}

function ChartShell({ title, insight, children, height = 260 }) {
  return (
    <div style={{ marginBottom: 36 }}>
      {title && (
        <div style={{ color: C.textPrimary, fontFamily: mono, fontSize: 13, fontWeight: 600, marginBottom: 10, letterSpacing: '0.03em' }}>{title}</div>
      )}
      {insight && <InsightBox text={insight} />}
      <div style={{ width: '100%', height }}>{children}</div>
    </div>
  );
}

function CustomTooltip({ active, payload, label, fmt }) {
  if (!active || !payload || !payload.length) return null;
  const formatter = fmt || (v => typeof v === 'number' ? v.toFixed(1) : v);
  return (
    <div style={{
      background: '#0A1020',
      border: `1px solid ${C.border}`,
      padding: '10px 14px',
      borderRadius: 4,
      fontFamily: mono,
      fontSize: 12,
      minWidth: 140,
    }}>
      <div style={{ color: C.textMuted, marginBottom: 8, fontSize: 11 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || C.textPrimary, marginBottom: 3 }}>
          <span style={{ color: C.textMuted }}>{p.name}: </span>{formatter(p.value)}
        </div>
      ))}
    </div>
  );
}

function DownloadCSV({ data, filename, label }) {
  function download() {
    if (!data || !data.length) return;
    const headers = Object.keys(data[0]);
    const rows = data.map(row => headers.map(h => {
      const v = row[h];
      return typeof v === 'string' && v.includes(',') ? `"${v}"` : v;
    }).join(','));
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'data.csv';
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <button onClick={download} style={{
      background: 'transparent',
      border: `1px solid ${C.blue}`,
      color: C.blue,
      fontFamily: mono,
      fontSize: 11,
      padding: '6px 14px',
      cursor: 'pointer',
      letterSpacing: '0.06em',
      transition: 'all 0.15s',
    }}
    onMouseEnter={e => { e.currentTarget.style.background = 'rgba(59,130,246,0.12)'; }}
    onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
    >↓ {label || 'DOWNLOAD CSV'}</button>
  );
}

function pct(v, d = 1) { return typeof v === 'number' ? v.toFixed(d) + '%' : '—'; }
function dollars(v) { return v >= 1000 ? '$' + (v / 1000).toFixed(1) + 'T' : '$' + v + 'B'; }

Object.assign(window, { C, mono, sans, InsightBox, KPITile, SectionHeader, ChartShell, CustomTooltip, DownloadCSV, pct, dollars });
