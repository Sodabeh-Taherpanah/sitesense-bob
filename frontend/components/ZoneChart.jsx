// ZoneChart.jsx
// Time-series line chart for a single zone's historical readings.
// Props: zoneId (string), history (array of {timestamp, water_level})
// Uses Recharts LineChart loaded from CDN.

const { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
        ReferenceLine, ResponsiveContainer } = Recharts;

function ZoneChart({ zoneId, history }) {
  if (!history || history.length === 0) {
    return (
      <div style={{ textAlign: "center", color: "#6b7280", padding: "40px 0" }}>
        No history available for {zoneId}
      </div>
    );
  }

  const data = history.map(r => ({
    time: new Date(r.timestamp).toLocaleTimeString(),
    level: r.water_level,
  }));

  return (
    <div>
      <h3 style={{ margin: "0 0 12px", fontSize: "14px", color: "#374151" }}>
        Water Level History — {zoneId}
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="time" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
          <YAxis domain={[0, 4]} tick={{ fontSize: 10 }} unit=" m" />
          <Tooltip formatter={(v) => [`${v.toFixed(3)} m`, "Water Level"]} />
          {/* threshold reference lines */}
          <ReferenceLine y={2.0} stroke="#f59e0b" strokeDasharray="4 2"
            label={{ value: "Warning", position: "right", fontSize: 10, fill: "#f59e0b" }} />
          <ReferenceLine y={2.5} stroke="#ef4444" strokeDasharray="4 2"
            label={{ value: "Critical", position: "right", fontSize: 10, fill: "#ef4444" }} />
          <Line type="monotone" dataKey="level" stroke="#3b82f6"
            dot={false} strokeWidth={2} animationDuration={300} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
