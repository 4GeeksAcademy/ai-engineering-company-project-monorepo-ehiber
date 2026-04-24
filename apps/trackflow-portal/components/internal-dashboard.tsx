import {
  countInterestedServices,
  countLeadRequestsByCountry,
  findLeadRequestByCompanyNameBinary,
  findLeadRequestByCompanyNameLinear,
  leadRequests,
  sortLeadRequestsByCompanyName,
  summarizeShipmentVolumes,
  validateLeadRequest,
} from "../../trackflow-coding-fundamentals/src/index";

const sortedLeadRequests = sortLeadRequestsByCompanyName(leadRequests);
const volumeSummary = summarizeShipmentVolumes(leadRequests);
const serviceTotals = countInterestedServices(leadRequests);
const countryTotals = countLeadRequestsByCountry(leadRequests);
const electroHubLinearIndex = findLeadRequestByCompanyNameLinear(leadRequests, "ElectroHub");
const electroHubBinaryIndex = findLeadRequestByCompanyNameBinary(sortedLeadRequests, "ElectroHub");
const freshBoxValidation = validateLeadRequest(leadRequests[3]);

export function InternalDashboard() {
  return (
    <div className="container" style={{ padding: "2.5rem 0 4rem" }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          gap: "1rem",
          alignItems: "end",
        }}
      >
        <div>
          <p className="eyebrow" style={{ color: "#67e8f9" }}>
            Internal App
          </p>
          <h1
            style={{
              margin: "0.8rem 0 0",
              color: "white",
              fontFamily: "var(--font-display)",
              fontSize: "clamp(2.2rem, 5vw, 4rem)",
              lineHeight: 1,
            }}
          >
            Lead intelligence workspace
          </h1>
          <p style={{ marginTop: "1rem", maxWidth: "44rem", color: "#cbd5e1", lineHeight: 1.8 }}>
            Esta vista usa el modulo TypeScript original de Milestone 2 para mostrar resultados
            directamente en pantalla. No hay copia de logica: las funciones vienen de
            `apps/trackflow-coding-fundamentals`.
          </p>
        </div>
      </div>

      <div className="stats-grid" style={{ marginTop: "2rem" }}>
        <div className="stat-chip">
          <div style={{ color: "#94a3b8" }}>Leads cargados</div>
          <div style={{ marginTop: "0.4rem", fontSize: "2rem", fontWeight: 800 }}>
            {leadRequests.length}
          </div>
        </div>
        <div className="stat-chip">
          <div style={{ color: "#94a3b8" }}>Promedio volumen</div>
          <div style={{ marginTop: "0.4rem", fontSize: "2rem", fontWeight: 800 }}>
            {volumeSummary.averageVolumeScore}
          </div>
        </div>
        <div className="stat-chip">
          <div style={{ color: "#94a3b8" }}>Rango de volumen</div>
          <div style={{ marginTop: "0.4rem", fontSize: "1.25rem", fontWeight: 800 }}>
            {volumeSummary.minimumVolume} - {volumeSummary.maximumVolume}
          </div>
        </div>
      </div>

      <div className="dashboard-grid" style={{ marginTop: "1.5rem" }}>
        <section className="internal-card" style={{ padding: "1.5rem" }}>
          <h2 style={{ margin: 0, fontFamily: "var(--font-display)", color: "white" }}>
            Resumen por pais
          </h2>
          <div className="public-grid" style={{ marginTop: "1rem" }}>
            {Object.entries(countryTotals).map(([country, total]) => (
              <div key={country} className="stat-chip">
                <div style={{ color: "#94a3b8" }}>{country}</div>
                <div style={{ marginTop: "0.35rem", fontSize: "1.5rem", fontWeight: 800 }}>
                  {total}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="internal-card" style={{ padding: "1.5rem" }}>
          <h2 style={{ margin: 0, fontFamily: "var(--font-display)", color: "white" }}>
            Servicios mas solicitados
          </h2>
          <div className="public-grid" style={{ marginTop: "1rem" }}>
            {Object.entries(serviceTotals).map(([service, total]) => (
              <div key={service} className="stat-chip">
                <div style={{ color: "#94a3b8" }}>{service}</div>
                <div style={{ marginTop: "0.35rem", fontSize: "1.5rem", fontWeight: 800 }}>
                  {total}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="dashboard-grid" style={{ marginTop: "1.5rem" }}>
        <section className="internal-card" style={{ padding: "1.5rem" }}>
          <h2 style={{ margin: 0, fontFamily: "var(--font-display)", color: "white" }}>
            Busqueda de ElectroHub
          </h2>
          <div className="public-grid" style={{ marginTop: "1rem" }}>
            <div className="stat-chip">
              <div style={{ color: "#94a3b8" }}>Indice lineal</div>
              <div style={{ marginTop: "0.35rem", fontSize: "1.5rem", fontWeight: 800 }}>
                {electroHubLinearIndex}
              </div>
            </div>
            <div className="stat-chip">
              <div style={{ color: "#94a3b8" }}>Indice binario</div>
              <div style={{ marginTop: "0.35rem", fontSize: "1.5rem", fontWeight: 800 }}>
                {electroHubBinaryIndex}
              </div>
            </div>
          </div>
        </section>

        <section className="internal-card" style={{ padding: "1.5rem" }}>
          <h2 style={{ margin: 0, fontFamily: "var(--font-display)", color: "white" }}>
            Validacion de FreshBox
          </h2>
          <div className="public-grid" style={{ marginTop: "1rem" }}>
            <div className="stat-chip">
              <div style={{ color: "#94a3b8" }}>Estado</div>
              <div style={{ marginTop: "0.35rem", fontSize: "1.5rem", fontWeight: 800 }}>
                {freshBoxValidation.isValid ? "Valido" : "Con alertas"}
              </div>
            </div>
            <div className="stat-chip">
              <div style={{ color: "#94a3b8" }}>Advertencia</div>
              <div style={{ marginTop: "0.35rem", lineHeight: 1.6 }}>
                {freshBoxValidation.warnings[0] ?? "Sin advertencias"}
              </div>
            </div>
          </div>
        </section>
      </div>

      <section className="internal-card" style={{ padding: "1.5rem", marginTop: "1.5rem" }}>
        <h2 style={{ margin: 0, fontFamily: "var(--font-display)", color: "white" }}>
          Leads ordenados por empresa
        </h2>
        <div style={{ overflowX: "auto", marginTop: "1rem" }}>
          <table>
            <thead>
              <tr>
                <th>Empresa</th>
                <th>Contacto</th>
                <th>Pais</th>
                <th>Producto</th>
                <th>Volumen</th>
                <th>Servicios</th>
              </tr>
            </thead>
            <tbody>
              {sortedLeadRequests.map((lead) => (
                <tr key={lead.companyName}>
                  <td>{lead.companyName}</td>
                  <td>{lead.contactPerson}</td>
                  <td>{lead.mainOperatingCountry}</td>
                  <td>{lead.productType}</td>
                  <td>{lead.estimatedMonthlyShipmentVolume}</td>
                  <td>{lead.interestedServices.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
