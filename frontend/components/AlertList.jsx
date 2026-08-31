// AlertList.jsx
// Renders the list of active alerts (zones above critical threshold).
// Props: alerts (array of {zone_id, latest_water_level, timestamp})

function AlertList({ alerts }) {
  if (alerts.length === 0) {
    return (
      <div style={{
        padding: "12px 16px",
        background: "#f0fdf4",
        border: "1px solid #bbf7d0",
        borderRadius: "6px",
        color: "#16a34a",
        fontSize: "13px",
      }}>
        ✓ No active alerts — all zones within safe levels.
      </div>
    );
  }

  return (
    <div>
      {alerts.map(alert => (
        <div key={alert.zone_id} style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 14px",
          marginBottom: "6px",
          background: "#fef2f2",
          border: "1px solid #fecaca",
          borderLeft: "4px solid #ef4444",
          borderRadius: "6px",
        }}>
          <div>
            <strong style={{ color: "#dc2626" }}>{alert.zone_id}</strong>
            <span style={{ marginLeft: "10px", fontSize: "12px", color: "#6b7280" }}>
              {new Date(alert.timestamp).toLocaleTimeString()}
            </span>
          </div>
          <span style={{
            fontWeight: "bold", fontSize: "18px", color: "#dc2626",
          }}>
            {alert.latest_water_level.toFixed(2)} m
          </span>
        </div>
      ))}
    </div>
  );
}
