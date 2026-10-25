import React, { useState, useEffect } from "react";

export function AdminDashboard() {
  const [tickets, setTickets] = useState([]);
  const [filter, setFilter] = useState("");

  const fetchTickets = async () => {
    try {
      const url = filter ? `/api/tickets?status=${filter}` : "/api/tickets";
      const res = await fetch(url);
      const data = await res.json();
      setTickets(data.tickets || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [filter]);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
        <h2>Support Ticket Queue & Escalations</h2>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="OPEN">Open</option>
          <option value="ESCALATED">Escalated</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="RESOLVED">Resolved</option>
        </select>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Subject</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Assigned</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t) => (
              <tr key={t.id}>
                <td><strong>{t.id}</strong></td>
                <td>{t.subject}</td>
                <td><span className={`badge badge-${t.priority.toLowerCase()}`}>{t.priority}</span></td>
                <td><span className={`badge badge-${t.status.toLowerCase()}`}>{t.status}</span></td>
                <td>{t.assigned_agent}</td>
                <td>{t.created_at?.slice(0, 16)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
