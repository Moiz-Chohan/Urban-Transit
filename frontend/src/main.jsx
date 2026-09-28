import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import axios from 'axios';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import './styles.css';

const CHART_YELLOW = '#F2B705';
const CHART_YELLOW_DARK = '#B88700';
const CHART_GRID = '#2D2A20';

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
  timeout: 8000,
});

const navigation = [
  { id: 'Overview', label: 'Dashboard', icon: '⌂' },
  { id: 'Routes', label: 'Routes', icon: '⇄' },
  { id: 'Flow', label: 'Passenger Flow', icon: '↗' },
  { id: 'Delays', label: 'Delays', icon: '◷' },
  { id: 'Occupancy', label: 'Occupancy', icon: '▥' },
  { id: 'Recommendations', label: 'Recommendations', icon: '✓' },
  { id: 'Forecast', label: 'Forecast', icon: '↗' },
  { id: 'Quality', label: 'Data Quality', icon: '✓' },
  { id: 'Comparison', label: 'Model Comparison', icon: '≈' },
  { id: 'Map', label: 'Network Map', icon: '⌖' },
  { id: 'What-if', label: 'What-if', icon: '⌁' },
];

const pageCopy = {
  Overview: ['Dashboard', 'A clear overview of the transport network.'],
  Routes: ['Route Performance', 'Compare passenger demand, occupancy and delays.'],
  Flow: ['Passenger Flow', 'See where passenger movement is concentrated.'],
  Delays: ['Delay Analysis', 'Review routes with higher average delays.'],
  Occupancy: ['Occupancy Analysis', 'Review routes operating close to capacity.'],
  Recommendations: ['Recommendations', 'Route-level actions based on the available data.'],
  Forecast: ['Demand Forecast', 'Review historical demand and future forecast values.'],
  Quality: ['Data Quality', 'Review validation rules and data-quality findings.'],
  Comparison: ['Model Comparison', 'Compare independent Spark and Python model outputs.'],
  Map: ['Network Map', 'Explore the geographic coverage of transport stops.'],
  'What-if': ['What-if Analysis', 'Test a service change and view the estimated occupancy.'],
};

function App() {
  const [isSignedIn, setIsSignedIn] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [activePage, setActivePage] = useState('Overview');
  const [dashboard, setDashboard] = useState(null);
  const [routeRows, setRouteRows] = useState([]);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [loginError, setLoginError] = useState('');

  useEffect(() => {
    if (!isSignedIn) {
      return;
    }

    Promise.all([api.get('/dashboard'), api.get('/routes')])
      .then(([dashboardResponse, routesResponse]) => {
        setDashboard(dashboardResponse.data);
        setRouteRows(routesResponse.data);
      })
      .catch(() => {
        setLoginError('The local analytics server is not available.');
      });
  }, [isSignedIn]);

  const handleLogin = async (event) => {
    event.preventDefault();
    setLoginError('');

    try {
      await api.post('/login', {
        email: email.trim().toLowerCase(),
        password,
      });
      setIsSignedIn(true);
    } catch (error) {
      if (!error.response) {
        setLoginError('The local analytics server is not available.');
      } else {
        setLoginError('Email or password is incorrect.');
      }
    }
  };

  const currentCopy = pageCopy[activePage];

  if (!isSignedIn) {
    return (
      <LoginScreen
        email={email}
        password={password}
        error={loginError}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onSubmit={handleLogin}
      />
    );
  }

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        onNavigate={(page) => {
          setActivePage(page);
          setMobileOpen(false);
        }}
      />

      {mobileOpen && (
        <button
          className="mobile-backdrop"
          type="button"
          onClick={() => setMobileOpen(false)}
          aria-label="Close menu"
        />
      )}

      <main className="main-content">
        <header className="topbar">
          <button
            className="mobile-menu"
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            ☰
          </button>

          <div className="heading-wrap">
            <span className="eyebrow">URBAN TRANSIT</span>
            <h1>{currentCopy[0]}</h1>
            <p>{currentCopy[1]}</p>
          </div>

          <button
            className="logout-button"
            type="button"
            onClick={() => setIsSignedIn(false)}
          >
            Log out
          </button>
        </header>

        {activePage === 'Overview' && (
          <Overview
            dashboard={dashboard}
            routes={routeRows}
            onNavigate={setActivePage}
          />
        )}

        {activePage === 'Routes' && <RouteTable rows={routeRows} />}

        {['Flow', 'Delays', 'Occupancy'].includes(activePage) && (
          <AnalyticsPage page={activePage} />
        )}

        {activePage === 'Recommendations' && <Recommendations />}
        {activePage === 'Forecast' && <ForecastPage />}
        {activePage === 'Quality' && <QualityPage />}
        {activePage === 'Comparison' && <ComparisonPage />}
        {activePage === 'Map' && <MapPage />}
        {activePage === 'What-if' && <WhatIfSimulator />}
      </main>
    </div>
  );
}

function LoginScreen({
  email,
  password,
  error,
  onEmailChange,
  onPasswordChange,
  onSubmit,
}) {
  return (
    <div className="login-screen">
      <div className="login-photo" />

      <div className="login-panel">

        <p className="brand-name">UrbanTransit</p>
        <h1>Transport data, kept simple.</h1>
        <p className="login-intro">
          View passenger demand, route performance, delays and occupancy in one place.
        </p>

        <form onSubmit={onSubmit}>
          <label htmlFor="email">
            Email address
            <input
              id="email"
              value={email}
              onChange={(event) => onEmailChange(event.target.value)}
              type="email"
              autoComplete="username"
              placeholder="Enter your email"
              required
            />
          </label>

          <label htmlFor="password">
            Password
            <input
              id="password"
              value={password}
              onChange={(event) => onPasswordChange(event.target.value)}
              type="password"
              autoComplete="current-password"
              placeholder="Enter your password"
              required
            />
          </label>

          {error && <div className="form-error">{error}</div>}

          <button className="primary-button" type="submit">
            Sign in
          </button>
        </form>
      </div>
    </div>
  );
}

function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      
      <nav>
        <p className="nav-label">MENU</p>
        {navigation.map((item) => (
          <button
            key={item.id}
            className={activePage === item.id ? 'nav-item active' : 'nav-item'}
            type="button"
            onClick={() => onNavigate(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}

function Overview({ dashboard, routes, onNavigate }) {
  const cards = [
    ['Passenger records', formatNumber(dashboard?.records), 'Total observations'],
    [
      'Average occupancy',
      dashboard ? `${Math.round(dashboard.avg_occupancy * 100)}%` : '—',
      'Network average',
    ],
    [
      'Average delay',
      dashboard ? `${Number(dashboard.avg_delay).toFixed(1)} min` : '—',
      'Recorded trips',
    ],
    ['Overcrowded trips', formatNumber(dashboard?.overcrowded), '95%+ capacity'],
  ];

  const chartRows = routes.slice(0, 10).map((route) => ({
    route: route.route_id,
    passengers: Number(route.avg_passengers || 0),
  }));

  return (
    <>
      <section className="welcome-banner">
        <div className="welcome-content">
          <span className="section-label">NETWORK OVERVIEW</span>
          <h2>See the network at a glance.</h2>
          <p>
            Passenger demand, occupancy and service delays in one view.
          </p>
        </div>
      </section>

      <div className="metric-grid">
        {cards.map(([label, value, note]) => (
          <MetricCard key={label} label={label} value={value} note={note} />
        ))}
      </div>

      <div className="content-grid two-one">
        <Panel
          title="Route demand"
          subtitle="Average passenger count by route"
          action={(
            <button
              className="text-button"
              type="button"
              onClick={() => onNavigate('Routes')}
            >
              View routes
            </button>
          )}
        >
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart
                data={chartRows}
                barSize={22}
                margin={{ left: -20, right: 10 }}
              >
                <CartesianGrid vertical={false} stroke={CHART_GRID} />
                <XAxis
                  dataKey="route"
                  tick={{ fill: '#71818D', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#71818D', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar
                  dataKey="passengers"
                  fill={CHART_YELLOW}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Network summary" subtitle="Current operating figures">
          <div className="summary-list">
            <SummaryRow
              label="Routes monitored"
              value={formatNumber(dashboard?.routes)}
            />
            <SummaryRow
              label="Capacity pressure"
              value={
                dashboard?.overcrowded
                  ? `${formatNumber(dashboard.overcrowded)} trips`
                  : 'Low'
              }
            />
            <SummaryRow
              label="Average delay"
              value={
                dashboard
                  ? `${Number(dashboard.avg_delay).toFixed(1)} min`
                  : '—'
              }
            />
          </div>

          <button
            className="secondary-button"
            type="button"
            onClick={() => onNavigate('What-if')}
          >
            Open what-if analysis
          </button>
        </Panel>
      </div>
    </>
  );
}

function MetricCard({ label, value, note }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value ?? '—'}</strong>
      <small>{note}</small>
    </article>
  );
}

function SummaryRow({ label, value }) {
  return (
    <div className="summary-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Panel({ title, subtitle, action, children }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function RouteTable({ rows }) {
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState('avg_passengers');
  const filtered = useMemo(() => rows
    .filter((row) => String(row.route_id || '').toLowerCase().includes(query.toLowerCase()))
    .slice()
    .sort((a, b) => Number(b[sort] || 0) - Number(a[sort] || 0)), [rows, query, sort]);

  const exportData = () => {
    window.open('http://127.0.0.1:5000/api/export/routes', '_blank');
  };

  return (
    <Panel
      title="Route performance"
      subtitle={`${filtered.length} matching route records`}
      action={<button className="secondary-button compact-button" type="button" onClick={exportData}>Export CSV</button>}
    >
      <div className="table-tools">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search route" aria-label="Search route" />
        <select value={sort} onChange={(event) => setSort(event.target.value)} aria-label="Sort routes">
          <option value="avg_passengers">Demand</option>
          <option value="avg_occupancy">Occupancy</option>
          <option value="avg_delay">Delay</option>
          <option value="performance_score">Performance</option>
        </select>
      </div>
      <div className="table-scroll">
        <table>
          <thead><tr><th>Route</th><th>Avg. passengers</th><th>Occupancy</th><th>Delay</th><th>Status</th></tr></thead>
          <tbody>
            {filtered.slice(0, 100).map((row, index) => (
              <tr key={`${row.route_id}-${index}`}>
                <td><strong className="route-name">{row.route_id}</strong></td>
                <td>{Number(row.avg_passengers || 0).toFixed(1)}</td>
                <td><Progress value={Number(row.avg_occupancy || 0) * 100} /></td>
                <td>{Number(row.avg_delay || 0).toFixed(1)} min</td>
                <td>{row.category || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

function Progress({ value }) {
  return (
    <div className="progress-cell">
      <div className="progress">
        <span style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <strong>{Math.round(value)}%</strong>
    </div>
  );
}

function AnalyticsPage({ page }) {
  const [rows, setRows] = useState([]);
  const endpoint =
    page === 'Flow' ? '/flow' : page === 'Delays' ? '/delays' : '/occupancy';
  const valueKey =
    page === 'Flow'
      ? 'total_passengers'
      : page === 'Delays'
        ? 'avg_delay'
        : 'avg_occupancy';
  const labelKey = page === 'Flow' ? 'stop_id' : 'route_id';

  const chartData = useMemo(
    () =>
      [...rows]
        .sort((a, b) => Number(b[valueKey] || 0) - Number(a[valueKey] || 0))
        .slice(0, 15)
        .map((row) => ({
          label: row[labelKey],
          value: Number(row[valueKey] || 0) * (page === 'Occupancy' ? 100 : 1),
        })),
    [rows, labelKey, valueKey, page]
  );

  useEffect(() => {
    api
      .get(endpoint)
      .then((response) => setRows(response.data))
      .catch(() => setRows([]));
  }, [endpoint]);

  const subtitle =
    page === 'Flow'
      ? 'Top passenger movement locations'
      : page === 'Delays'
        ? 'Routes with the highest average delay'
        : 'Routes closest to capacity';

  const isDelay = page === 'Delays';

  return (
    <Panel title={`${page} analysis`} subtitle={subtitle}>
      <div className={`chart-wrap large analytics-chart ${isDelay ? 'delay-chart' : ''}`}>
        <ResponsiveContainer width="100%" height={isDelay ? 470 : 430}>
          {isDelay ? (
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 8, right: 42, left: 12, bottom: 8 }}
              barCategoryGap="24%"
            >
              <CartesianGrid horizontal={false} stroke="#262b2d" />
              <XAxis
                type="number"
                domain={[0, 'dataMax + 2']}
                tick={{ fill: '#8C969B', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value) => `${value}m`}
              />
              <YAxis
                type="category"
                dataKey="label"
                width={54}
                tick={{ fill: '#C7CED1', fontSize: 11, fontWeight: 600 }}
                axisLine={false}
                tickLine={false}
              />
              <ReferenceLine
                x={10}
                stroke={CHART_YELLOW_DARK}
                strokeDasharray="4 4"
                label={{ value: '10 min', position: 'top', fill: CHART_YELLOW_DARK, fontSize: 10 }}
              />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.035)' }}
                contentStyle={tooltipStyle}
                formatter={(value) => [`${Number(value).toFixed(1)} min`, 'Average delay']}
                labelFormatter={(label) => `Route ${label}`}
              />
              <Bar
                dataKey="value"
                fill={CHART_YELLOW}
                radius={[0, 6, 6, 0]}
                maxBarSize={24}
              />
            </BarChart>
          ) : (
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 55 }}>
              <CartesianGrid vertical={false} stroke={CHART_GRID} />
              <XAxis
                dataKey="label"
                tick={{ fill: '#71818D', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                angle={-35}
                textAnchor="end"
                interval={0}
              />
              <YAxis
                tick={{ fill: '#71818D', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value) => page === 'Occupancy' ? `${value}%` : value}
              />
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(value) => [
                  page === 'Occupancy'
                    ? `${Number(value).toFixed(1)}%`
                    : Number(value).toLocaleString(),
                  page === 'Occupancy' ? 'Occupancy' : 'Passengers',
                ]}
              />
              <Bar dataKey="value" fill={CHART_YELLOW} radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      <div className="chart-summary">
        <div>
          <span className="summary-dot" />
          <span>{isDelay ? 'Average delay by route' : page === 'Flow' ? 'Passenger count by stop' : 'Average occupancy by route'}</span>
        </div>
        {isDelay && <span className="summary-note">Dashed line = 10 minute reference</span>}
      </div>

      <div className="insight-strip">
        <span>Showing top {Math.min(rows.length, 15)} of {rows.length} records</span>
      </div>
    </Panel>
  );
}

function Recommendations() {
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    api
      .get('/recommendations')
      .then((response) => setRecommendations(response.data))
      .catch(() => setRecommendations([]));
  }, []);

  return (
    <div className="recommendation-grid">
      {recommendations.slice(0, 30).map((item, index) => (
        <article className="recommendation-card" key={`${item.route_id}-${index}`}>
          <div className="rec-top">
            <span
              className={`priority ${String(item.priority || '').toLowerCase()}`}
            >
              {item.priority || 'Review'}
            </span>
            <span>#{index + 1}</span>
          </div>
          <h3>{item.route_id}</h3>
          <p>{item.recommendation}</p>
          <div className="rec-evidence">
            <span>
              Occupancy{' '}
              <strong>
                {(Number(item.evidence_avg_occupancy || 0) * 100).toFixed(1)}%
              </strong>
            </span>
            <span>
              Delay{' '}
              <strong>
                {Number(item.evidence_avg_delay || 0).toFixed(1)} min
              </strong>
            </span>
          </div>
        </article>
      ))}
    </div>
  );
}

function ForecastPage() {
  const [data, setData] = useState({ historical: [], future: [] });
  useEffect(() => { api.get('/forecast').then((r) => setData(r.data)).catch(() => setData({ historical: [], future: [] })); }, []);
  const chart = [...data.historical.slice(-30).map((r) => ({ label: String(r.date).slice(5), value: Number(r.actual || 0) })), ...data.future.map((r) => ({ label: String(r.date).slice(5), value: Number(r.forecast || 0) }))];
  return <Panel title="Demand forecast" subtitle="Recent observed demand and the next forecast period.">
    <div className="chart-wrap large"><ResponsiveContainer width="100%" height={420}><LineChart data={chart}><CartesianGrid vertical={false} stroke={CHART_GRID} /><XAxis dataKey="label" tick={{ fill: '#71818D', fontSize: 11 }} /><YAxis tick={{ fill: '#71818D', fontSize: 11 }} /><Tooltip contentStyle={tooltipStyle} /><Line type="monotone" dataKey="value" stroke={CHART_YELLOW} strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer></div>
    <div className="insight-strip"><span>{data.future.length} future days forecast</span><button className="text-button" type="button" onClick={() => window.open('http://127.0.0.1:5000/api/export/forecast', '_blank')}>Export</button></div>
  </Panel>;
}

function QualityPage() {
  const [rows, setRows] = useState([]);
  useEffect(() => { api.get('/quality').then((r) => setRows(r.data)).catch(() => setRows([])); }, []);
  return <Panel title="Data quality" subtitle="Validation rules applied to the transport source data.">
    <div className="table-scroll"><table><thead><tr><th>Table</th><th>Rule</th><th>Count</th><th>Severity</th></tr></thead><tbody>{rows.map((r, i) => <tr key={i}><td>{r.table}</td><td>{r.rule}</td><td>{Number(r.count || 0).toLocaleString()}</td><td>{r.severity}</td></tr>)}</tbody></table></div>
  </Panel>;
}

function ComparisonPage() {
  const [data, setData] = useState({ cases: [], summary: [] });

  useEffect(() => {
    api
      .get('/comparison')
      .then((response) => setData(response.data))
      .catch(() => setData({ cases: [], summary: [] }));
  }, []);

  const summary = data.summary?.[0];

  const cases = data.cases || [];

  const matches = cases.filter((item) => item.match).length;
  const mismatches = cases.filter((item) => !item.match).length;

  const agreementRate = summary
    ? Number(summary.agreement_rate) * 100
    : cases.length
      ? (matches / cases.length) * 100
      : 0;

  return (
    <div className="comparison-page">
      <Panel
        title="Model comparison"
        subtitle="Compare Spark MLlib and Python predictions on unseen cases."
      >
        {summary ? (
          <>
            <div className="metric-grid comparison-metrics">
              <MetricCard
                label="Cases compared"
                value={Number(summary.cases_compared).toLocaleString()}
                note="Unseen test cases"
              />

              <MetricCard
                label="Agreement"
                value={`${agreementRate.toFixed(1)}%`}
                note="Spark vs Python"
              />

              <MetricCard
                label="Matching cases"
                value={matches.toLocaleString()}
                note="Same prediction"
              />

              <MetricCard
                label="Different cases"
                value={mismatches.toLocaleString()}
                note="Different prediction"
              />
            </div>

            <div className="comparison-overview">
              <div className="comparison-heading">
                <div>
                  <h3>Prediction agreement</h3>
                  <p>
                    Percentage of cases where both workflows produced the
                    same prediction.
                  </p>
                </div>

                <strong>{agreementRate.toFixed(1)}%</strong>
              </div>

              <div className="comparison-progress">
                <span
                  style={{
                    width: `${Math.min(Math.max(agreementRate, 0), 100)}%`,
                  }}
                />
              </div>

              <div className="comparison-legend">
                <span>
                  <i className="comparison-dot" />
                  Matching predictions
                </span>

                <span>
                  <i className="comparison-dot muted" />
                  Different predictions
                </span>
              </div>
            </div>
          </>
        ) : (
          <div className="empty-state">
            Run the Spark and Python pipelines to create comparison evidence.
          </div>
        )}

        <div className="comparison-table-section">
          <div className="panel-heading">
            <div>
              <h2>Prediction details</h2>
              <p>Sample of the compared unseen cases.</p>
            </div>

            <span className="comparison-count">
              {cases.length.toLocaleString()} cases
            </span>
          </div>

          {cases.length > 0 ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Case</th>
                    <th>Spark MLlib</th>
                    <th>Python</th>
                    <th>Result</th>
                  </tr>
                </thead>

                <tbody>
                  {cases.slice(0, 100).map((row, index) => (
                    <tr key={`${row.count_id}-${index}`}>
                      <td>
                        <strong className="route-name">
                          {row.count_id}
                        </strong>
                      </td>

                      <td>{row.spark_prediction}</td>

                      <td>{row.python_prediction}</td>

                      <td>
                        <span
                          className={
                            row.match
                              ? 'comparison-status match'
                              : 'comparison-status different'
                          }
                        >
                          {row.match ? 'Match' : 'Different'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              No comparison cases are available.
            </div>
          )}
        </div>

        <div className="insight-strip">
          <span>
            Showing {Math.min(cases.length, 100).toLocaleString()} of{' '}
            {cases.length.toLocaleString()} comparison cases
          </span>
          <span>
            Spark MLlib ↔ Python
          </span>
        </div>
      </Panel>
    </div>
  );
}

function MapPage() {
  const [stops, setStops] = useState([]);

  useEffect(() => {
    api
      .get('/map')
      .then((response) => setStops(response.data))
      .catch(() => setStops([]));
  }, []);

  const validStops = stops.filter(
    (stop) =>
      Number.isFinite(Number(stop.latitude)) &&
      Number.isFinite(Number(stop.longitude))
  );

  const lats = validStops.map((stop) => Number(stop.latitude));
  const lons = validStops.map((stop) => Number(stop.longitude));

  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLon = Math.min(...lons);
  const maxLon = Math.max(...lons);

  const latRange = maxLat - minLat || 1;
  const lonRange = maxLon - minLon || 1;

  return (
    <Panel
      title="Network map"
      subtitle="Geographic distribution of transport stops."
    >
      {validStops.length > 0 ? (
        <>
          <div className="network-map">
            {validStops.map((stop) => {
              const left =
                ((Number(stop.longitude) - minLon) / lonRange) * 92 + 4;

              const top =
                96 -
                ((Number(stop.latitude) - minLat) / latRange) * 92;

              return (
                <span
                  key={stop.stop_id}
                  className="map-stop"
                  style={{
                    left: `${left}%`,
                    top: `${top}%`,
                  }}
                  title={`${stop.stop_name || stop.stop_id}`}
                />
              );
            })}

            <div className="map-label map-label-top">
              NORTH
            </div>

            <div className="map-label map-label-bottom">
              SOUTH
            </div>
          </div>

          <div className="map-summary">
            <div>
              <span className="summary-dot" />
              <span>Transport stops</span>
            </div>

            <strong>
              {validStops.length.toLocaleString()} stops
            </strong>
          </div>
        </>
      ) : (
        <div className="empty-state">
          No geographic stop data is available.
        </div>
      )}
    </Panel>
  );
}

function WhatIfSimulator() {
  const [scenario, setScenario] = useState({
    occupancy: 0.94,
    frequency_change: 10,
    capacity_change: 0,
    demand_change: 10,
  });
  const [result, setResult] = useState(null);
  const fields = [
    ['occupancy', 'Current occupancy', '0.01'],
    ['frequency_change', 'Frequency change (%)', '1'],
    ['capacity_change', 'Capacity change (%)', '1'],
    ['demand_change', 'Demand change (%)', '1'],
  ];

  const updateScenario = (key, value) => {
    setScenario((current) => ({
      ...current,
      [key]: Number(value),
    }));
  };

  const runScenario = () => {
    api
      .post('/what-if', scenario)
      .then((response) => setResult(response.data))
      .catch(() => setResult(null));
  };

  return (
    <Panel
      title="What-if analysis"
      subtitle="Adjust service inputs and estimate occupancy."
    >
      <div className="scenario-layout">
        <div className="scenario-fields">
          {fields.map(([key, label, step]) => (
            <label key={key} htmlFor={key}>
              {label}
              <input
                id={key}
                type="number"
                step={step}
                value={scenario[key]}
                onChange={(event) => updateScenario(key, event.target.value)}
              />
            </label>
          ))}

          <button
            className="primary-button"
            type="button"
            onClick={runScenario}
          >
            Run analysis
          </button>
        </div>

        <div className="scenario-result">
          {result ? (
            <>
              <span>ESTIMATED OCCUPANCY</span>
              <strong>{(result.estimated_occupancy * 100).toFixed(1)}%</strong>
              <b className={`risk ${String(result.risk).toLowerCase()}`}>
                {result.risk}
              </b>
              <p>
                Estimate based on the selected frequency, capacity and demand changes.
              </p>
            </>
          ) : (
            <>
              <span>RESULT</span>
              <strong>—</strong>
              <p>Run the analysis to see the estimated occupancy.</p>
            </>
          )}
        </div>
      </div>
    </Panel>
  );
}

const tooltipStyle = {
  background: '#FFFFFF',
  border: '1px solid #DCE4E8',
  borderRadius: 6,
  color: '#183043',
};

const formatNumber = (value) =>
  value == null ? '—' : Number(value).toLocaleString();

createRoot(document.getElementById('root')).render(<App />);
