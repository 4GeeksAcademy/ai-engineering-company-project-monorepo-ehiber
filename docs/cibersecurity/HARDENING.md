# Endurecimiento de runtime — TrackFlow

Documento de evidencia para la rúbrica OWASP (servidor / red) y NIST Protect. El runtime real de este fork es **Docker Compose**, no un VPS. Las plantillas SSH/firewall para un host futuro están en [`infra/hardening/`](../../infra/hardening/).

Informes: [NIST_REPORT.md](./NIST_REPORT.md) · [OWASP_TOP10_AUDIT.md](./OWASP_TOP10_AUDIT.md) · CONTEXT [audit.md](./audit.md)

## Usuario no-root

| Imagen | Usuario | Evidencia |
| --- | --- | --- |
| `services/trackflow-api` (API, Celery, Flower) | `app` uid 1000 | `USER app` en `services/trackflow-api/Dockerfile` |
| `mcps/trackflow-mcp` | `app` uid 1000 | `USER app` en `mcps/trackflow-mcp/Dockerfile` |
| `uis/backoffice` | `node` | `USER node` en `uis/backoffice/Dockerfile` |
| `uis/trackflow-portal` | `node` | `USER node` en `uis/trackflow-portal/Dockerfile` |

### Excepciones (documentadas, no críticas de este ciclo)

- `scripts/Dockerfile.nightly-telemetry` corre `cron -f` como root.
- `data/pipelines/telemetry-kpi-daily/Dockerfile` monta `/var/run/docker.sock` (Prefect worker). Residual A05: un compromiso del pipeline implica control del daemon Docker.

En un host, el operador diario es `deploy` (no root). Snippet: [`infra/hardening/sshd/sshd_config.d-trackflow.conf`](../../infra/hardening/sshd/sshd_config.d-trackflow.conf) (`PermitRootLogin no`, `AllowUsers deploy`).

## Superficie de red (Compose)

Público (cualquier interfaz, detrás de TLS en producción):

- API `8000`
- Portal `3001`
- Backoffice `3002`

Solo loopback (`127.0.0.1`), no LAN/internet:

| Servicio | Puerto | `docker-compose.yml` |
| --- | --- | --- |
| Redis | 6379 | `127.0.0.1:6379:6379` |
| Qdrant HTTP | 6333 | `127.0.0.1:6333:6333` |
| Qdrant gRPC | 6334 | `127.0.0.1:6334:6334` |
| MCP | 8002 | `127.0.0.1:8002:8002` |
| Flower | 5555 | `127.0.0.1:5555:5555` |

La API habla con MCP y Redis por la red interna de Compose (`trackflow-mcp:8002`, `redis:6379`), no hace falta publicar esos puertos al host salvo debug local.

Comando de evidencia:

```bash
docker compose config | grep -A2 "ports:"
```

Firewall de host (plantilla, no aplicada aquí): [`infra/hardening/ufw/trackflow.rules.sh`](../../infra/hardening/ufw/trackflow.rules.sh) — deny incoming, allow 22/80/443.

## Permisos de carpetas

Plantilla host: [`infra/hardening/permissions/layout.md`](../../infra/hardening/permissions/layout.md). Secretos solo en env / `/etc/trackflow/.env` modo `0640`. El checkout de código no debe contener `LITELLM_API_KEY`, JWT ni secretos de carriers.

## SSH (baseline para sign-off)

No hay VM de producción en este fork. El criterio de la rúbrica se cumple así:

1. Compose no usa `user: "0:0"`.
2. Las imágenes de aplicación declaran `USER` no-root.
3. El snippet sshd deshabilita root login y restringe a `deploy`.

## Antes / después (puertos)

**Antes:** Redis, Qdrant, MCP y Flower se publicaban como `6379:6379` (todas las interfaces).

**Después:** bind `127.0.0.1`. Un escaneo desde otra máquina de la LAN no debe ver 6379/6333/8002/5555.
