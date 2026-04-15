# CONTEXT.md - TrackFlow

## Hito 1: Sitio Web Publico de tu Empresa

_These instructions are available in English in the syllabus repository._

> Este documento describe tu empresa y la situacion concreta para la que estas construyendo este hito. Leelo completo antes de escribir codigo. Todo lo que construyas debe reflejar este contexto.

---

## Tu empresa

**TrackFlow** es una empresa de gestion de almacenes y entregas de ultima milla fundada en 2009 en Monterrey, Mexico. Opera en dos mercados - Mexico y Espana (Zaragoza) - y ofrece tres servicios: gestion de almacenes para marcas de e-commerce, entregas de ultima milla y logistica inversa para devoluciones y reacondicionamiento de productos. Tiene aproximadamente 130 empleados y genera alrededor de 9 millones de euros en facturacion anual. Sus clientes son marcas medianas de moda, electronica y cosmetica que venden en linea.

---

## Tu departamento y el problema que debes resolver

Trabajas en la unidad **TrackFlow Tech**, reportando directamente al CTO Andres Kim. El sitio web corporativo actual de TrackFlow fue construido hace anos por una agencia externa y esta completamente desactualizado. No refleja que la empresa opera en dos paises, no explica claramente los servicios, y no hay forma de que empresas interesadas soliciten informacion de manera estructurada. Miguel Torres, Director Comercial, necesita un sitio web profesional que presente los servicios de TrackFlow y capture leads de empresas potenciales que quieran externalizar su logistica.

---

## Tu stakeholder

**Miguel Torres, Director Comercial**

> Necesitamos un nuevo sitio web que presente TrackFlow como lo que somos: un operador logistico serio con presencia en Mexico y Espana. Debe explicar nuestros tres servicios principales: gestion de almacenes, ultima milla y logistica inversa. Tambien necesito una pagina con un formulario para que empresas interesadas puedan solicitar informacion. Actualmente nos llegan consultas muy vagas por email y perdemos mucho tiempo calificando si son clientes reales o no. Quiero capturar: datos de la empresa, tipo de producto que manejan, volumen mensual estimado de envios, paises donde operan, y que servicios les interesan. El sitio debe ser responsive, accesible, y optimizado para SEO. Usa Tailwind y asegurate de que el formulario tenga validacion completa.

---

## Contenido de la landing page

### Header

- Logo o nombre "TrackFlow"
- Navegacion: Inicio | Servicios | Cobertura | Contacto

### Hero

- Titular: "Logistica que escala con tu e-commerce"
- Subtitulo: "Gestion de almacenes, entregas de ultima milla y logistica inversa en Mexico y Espana. Mas de 15 anos ayudando a marcas de moda, electronica y cosmetica a crecer sin preocuparse por la operacion."
- Call to action: Boton "Solicitar informacion" que enlace al formulario

### Servicios

1. **Gestion de Almacenes**
   - Almacenamiento, picking y packing
   - Inventario en tiempo real
   - Operamos almacenes en Monterrey y Zaragoza

2. **Entregas de Ultima Milla**
   - Red de carriers certificados en ambos paises
   - Seguimiento unificado de envios
   - Gestion de incidencias y devoluciones

3. **Logistica Inversa**
   - Gestion completa de devoluciones
   - Inspeccion y reacondicionamiento
   - Integracion con tu plataforma de ventas

### Cobertura

- **Mexico**
  - Almacen en Monterrey
  - Cobertura nacional
  - Carriers: Estafeta, FedEx, DHL

- **Espana**
  - Almacen en Zaragoza
  - Cobertura peninsular e islas
  - Carriers: MRW, SEUR, DHL

### Por que TrackFlow

- Operacion binacional: El unico operador con infraestructura propia en Mexico y Espana
- +130 profesionales dedicados a tu logistica
- Tecnologia propia para visibilidad total de tu inventario
- Especializacion e-commerce en moda, electronica y cosmetica

### Contacto

- Email: comercial@trackflow.com
- Monterrey: +52 81 1234 5678
- Zaragoza: +34 976 123 456

### Footer

- (c) 2025 TrackFlow. Todos los derechos reservados.
- LinkedIn

---

## Campos del formulario de solicitud de informacion

- Nombre de la empresa: texto, minimo 2 caracteres, obligatorio
- Persona de contacto: texto, minimo 2 palabras, obligatorio
- Email corporativo: email valido, obligatorio
- Telefono: formato +[codigo pais] [numero], obligatorio
- Sitio web de la empresa: URL valida si se completa, opcional
- Pais de operacion principal: Mexico / Espana / Ambos / Otro, obligatorio
- Tipo de producto: Moda / Electronica / Cosmetica / Alimentacion / Otro, obligatorio
- Volumen mensual estimado de envios: 0-100 / 101-500 / 501-2000 / 2000+ / No estoy seguro, obligatorio
- Servicios de interes: Almacenaje / Ultima milla / Logistica inversa, multiple y obligatorio
- Actualmente trabajas con otro 3PL?: Si / No / Estoy evaluando opciones, obligatorio
- Comentarios o necesidades especificas: maximo 500 caracteres, opcional
- Acepto politica de privacidad: obligatorio

---

## Validaciones especificas

1. Nombre de empresa: minimo 2 caracteres
2. Persona de contacto: debe contener al menos nombre y apellido
3. Email: formato valido con @ y dominio
4. Telefono: debe comenzar con +
5. Sitio web: si se proporciona, debe comenzar con http:// o https://
6. Servicios de interes: al menos uno seleccionado
7. Comentarios: maximo 500 caracteres con contador visible
8. Politica de privacidad: debe estar marcada para enviar

---

## Mensajes de error esperados

- Nombre de empresa: "El nombre de la empresa debe tener al menos 2 caracteres"
- Persona de contacto: "Ingresa nombre y apellido del contacto"
- Email: "Ingresa un email corporativo valido (ejemplo: nombre@empresa.com)"
- Telefono: "El telefono debe incluir codigo de pais (ejemplo: +52 81 1234 5678)"
- Sitio web: "Si incluyes sitio web, debe ser una URL valida"
- Pais: "Selecciona el pais de operacion principal"
- Tipo de producto: "Selecciona el tipo de producto que manejas"
- Volumen mensual: "Selecciona el volumen mensual estimado"
- Servicios de interes: "Selecciona al menos un servicio de interes"
- 3PL actual: "Indica si actualmente trabajas con otro proveedor logistico"
- Comentarios: "Los comentarios no pueden exceder 500 caracteres (quedan X)"
- Politica de privacidad: "Debes aceptar la politica de privacidad para continuar"

---

## Mensaje de exito

> Gracias por tu interes en TrackFlow.
>
> Hemos recibido tu solicitud. Nuestro equipo comercial revisara tu informacion y te contactara en las proximas 24-48 horas para agendar una llamada y conocer tus necesidades logisticas en detalle.
>
> Si tienes alguna consulta urgente, escribenos directamente a comercial@trackflow.com

---

## Restriccion especifica

El formulario esta disenado para empresas de e-commerce que buscan externalizar su logistica, no para consumidores finales que quieren rastrear un paquete o hacer una devolucion. Si detectas que el volumen seleccionado es "0-100 envios/mes", incluye el siguiente mensaje de advertencia:

"Para volumenes menores a 100 envios mensuales, nuestros servicios podrian no ser la solucion mas eficiente. Seguro que quieres continuar?"

---

## Schema.org markup requerido

Usa un objeto `Organization` con:

- `name`: TrackFlow
- `description`: Gestion de almacenes y entregas de ultima milla para e-commerce
- `url`: https://trackflow.com
- `foundingDate`: 2009
- `address`: Monterrey, MX y Zaragoza, ES
- `contactPoint`: telefono +52-81-1234-5678, tipo sales, idiomas Spanish y English
- `sameAs`: https://linkedin.com/company/trackflow
- `areaServed`: Mexico y Spain
