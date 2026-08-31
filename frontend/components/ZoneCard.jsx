// ZoneCard.jsx
// Displays a single zone's current status.
// Props: zone { zone_id, latest_water_level, status, timestamp }
//        onClick: called when card is clicked (to show chart)
//        selected: bool — highlights the card when true

function ZoneCard({ zone, onClick, selected }) {
  const STATUS_CONFIG = {
    ok:       { color: "#22c55e", label: "OK",       bg: "#f0fdf4" },
    warning:  { color: "#f59e0b", label: "WARNING",  bg: "#fffbeb" },
    critical: { color: "#ef4444", label: "CRITICAL", bg: "#fef2f2" },
  };

  const cfg = STATUS_CONFIG[zone.status] || STATUS_CONFIG.ok;
  const ts  = new Date(zone.timestamp).toLocaleTimeString();

  const cardStyle = {
    border: `2px solid ${selected ? "#3b82f6" : cfg.color}`,
    borderRadius: "8px",
    padding: "16px",
    background: selected ? "#eff6ff" : cfg.bg,
    cursor: "pointer",
    transition: "box-shadow 0.15s",
    boxShadow: selected ? "0 0 0 3px rgba(59,130,246,0.3)" : "none",
  };

  return (
    <div style={cardStyle} onClick={onClick}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <strong style={{ fontSize: "15px" }}>{zone.zone_id}</strong>
        <span style={{
          background: cfg.color, color: "#fff",
          borderRadius: "4px", padding: "2px 8px",
          fontSize: "11px", fontWeight: "bold",
        }}>
          {cfg.label}
        </span>
      </div>
      <div style={{ marginTop: "8px", fontSize: "26px", fontWeight: "bold", color: cfg.color }}>
        {zone.latest_water_level.toFixed(2)} m
      </div>
      <div style={{ marginTop: "4px", fontSize: "11px", color: "#6b7280" }}>
        Last update: {ts}
      </div>
    </div>
  );
}
