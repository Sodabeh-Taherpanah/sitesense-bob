// app.js
// React app root: fetches data, holds state, renders ZoneCard + AlertList + ZoneChart.
// Polls the backend every 5 seconds via useEffect + setInterval.

const { useState, useEffect, useCallback } = React;

const POLL_INTERVAL = 5000; // ms

function App() {
  const [zones, setZones]         = useState([]);
  const [alerts, setAlerts]       = useState([]);
  const [history, setHistory]     = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [lastUpdated, setLastUpdated]   = useState(null);
  const [error, setError]         = useState(null);

  // Fetch zones + alerts together
  const fetchDashboard = useCallback(async () => {
    try {
      const [z, a] = await Promise.all([api.getZones(), api.getAlerts()]);
      setZones(z);
      setAlerts(a);
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      setError("Cannot reach backend — retrying…");
    }
  }, []);

  // Fetch history when a zone is selected
  const fetchHistory = useCallback(async (zoneId) => {
    try {
      const h = await api.getHistory(zoneId);
      setHistory(h);
    } catch {
      setHistory([]);
    }
  }, []);

  // Initial load + polling
  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchDashboard]);

  // Re-fetch history whenever selectedZone or zones update
  useEffect(() => {
    if (selectedZone) fetchHistory(selectedZone);
  }, [selectedZone, zones, fetchHistory]);

  const handleZoneClick = (zoneId) => {
    setSelectedZone(prev => prev === zoneId ? null : zoneId);
    if (selectedZone !== zoneId) fetchHistory(zoneId);
  };

  // Summary counts
  const counts = { ok: 0, warning: 0, critical: 0 };
  zones.forEach(z => { counts[z.status] = (counts[z.status] || 0) + 1; });

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto", padding: "24px 16px", fontFamily: "system-ui, sans-serif" }}>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "22px", color: "#1f2328" }}>
            🏗 SiteSense Dashboard
          </h1>
          <p style={{ margin: "4px 0 0", fontSize: "12px", color: "#6b7280" }}>
            Construction Site Water Level Monitor
          </p>
        </div>
        <div style={{ textAlign: "right", fontSize: "12px", color: "#6b7280" }}>
          {lastUpdated ? `Updated: ${lastUpdated}` : "Loading…"}
          <div style={{ marginTop: "4px" }}>
            <span style={{ marginRight: "10px", color: "#22c55e" }}>● {counts.ok} OK</span>
            <span style={{ marginRight: "10px", color: "#f59e0b" }}>● {counts.warning} Warning</span>
            <span style={{ color: "#ef4444" }}>● {counts.critical} Critical</span>
          </div>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div style={{ background: "#fef3c7", border: "1px solid #fcd34d", borderRadius: "6px",
          padding: "10px 14px", marginBottom: "16px", fontSize: "13px", color: "#92400e" }}>
          ⚠ {error}
        </div>
      )}

      {/* Alerts section */}
      <section style={{ marginBottom: "28px" }}>
        <h2 style={{ fontSize: "14px", fontWeight: "600", color: "#374151",
          textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "10px" }}>
          🚨 Active Alerts
        </h2>
        <AlertList alerts={alerts} />
      </section>

      {/* Zone cards grid */}
      <section style={{ marginBottom: "28px" }}>
        <h2 style={{ fontSize: "14px", fontWeight: "600", color: "#374151",
          textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "10px" }}>
          📡 Zone Status — click a zone to see its history
        </h2>
        {zones.length === 0 ? (
          <div style={{ color: "#6b7280", fontSize: "13px", padding: "20px 0" }}>
            No sensor data yet. Start the simulator to populate zones.
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap: "12px" }}>
            {zones.map(zone => (
              <ZoneCard
                key={zone.zone_id}
                zone={zone}
                selected={selectedZone === zone.zone_id}
                onClick={() => handleZoneClick(zone.zone_id)}
              />
            ))}
          </div>
        )}
      </section>

      {/* History chart */}
      {selectedZone && (
        <section style={{
          background: "#f9fafb", border: "1px solid #e5e7eb",
          borderRadius: "8px", padding: "20px", marginBottom: "16px",
        }}>
          <ZoneChart zoneId={selectedZone} history={history} />
        </section>
      )}

      {/* Footer */}
      <footer style={{ textAlign: "center", fontSize: "11px", color: "#9ca3af",
        borderTop: "1px solid #e5e7eb", paddingTop: "12px", marginTop: "8px" }}>
        Polling every {POLL_INTERVAL / 1000}s &nbsp;·&nbsp; Thresholds: Warning ≥ 2.0 m · Critical ≥ 2.5 m
      </footer>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
