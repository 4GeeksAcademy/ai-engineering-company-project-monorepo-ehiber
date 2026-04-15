const form = document.querySelector("#application-form");

if (form) {
  const successBox = document.querySelector("#form-success");
  const warningBox = document.querySelector("#volume-warning");
  const clearButton = document.querySelector("#clear-form");
  const commentsField = document.querySelector("#comments");
  const counter = document.querySelector("#comments-counter");
  const serviceInputs = Array.from(document.querySelectorAll('input[name="services"]'));
  const current3plInputs = Array.from(document.querySelectorAll('input[name="current3pl"]'));
  const volumeField = document.querySelector("#monthlyVolume");
  const productTypeField = document.querySelector("#productType");

  const fieldMessages = {
    companyName: "El nombre de la empresa debe tener al menos 2 caracteres",
    contactPerson: "Ingresa nombre y apellido del contacto",
    companyEmail: "Ingresa un email corporativo valido (ejemplo: nombre@empresa.com)",
    phone: "El telefono debe incluir codigo de pais (ejemplo: +52 81 1234 5678)",
    website: "Si incluyes sitio web, debe ser una URL valida",
    operatingCountry: "Selecciona el pais de operacion principal",
    productType: "Selecciona el tipo de producto que manejas",
    monthlyVolume: "Selecciona el volumen mensual estimado",
    services: "Selecciona al menos un servicio de interes",
    current3pl: "Indica si actualmente trabajas con otro proveedor logistico",
    privacyPolicy: "Debes aceptar la politica de privacidad para continuar"
  };

  const fields = {
    companyName: document.querySelector("#companyName"),
    contactPerson: document.querySelector("#contactPerson"),
    companyEmail: document.querySelector("#companyEmail"),
    phone: document.querySelector("#phone"),
    website: document.querySelector("#website"),
    operatingCountry: document.querySelector("#operatingCountry"),
    productType: document.querySelector("#productType"),
    monthlyVolume: document.querySelector("#monthlyVolume"),
    comments: commentsField,
    privacyPolicy: document.querySelector("#privacyPolicy")
  };

  const showError = (name, message) => {
    const errorEl = document.querySelector(`#${name}-error`);
    const field = fields[name];

    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.remove("hidden");
    }

    if (field) {
      field.setAttribute("aria-invalid", "true");
      field.classList.remove("border-slate-300", "focus:border-teal-500", "focus:ring-teal-100");
      field.classList.add("border-rose-500", "focus:border-rose-500", "focus:ring-rose-100");
    }
  };

  const clearError = (name) => {
    const errorEl = document.querySelector(`#${name}-error`);
    const field = fields[name];

    if (errorEl) {
      errorEl.textContent = "";
      errorEl.classList.add("hidden");
    }

    if (field) {
      field.removeAttribute("aria-invalid");
      field.classList.remove("border-rose-500", "focus:border-rose-500", "focus:ring-rose-100");
      field.classList.add("border-slate-300", "focus:border-teal-500", "focus:ring-teal-100");
    }
  };

  const toggleGroupError = (name, hasError) => {
    const errorEl = document.querySelector(`#${name}-error`);
    if (!errorEl) return;
    if (hasError) {
      errorEl.classList.remove("hidden");
      errorEl.textContent = fieldMessages[name];
    } else {
      errorEl.classList.add("hidden");
      errorEl.textContent = "";
    }
  };

  const validateCompanyName = () => {
    const value = fields.companyName.value.trim();
    if (value.length < 2) {
      showError("companyName", fieldMessages.companyName);
      return false;
    }
    clearError("companyName");
    return true;
  };

  const validateContactPerson = () => {
    const value = fields.contactPerson.value.trim().replace(/\s+/g, " ");
    if (value.split(" ").filter(Boolean).length < 2) {
      showError("contactPerson", fieldMessages.contactPerson);
      return false;
    }
    clearError("contactPerson");
    return true;
  };

  const validateEmail = () => {
    const value = fields.companyEmail.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      showError("companyEmail", fieldMessages.companyEmail);
      return false;
    }
    clearError("companyEmail");
    return true;
  };

  const validatePhone = () => {
    const value = fields.phone.value.trim();
    const phoneRegex = /^\+\d{1,3}[\s\d().-]{6,}$/;
    if (!phoneRegex.test(value)) {
      showError("phone", fieldMessages.phone);
      return false;
    }
    clearError("phone");
    return true;
  };

  const validateWebsite = () => {
    const value = fields.website.value.trim();
    if (!value) {
      clearError("website");
      return true;
    }

    const websiteRegex = /^https?:\/\/[^\s/$.?#].[^\s]*$/i;
    if (!websiteRegex.test(value)) {
      showError("website", fieldMessages.website);
      return false;
    }
    clearError("website");
    return true;
  };

  const validateSelect = (name) => {
    if (!fields[name].value) {
      showError(name, fieldMessages[name]);
      return false;
    }
    clearError(name);
    return true;
  };

  const validateServices = () => {
    const isChecked = serviceInputs.some((input) => input.checked);
    toggleGroupError("services", !isChecked);
    return isChecked;
  };

  const validateCurrent3pl = () => {
    const isChecked = current3plInputs.some((input) => input.checked);
    toggleGroupError("current3pl", !isChecked);
    return isChecked;
  };

  const validateComments = () => {
    const value = fields.comments.value;
    const remaining = 500 - value.length;
    counter.textContent = `${remaining} caracteres disponibles`;

    if (remaining < 0) {
      const message = `Los comentarios no pueden exceder 500 caracteres (quedan ${remaining})`;
      const errorEl = document.querySelector("#comments-error");
      errorEl.textContent = message;
      errorEl.classList.remove("hidden");
      fields.comments.setAttribute("aria-invalid", "true");
      fields.comments.classList.remove("border-slate-300", "focus:border-teal-500", "focus:ring-teal-100");
      fields.comments.classList.add("border-rose-500", "focus:border-rose-500", "focus:ring-rose-100");
      return false;
    }

    const errorEl = document.querySelector("#comments-error");
    errorEl.textContent = "";
    errorEl.classList.add("hidden");
    fields.comments.removeAttribute("aria-invalid");
    fields.comments.classList.remove("border-rose-500", "focus:border-rose-500", "focus:ring-rose-100");
    fields.comments.classList.add("border-slate-300", "focus:border-teal-500", "focus:ring-teal-100");
    return true;
  };

  const validatePrivacy = () => {
    if (!fields.privacyPolicy.checked) {
      showError("privacyPolicy", fieldMessages.privacyPolicy);
      return false;
    }
    clearError("privacyPolicy");
    return true;
  };

  const updateVolumeWarning = () => {
    const lowVolume = volumeField.value === "0-100";
    const hasProductType = productTypeField.value !== "";

    if (lowVolume && hasProductType) {
      warningBox.textContent =
        "Para volumenes menores a 100 envios mensuales, nuestros servicios podrian no ser la solucion mas eficiente. Seguro que quieres continuar?";
      warningBox.classList.remove("hidden");
      return true;
    }

    warningBox.textContent = "";
    warningBox.classList.add("hidden");
    return false;
  };

  const validators = {
    companyName: validateCompanyName,
    contactPerson: validateContactPerson,
    companyEmail: validateEmail,
    phone: validatePhone,
    website: validateWebsite,
    operatingCountry: () => validateSelect("operatingCountry"),
    productType: () => validateSelect("productType"),
    monthlyVolume: () => validateSelect("monthlyVolume"),
    comments: validateComments,
    privacyPolicy: validatePrivacy
  };

  Object.entries(fields).forEach(([name, field]) => {
    if (!field || name === "comments" || name === "privacyPolicy") return;
    field.addEventListener("input", () => {
      validators[name]();
      if (name === "monthlyVolume" || name === "productType") updateVolumeWarning();
    });
    field.addEventListener("blur", validators[name]);
  });

  commentsField.addEventListener("input", validateComments);
  commentsField.addEventListener("blur", validateComments);
  fields.privacyPolicy.addEventListener("change", validatePrivacy);

  serviceInputs.forEach((input) => input.addEventListener("change", validateServices));
  current3plInputs.forEach((input) => input.addEventListener("change", validateCurrent3pl));
  volumeField.addEventListener("change", updateVolumeWarning);
  productTypeField.addEventListener("change", updateVolumeWarning);

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    successBox.classList.add("hidden");
    successBox.textContent = "";

    const results = [
      validateCompanyName(),
      validateContactPerson(),
      validateEmail(),
      validatePhone(),
      validateWebsite(),
      validateSelect("operatingCountry"),
      validateSelect("productType"),
      validateSelect("monthlyVolume"),
      validateServices(),
      validateCurrent3pl(),
      validateComments(),
      validatePrivacy()
    ];

    const shouldWarn = updateVolumeWarning();

    if (results.some((result) => !result)) {
      const firstError = form.querySelector('[aria-invalid="true"]');
      if (firstError && typeof firstError.focus === "function") firstError.focus();
      return;
    }

    if (shouldWarn) {
      const confirmed = window.confirm(
        "Para volumenes menores a 100 envios mensuales, nuestros servicios podrian no ser la solucion mas eficiente. Seguro que quieres continuar?"
      );
      if (!confirmed) return;
    }

    successBox.innerHTML =
      "<strong>Gracias por tu interes en TrackFlow.</strong><br>Hemos recibido tu solicitud. Nuestro equipo comercial revisara tu informacion y te contactara en las proximas 24-48 horas para agendar una llamada y conocer tus necesidades logisticas en detalle.<br><br>Si tienes alguna consulta urgente, escribenos directamente a comercial@trackflow.com";
    successBox.classList.remove("hidden");
    form.reset();
    updateVolumeWarning();
    validateComments();
    ["companyName","contactPerson","companyEmail","phone","website","operatingCountry","productType","monthlyVolume","privacyPolicy"].forEach(clearError);
    toggleGroupError("services", false);
    toggleGroupError("current3pl", false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  clearButton.addEventListener("click", () => {
    successBox.classList.add("hidden");
    successBox.textContent = "";
    warningBox.classList.add("hidden");
    warningBox.textContent = "";
    window.setTimeout(() => {
      ["companyName","contactPerson","companyEmail","phone","website","operatingCountry","productType","monthlyVolume","privacyPolicy"].forEach(clearError);
      toggleGroupError("services", false);
      toggleGroupError("current3pl", false);
      validateComments();
    }, 0);
  });

  validateComments();
}
