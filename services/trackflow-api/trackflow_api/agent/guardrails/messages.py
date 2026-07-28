from __future__ import annotations

REJECTION_INJECTION = (
    "No puedo modificar ni ignorar mis instrucciones de sistema. "
    "Soy el agente de CX de TrackFlow y solo puedo ayudarte con tracking de envíos, "
    "políticas de devolución/SLA por país (EE. UU. y España) e incidencias logísticas."
)

REJECTION_PERSONAL_USE = (
    "No puedo usarme como asistente personal para ensayos, tareas, código u otros temas "
    "ajenos a TrackFlow. Estoy aquí para soporte logístico: estado de envíos, devoluciones "
    "e incidencias. ¿En qué pedido o política de TrackFlow te ayudo?"
)

REJECTION_UNAUTHORIZED_TRACKING = (
    "No estoy autorizado a consultar ese pedido/tracking para la sesión autenticada actual. "
    "Por seguridad no puedo compartir información de envíos que no te pertenecen. "
    "Verifica que iniciaste sesión con la cuenta correcta o contacta a soporte CX de TrackFlow."
)

REDIRECT_OFF_TOPIC = (
    "Puedo responder de forma breve fuera de tema, pero mi función es el soporte CX de TrackFlow. "
    "Te reoriento: ¿necesitas el estado de un envío, una política de devolución "
    "(EE. UU. o España) o abrir/consultar una incidencia?"
)

REDIRECT_GENERAL_LOGISTICS = (
    "En logística, conceptos generales como la logística inversa describen el flujo de devoluciones "
    "y reacondicionamiento. En TrackFlow lo aplicamos con políticas distintas por país "
    "(EE. UU. vs España), etiquetas de devolución y gestión de incidencias. "
    "¿Quieres la política de devolución de un país concreto o el estado de un envío?"
)
