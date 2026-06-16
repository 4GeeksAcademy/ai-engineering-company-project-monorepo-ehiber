# TrackFlow Backoffice

Aplicacion Next.js dedicada para operaciones internas bajo rutas `/backoffice/*`.

## Rutas principales

- `/backoffice/login`
- `/backoffice/inventory/products`
- `/backoffice/inventory/orders/inbound`
- `/backoffice/inventory/orders/outbound`
- `/backoffice/inventory/orders`
- `/backoffice/suppliers`
- `/backoffice/incidents`
- `/backoffice/candidates`

## Ejecutar

```bash
npm install
npm run dev
npm run typecheck
npm run lint
```

## Variables de entorno

Copiar `.env.example` a `.env.local` y ajustar:

- `NEXT_PUBLIC_TRACKFLOW_API_URL`
