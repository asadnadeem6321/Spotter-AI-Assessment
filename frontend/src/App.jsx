import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";

const colors = ["#ef6351", "#24a19c", "#f3b562"];
const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

function FitRoutes({ routes }) {
  const map = useMap();
  if (routes.length) {
    const points = routes.flatMap((route) => route.coordinates);
    map.fitBounds(points, { padding: [28, 28] });
  }
  return null;
}

function riskColor(risk) {
  return { low: "#24a19c", moderate: "#f3b562", high: "#ef9b45", severe: "#ef6351", "no travel": "#7a1f3d" }[risk] || "#607080";
}

function RouteMap({ routes, selectedId, forecastHour }) {
  const selected = routes.find((route) => route.id === selectedId);
  return (
    <MapContainer className="route-map" center={[39.5, -77]} zoom={6} scrollWheelZoom>
      <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <FitRoutes routes={routes} />
      {routes.map((route, index) => (
        <span key={route.id}>
          <Polyline positions={route.coordinates} pathOptions={{ color: colors[index], weight: route.id === selectedId ? 6 : 3, opacity: route.id === selectedId ? 1 : 0.48 }} />
          {route.checkpoints.map((point) => (
            <CircleMarker key={`${route.id}-${point.miles}`} center={[point.latitude, point.longitude]} radius={selected?.id === route.id ? 7 : 5} pathOptions={{ color: riskColor(point.forecast?.[forecastHour]?.risk || point.risk), fillColor: riskColor(point.forecast?.[forecastHour]?.risk || point.risk), fillOpacity: 0.85 }}>
              <Tooltip>{`${point.miles.toFixed(0)} mi · ${point.forecast?.[forecastHour]?.risk || point.risk} · +${forecastHour}h`}</Tooltip>
            </CircleMarker>
          ))}
        </span>
      ))}
    </MapContainer>
  );
}

function App() {
  const [form, setForm] = useState({ origin: "New York, NY", destination: "Washington, DC", departure: "2026-10-19T08:00", load_weight_lb: "35000" });
  const [routes, setRoutes] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [forecastHour, setForecastHour] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [backendStatus, setBackendStatus] = useState("checking");

  useEffect(() => {
    let active = true;
    fetch(`${API_URL}/api/health/`)
      .then((response) => {
        if (!response.ok) throw new Error("Backend health check failed");
        if (active) setBackendStatus("connected");
      })
      .catch(() => {
        if (active) setBackendStatus("unavailable");
      });
    return () => {
      active = false;
    };
  }, []);

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/route-plan/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...form, load_weight_lb: Number(form.load_weight_lb) }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Unable to calculate routes");
      setRoutes(data.routes);
      setSelectedId(data.recommended_route_id);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header className="masthead">
        <div><p className="eyebrow">SPOTTER / ROUTE DESK</p><h1>Weather-aware routing for the long haul.</h1><p className="lede">Compare route risk at the moment your truck reaches each checkpoint.</p></div>
        <div className={`status-dot ${backendStatus}`}><span /> {backendStatus === "checking" ? "Connecting to API" : backendStatus === "connected" ? "Backend connected" : "Backend unavailable"}</div>
      </header>
      <section className="workspace">
        <aside className="control-panel">
          <div className="panel-heading"><p className="eyebrow">Trip profile</p><h2>Plan a safer run</h2></div>
          <form onSubmit={submit}>
            <label>Origin<input required name="origin" value={form.origin} onChange={updateField} /></label>
            <label>Destination<input required name="destination" value={form.destination} onChange={updateField} /></label>
            <label>Departure (UTC)<input required type="datetime-local" name="departure" value={form.departure} onChange={updateField} /></label>
            <label>Load weight <span className="unit">LB</span><input required min="0" step="1" type="number" name="load_weight_lb" value={form.load_weight_lb} onChange={updateField} /></label>
            <button type="submit" disabled={loading}>{loading ? "Calculating routes..." : "Calculate route options"}</button>
          </form>
          {error && <p className="error">{error}</p>}
          <div className="rule-note"><strong>Risk model</strong><span>Wind, rain and snow are sampled at the truck&apos;s estimated arrival time. Load overrides are applied before ranking.</span></div>
        </aside>
        <section className="map-panel">
          <div className="map-toolbar"><div><p className="eyebrow">Trip corridor</p><h2>{routes.length ? "Three options, one clear recommendation" : "Your route picture will appear here"}</h2></div><div className="forecast"><label htmlFor="forecast">Forecast window <strong>{forecastHour}h</strong></label><input id="forecast" type="range" min="0" max="48" step="1" value={forecastHour} onChange={(event) => setForecastHour(Number(event.target.value))} /></div></div>
          <div className="map-wrap">{routes.length ? <RouteMap routes={routes} selectedId={selectedId} forecastHour={forecastHour} /> : <div className="map-empty"><span className="map-mark">+</span><p>Enter a trip to see weather risk along the corridor.</p></div>}</div>
        </section>
      </section>
      {routes.length > 0 && <section className="route-results"><div className="results-heading"><div><p className="eyebrow">Route comparison</p><h2>Decision support</h2></div><p className="legend"><span className="legend-dot low" /> Low <span className="legend-dot moderate" /> Moderate <span className="legend-dot severe" /> Severe</p></div><div className="route-grid">{routes.map((route, index) => <button className={`route-card ${selectedId === route.id ? "selected" : ""}`} key={route.id} onClick={() => setSelectedId(route.id)}><div className="route-card-top"><span className="route-line" style={{ background: colors[index] }} /> <span>OPTION {index + 1}</span>{selectedId === route.id && <strong className="recommended">RECOMMENDED</strong>}</div><h3>{route.summary}</h3><div className="route-stats"><span><strong>{Math.round(route.distance_miles)}</strong> mi</span><span><strong>{Math.round(route.duration_minutes / 60)}h {Math.round(route.duration_minutes % 60)}m</strong></span><span><strong>{route.average_risk.toFixed(1)}</strong> avg risk</span></div><p className="route-foot">{Math.round(route.severe_miles)} severe mi · {Math.round(route.high_miles)} high mi · {route.checkpoints.length} checkpoints</p></button>)}</div></section>}
    </main>
  );
}

export default App;
