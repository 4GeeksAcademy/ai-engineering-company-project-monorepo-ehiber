# Folder permissions (host)

Create a dedicated non-root operator (`deploy`) and keep secrets out of the application tree.

```text
/opt/trackflow/app      deploy:deploy  0750   application checkout
/var/log/trackflow      deploy:deploy  0750   logs (not world-readable)
/etc/trackflow          root:deploy    0750   env files / TLS material
/etc/trackflow/.env     root:deploy    0640   secrets; never committed
```

Do not store `LITELLM_API_KEY`, `MCP_AUTH_JWT_SECRET`, `TRACKFLOW_JWT_SECRET_KEY`, or carrier/webhook secrets under `/opt/trackflow/app`.
