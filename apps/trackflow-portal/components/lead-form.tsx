"use client";

import { useMemo, useState } from "react";

type MainOperatingCountry = "Mexico" | "Espana" | "Ambos" | "Otro";
type ProductType = "Moda" | "Electronica" | "Cosmetica" | "Alimentacion" | "Otro";
type EstimatedMonthlyShipmentVolume =
  | "0-100"
  | "101-500"
  | "501-2000"
  | "2000+"
  | "No estoy seguro";
type InterestedService = "Almacenaje" | "Ultima milla" | "Logistica inversa";
type Current3plStatus = "Si" | "No" | "Estoy evaluando opciones";

type FormValues = {
  companyName: string;
  contactPerson: string;
  companyEmail: string;
  phone: string;
  website: string;
  operatingCountry: MainOperatingCountry | "";
  productType: ProductType | "";
  monthlyVolume: EstimatedMonthlyShipmentVolume | "";
  services: InterestedService[];
  current3pl: Current3plStatus | "";
  comments: string;
  privacyPolicy: boolean;
};

type FormErrors = Partial<Record<keyof FormValues | "services", string>>;

const initialValues: FormValues = {
  companyName: "",
  contactPerson: "",
  companyEmail: "",
  phone: "",
  website: "",
  operatingCountry: "",
  productType: "",
  monthlyVolume: "",
  services: [],
  current3pl: "",
  comments: "",
  privacyPolicy: false,
};

const successMessage = `Gracias por tu interes en TrackFlow.

Hemos recibido tu solicitud. Nuestro equipo comercial revisara tu informacion y te contactara en las proximas 24-48 horas para agendar una llamada y conocer tus necesidades logisticas en detalle.

Si tienes alguna consulta urgente, escribenos directamente a comercial@trackflow.com`;

const lowVolumeWarning =
  "Para volumenes menores a 100 envios mensuales, nuestros servicios podrian no ser la solucion mas eficiente. Seguro que quieres continuar?";

function validate(values: FormValues): FormErrors {
  const errors: FormErrors = {};

  if (values.companyName.trim().length < 2) {
    errors.companyName = "El nombre de la empresa debe tener al menos 2 caracteres";
  }

  if (values.contactPerson.trim().split(/\s+/).filter(Boolean).length < 2) {
    errors.contactPerson = "Ingresa nombre y apellido del contacto";
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.companyEmail.trim())) {
    errors.companyEmail =
      "Ingresa un email corporativo valido (ejemplo: nombre@empresa.com)";
  }

  if (!/^\+\d{1,3}[\s\d().-]{6,}$/.test(values.phone.trim())) {
    errors.phone = "El telefono debe incluir codigo de pais (ejemplo: +52 81 1234 5678)";
  }

  if (
    values.website.trim() &&
    !/^https?:\/\/[^\s/$.?#].[^\s]*$/i.test(values.website.trim())
  ) {
    errors.website = "Si incluyes sitio web, debe ser una URL valida";
  }

  if (!values.operatingCountry) {
    errors.operatingCountry = "Selecciona el pais de operacion principal";
  }

  if (!values.productType) {
    errors.productType = "Selecciona el tipo de producto que manejas";
  }

  if (!values.monthlyVolume) {
    errors.monthlyVolume = "Selecciona el volumen mensual estimado";
  }

  if (values.services.length === 0) {
    errors.services = "Selecciona al menos un servicio de interes";
  }

  if (!values.current3pl) {
    errors.current3pl = "Indica si actualmente trabajas con otro proveedor logistico";
  }

  if (values.comments.length > 500) {
    const remaining = 500 - values.comments.length;
    errors.comments = `Los comentarios no pueden exceder 500 caracteres (quedan ${remaining})`;
  }

  if (!values.privacyPolicy) {
    errors.privacyPolicy = "Debes aceptar la politica de privacidad para continuar";
  }

  return errors;
}

export function LeadForm() {
  const [values, setValues] = useState<FormValues>(initialValues);
  const [errors, setErrors] = useState<FormErrors>({});
  const [success, setSuccess] = useState("");

  const remainingCharacters = 500 - values.comments.length;
  const showVolumeWarning =
    values.monthlyVolume === "0-100" && values.productType !== "";

  const commentsLabel = useMemo(() => {
    if (remainingCharacters >= 0) {
      return `${remainingCharacters} caracteres disponibles`;
    }
    return `Has excedido el limite por ${Math.abs(remainingCharacters)} caracteres`;
  }, [remainingCharacters]);

  function updateField<K extends keyof FormValues>(field: K, nextValue: FormValues[K]) {
    setValues((currentValues) => ({ ...currentValues, [field]: nextValue }));
  }

  function toggleService(service: InterestedService) {
    setValues((currentValues) => {
      const alreadySelected = currentValues.services.includes(service);
      return {
        ...currentValues,
        services: alreadySelected
          ? currentValues.services.filter((currentService) => currentService !== service)
          : [...currentValues.services, service],
      };
    });
  }

  function clearForm() {
    setValues(initialValues);
    setErrors({});
    setSuccess("");
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validate(values);
    setErrors(nextErrors);
    setSuccess("");

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    if (showVolumeWarning && !window.confirm(lowVolumeWarning)) {
      return;
    }

    setSuccess(successMessage);
    setValues(initialValues);
  }

  return (
    <form onSubmit={handleSubmit} noValidate style={{ marginTop: "2rem" }}>
      {success ? (
        <div className="notice notice-success" style={{ whiteSpace: "pre-line", marginBottom: "1rem" }}>
          {success}
        </div>
      ) : null}

      {showVolumeWarning ? (
        <div className="notice notice-warning" style={{ marginBottom: "1rem" }}>
          {lowVolumeWarning}
        </div>
      ) : null}

      <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
        <legend style={{ fontWeight: 800, fontSize: "1.1rem", color: "#0f172a", marginBottom: "1rem" }}>
          Datos de empresa
        </legend>
        <div className="field-grid">
          <div className="full-span">
            <label className="field-label" htmlFor="companyName">
              Nombre de la empresa *
            </label>
            <input
              id="companyName"
              className="field-input"
              value={values.companyName}
              onChange={(event) => updateField("companyName", event.target.value)}
            />
            {errors.companyName ? <p className="field-error">{errors.companyName}</p> : null}
          </div>

          <div>
            <label className="field-label" htmlFor="contactPerson">
              Persona de contacto *
            </label>
            <input
              id="contactPerson"
              className="field-input"
              value={values.contactPerson}
              onChange={(event) => updateField("contactPerson", event.target.value)}
            />
            {errors.contactPerson ? <p className="field-error">{errors.contactPerson}</p> : null}
          </div>

          <div>
            <label className="field-label" htmlFor="companyEmail">
              Email corporativo *
            </label>
            <input
              id="companyEmail"
              type="email"
              className="field-input"
              value={values.companyEmail}
              onChange={(event) => updateField("companyEmail", event.target.value)}
            />
            {errors.companyEmail ? <p className="field-error">{errors.companyEmail}</p> : null}
          </div>

          <div>
            <label className="field-label" htmlFor="phone">
              Telefono *
            </label>
            <input
              id="phone"
              className="field-input"
              placeholder="+52 81 1234 5678"
              value={values.phone}
              onChange={(event) => updateField("phone", event.target.value)}
            />
            {errors.phone ? <p className="field-error">{errors.phone}</p> : null}
          </div>

          <div>
            <label className="field-label" htmlFor="website">
              Sitio web de la empresa
            </label>
            <input
              id="website"
              className="field-input"
              placeholder="https://tuempresa.com"
              value={values.website}
              onChange={(event) => updateField("website", event.target.value)}
            />
            {errors.website ? <p className="field-error">{errors.website}</p> : null}
          </div>

          <div>
            <label className="field-label" htmlFor="operatingCountry">
              Pais de operacion principal *
            </label>
            <select
              id="operatingCountry"
              className="field-select"
              value={values.operatingCountry}
              onChange={(event) =>
                updateField("operatingCountry", event.target.value as FormValues["operatingCountry"])
              }
            >
              <option value="">Selecciona una opcion</option>
              <option value="Mexico">Mexico</option>
              <option value="Espana">Espana</option>
              <option value="Ambos">Ambos</option>
              <option value="Otro">Otro</option>
            </select>
            {errors.operatingCountry ? <p className="field-error">{errors.operatingCountry}</p> : null}
          </div>

          <div>
            <label className="field-label" htmlFor="productType">
              Tipo de producto *
            </label>
            <select
              id="productType"
              className="field-select"
              value={values.productType}
              onChange={(event) =>
                updateField("productType", event.target.value as FormValues["productType"])
              }
            >
              <option value="">Selecciona una opcion</option>
              <option value="Moda">Moda</option>
              <option value="Electronica">Electronica</option>
              <option value="Cosmetica">Cosmetica</option>
              <option value="Alimentacion">Alimentacion</option>
              <option value="Otro">Otro</option>
            </select>
            {errors.productType ? <p className="field-error">{errors.productType}</p> : null}
          </div>

          <div>
            <label className="field-label" htmlFor="monthlyVolume">
              Volumen mensual estimado de envios *
            </label>
            <select
              id="monthlyVolume"
              className="field-select"
              value={values.monthlyVolume}
              onChange={(event) =>
                updateField("monthlyVolume", event.target.value as FormValues["monthlyVolume"])
              }
            >
              <option value="">Selecciona una opcion</option>
              <option value="0-100">0-100</option>
              <option value="101-500">101-500</option>
              <option value="501-2000">501-2000</option>
              <option value="2000+">2000+</option>
              <option value="No estoy seguro">No estoy seguro</option>
            </select>
            {errors.monthlyVolume ? <p className="field-error">{errors.monthlyVolume}</p> : null}
          </div>
        </div>
      </fieldset>

      <fieldset style={{ border: 0, padding: 0, margin: "2rem 0 0" }}>
        <legend style={{ fontWeight: 800, fontSize: "1.1rem", color: "#0f172a" }}>
          Servicios de interes *
        </legend>
        <div className="choice-grid" style={{ marginTop: "1rem" }}>
          {(["Almacenaje", "Ultima milla", "Logistica inversa"] as InterestedService[]).map(
            (service) => (
              <label key={service} className="choice-card">
                <input
                  type="checkbox"
                  checked={values.services.includes(service)}
                  onChange={() => toggleService(service)}
                />
                <span>{service}</span>
              </label>
            ),
          )}
        </div>
        {errors.services ? <p className="field-error">{errors.services}</p> : null}
      </fieldset>

      <fieldset style={{ border: 0, padding: 0, margin: "2rem 0 0" }}>
        <legend style={{ fontWeight: 800, fontSize: "1.1rem", color: "#0f172a" }}>
          Actualmente trabajas con otro 3PL? *
        </legend>
        <div className="choice-grid" style={{ marginTop: "1rem" }}>
          {(["Si", "No", "Estoy evaluando opciones"] as Current3plStatus[]).map((status) => (
            <label key={status} className="choice-card">
              <input
                type="radio"
                name="current3pl"
                checked={values.current3pl === status}
                onChange={() => updateField("current3pl", status)}
              />
              <span>{status}</span>
            </label>
          ))}
        </div>
        {errors.current3pl ? <p className="field-error">{errors.current3pl}</p> : null}
      </fieldset>

      <fieldset style={{ border: 0, padding: 0, margin: "2rem 0 0" }}>
        <legend style={{ fontWeight: 800, fontSize: "1.1rem", color: "#0f172a" }}>
          Contexto adicional
        </legend>
        <label className="field-label" htmlFor="comments" style={{ marginTop: "1rem" }}>
          Comentarios o necesidades especificas
        </label>
        <textarea
          id="comments"
          rows={5}
          className="field-textarea"
          value={values.comments}
          onChange={(event) => updateField("comments", event.target.value)}
        />
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            gap: "0.75rem",
            marginTop: "0.5rem",
            color: "#64748b",
          }}
        >
          <span>{commentsLabel}</span>
          {errors.comments ? <span className="field-error" style={{ marginTop: 0 }}>{errors.comments}</span> : null}
        </div>
      </fieldset>

      <fieldset style={{ border: 0, padding: 0, margin: "2rem 0 0" }}>
        <label className="choice-card" style={{ maxWidth: "40rem" }}>
          <input
            type="checkbox"
            checked={values.privacyPolicy}
            onChange={(event) => updateField("privacyPolicy", event.target.checked)}
          />
          <span>Acepto politica de privacidad *</span>
        </label>
        {errors.privacyPolicy ? <p className="field-error">{errors.privacyPolicy}</p> : null}
      </fieldset>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.8rem", marginTop: "2rem" }}>
        <button type="submit" className="button-primary">
          Enviar solicitud
        </button>
        <button
          type="button"
          className="button-secondary"
          style={{ color: "#334155", borderColor: "#cbd5e1" }}
          onClick={clearForm}
        >
          Limpiar formulario
        </button>
      </div>
    </form>
  );
}
