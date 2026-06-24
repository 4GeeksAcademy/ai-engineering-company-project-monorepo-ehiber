"use client";

import { useMemo, useState } from "react";

type CandidateStage = "screening" | "technical" | "final" | "hired";

type Candidate = {
  id: string;
  name: string;
  role: string;
  location: string;
  stage: CandidateStage;
  score: number;
};

const candidatesSeed: Candidate[] = [
  {
    id: "cand-001",
    name: "Alejandra Ramos",
    role: "Warehouse Ops Analyst",
    location: "Monterrey",
    stage: "technical",
    score: 86,
  },
  {
    id: "cand-002",
    name: "Diego Ortega",
    role: "Inventory Coordinator",
    location: "Zaragoza",
    stage: "screening",
    score: 74,
  },
  {
    id: "cand-003",
    name: "Marta Villanueva",
    role: "Supply Planner",
    location: "Zaragoza",
    stage: "final",
    score: 91,
  },
  {
    id: "cand-004",
    name: "Javier Solis",
    role: "Last Mile Supervisor",
    location: "Monterrey",
    stage: "hired",
    score: 88,
  },
];

export default function CandidatesPageContent() {
  const [query, setQuery] = useState("");
  const [stageFilter, setStageFilter] = useState<"all" | CandidateStage>("all");

  const filteredCandidates = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return candidatesSeed.filter((candidate) => {
      if (stageFilter !== "all" && candidate.stage !== stageFilter) {
        return false;
      }

      if (!normalized) {
        return true;
      }

      return (
        candidate.name.toLowerCase().includes(normalized) ||
        candidate.role.toLowerCase().includes(normalized) ||
        candidate.location.toLowerCase().includes(normalized)
      );
    });
  }, [query, stageFilter]);

  return (
    <main>
      <header className="page-head card-reveal">
        <p className="kicker">Consolidated Module</p>
        <h2>Candidates</h2>
        <p className="muted">
          Version v1 sin datos reales. Consolida una vista pipeline local en espera de API definitiva.
        </p>
      </header>

      <section className="panel card-reveal">
        <h3>Pipeline mock</h3>

        <div className="filters-grid">
          <label>
            Search
            <input
              className="input"
              placeholder="Name, role, location"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>

          <label>
            Stage
            <select
              className="input"
              value={stageFilter}
              onChange={(event) => setStageFilter(event.target.value as "all" | CandidateStage)}
            >
              <option value="all">all</option>
              <option value="screening">screening</option>
              <option value="technical">technical</option>
              <option value="final">final</option>
              <option value="hired">hired</option>
            </select>
          </label>
        </div>

        {filteredCandidates.length === 0 ? (
          <p className="muted">No candidates found for current filters.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Location</th>
                  <th>Stage</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {filteredCandidates.map((candidate) => (
                  <tr key={candidate.id}>
                    <td>{candidate.name}</td>
                    <td>{candidate.role}</td>
                    <td>{candidate.location}</td>
                    <td>
                      <span className="pill pill-info">{candidate.stage}</span>
                    </td>
                    <td>{candidate.score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
