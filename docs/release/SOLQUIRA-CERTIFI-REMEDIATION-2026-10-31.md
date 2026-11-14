# Solquira — remediación acotada de `certifi` (Fase 1)

Fecha: 2026-10-31  
Rama: `fix/certifi-20261019` (creada desde `main` `4e1e456`)  
Estado: **FASE 1 COMPLETA — sin deploy, sin reinicio, sin inferencia**

## 1. Alcance y diff

Se modificó únicamente una línea del lockfile del backend:

```diff
--- a/artifacts/solquira/backend/requirements.lock.txt
+++ b/artifacts/solquira/backend/requirements.lock.txt
@@ -1,7 +1,7 @@
 annotated-doc==0.0.5
 annotated-types==0.8.0
 anyio==4.15.1
-certifi==2026.7.22
+certifi==2026.10.19
 click==8.5.0
 fastapi==0.143.0
 h11==0.16.0
```

No se modificaron frontend, Cesium, NASA, Devpost, YouTube, scripts de staging, Dockerfile ni configuración de producción. `main` sigue en `4e1e456`.

### Selección de versión

- `certifi==2026.10.19` existe en PyPI (publicado 2026-10-20), requiere Python >=3.7 y no tiene dependencias.
- OSV no reporta vulnerabilidades para `2026.10.19`.
- Corrige `GHSA-6q48-6c7w-9gw2` / `PYSEC-2026-4320` (CWE-295), corregido desde `2026.10.18`.
- Se eligió `2026.10.19` por ser la versión indicada por el owner y estar dentro del rango corregido. `2026.10.23` también existe, pero no se usó para mantener el cambio mínimo solicitado.

## 2. Contexto de build y hallazgos de staging

El camino oficial completo **no pudo ejecutarse sin modificar tooling no autorizado**:

1. `scripts/stage-hosted-release.py` rechazó el build por un asset estático preexistente no incluido en su allowlist: `solquira-rural-landscape.svg`. No es un efecto del cambio de `certifi`.
2. `scripts/check-studio-package.py --build` referencia `deploy/studio/Dockerfile`, pero el repositorio solo tiene `deploy/studio/hosted.Dockerfile`. Es una referencia stale preexistente.

Para no modificar scripts ni allowlists, se construyó un **contexto backend-only temporal** usando exactamente:

- `check-studio-package.source_files()` como allowlist de fuentes.
- `check-studio-package.stage_source()` para copiar.
- `deploy/studio/hosted.Dockerfile` como Dockerfile.
- `scripts/run-studio-hosted.py`, que el staging oficial también añade.

Resultado del contexto:

- **35 archivos**.
- `requirements.lock.txt` con `certifi==2026.10.19`.
- **0 rutas prohibidas**: sin `.data`, `.env`, SQLite, `.key`, `.pem`, `output`, `node_modules` ni `__pycache__`.
- Manifiesto con SHA-256: `output/certifi-remediation-20261031/context-manifest.json`.

Esto es un **backend-only build**; no es el manifiesto completo de release frontend. Antes de un despliegue staged completo conviene corregir las dos referencias stale en una tarea separada y autorizada.

## 3. Imagen preparada

| Elemento    | Valor                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------ |
| Tag local   | `solquira-studio:certifi-20261019`                                                         |
| Image ID    | `sha256:b522ed8d7b703d429f2a13fff95d4e05bb4f96af70fb5bd9b54ca338c338b5c6`                  |
| Creada      | `2026-10-31T18:50:15Z`                                                                     |
| Tamaño      | 51,787,391 bytes                                                                           |
| Base        | `python:3.12-slim@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f` |
| Usuario     | `10001:10001`                                                                              |
| CMD         | `python scripts/run-studio-hosted.py`                                                      |
| Healthcheck | `GET /solquira-api/healthz` cada 30 s, timeout 5 s, start 15 s, 3 retries                  |

Build ejecutado con `--no-cache` para garantizar que la capa de `pip install` no reutilizara el `certifi` anterior. Log: `output/certifi-remediation-20261031/docker-build.log`. Inspección: `image-inspect.json`.

## 4. Verificación dentro del contenedor

| Prueba                                                                      | Resultado                                                    |
| --------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `certifi.__version__` dentro de la imagen                                   | **2026.10.19**                                               |
| Bundle CA usado                                                             | `/usr/local/lib/python3.12/site-packages/certifi/cacert.pem` |
| `pip check`                                                                 | **No broken requirements found**                             |
| Búsqueda de `.env`, SQLite, `.db`, `.key`, `.pem`, `.p12`, `.pfx` en `/app` | **Ninguno**                                                  |
| TLS a `api.tokenfactory.nebius.com` sin credenciales                        | **HTTP 401**, handshake TLS válido (401 esperado sin auth)   |
| TLS a `api.open-meteo.com`                                                  | **HTTP 200**                                                 |
| Tests `test_studio_security` + `test_dryland_brief` dentro de la imagen     | **41/41 PASS** (0.983 s)                                     |
| Inferencia consumida                                                        | **0**; contador público sigue en **39/600**                  |

Logs: `output/certifi-remediation-20261031/pip-check.log`, `tls-connectivity.log`, `tests.log`.

## 5. Imagen actualmente desplegada y rollback

La imagen de producción **no se inspeccionó en vivo** porque no se autorizó acceso al host y el daemon local no la contiene. El artefacto de despliegue `output/deploy/cesium-mobile-review/PREVIEW_ORIGIN_APPROVAL_REQUEST.md` reporta:

- Contenedor: `solquira-quality-hour`.
- Imagen candidata/actual reportada: `sha256:a9cb7b945f68b7c46b4f9ba084449b40f06bc636e3f9bfc23c7e7e02d6a658ac`.
- El helper `apply_preview_origin.py --check` imprime el digest vivo y puede exigir `--expect-image`.

Antes de desplegar, el operador debe confirmar en el host:

```bash
docker inspect solquira-quality-hour --format '{{.Image}} {{.Config.Image}}'
docker image tag <current_image_id> solquira-studio:rollback-certifi-20261031
```

El rollback probado en el artefacto es conservar el contenedor anterior detenido, nunca borrarlo, y volver con:

```bash
docker stop solquira-quality-hour
docker rename solquira-quality-hour-origin-prev solquira-quality-hour
docker start solquira-quality-hour
```

No se ejecutó ningún comando de despliegue, stop, rename, start ni restart.

## 6. Procedimiento de despliegue preparado (no ejecutado)

1. Confirmar en el host el digest actual y crear el tag de rollback.
2. Transferir/cargar `solquira-studio:certifi-20261019` o reconstruirla desde el contexto staged seguro.
3. Verificar en la nueva imagen `certifi==2026.10.19`, `pip check` y TLS.
4. Crear el contenedor de reemplazo con la misma configuración, variables, volumen `/data`, puerto, healthcheck y restart policy del contenedor actual.
5. Detener y renombrar el contenedor actual; arrancar el reemplazo.
6. Verificar `/solquira-api/healthz`, `/solquira-api/studio/bootstrap`, CSRF/cookies y una ejecución determinista sin modelo.
7. Si falla, ejecutar el rollback anterior.
8. Solo después de aprobación explícita: una llamada real a Nemotron y captura de `04_evidencia_ia_live.mp4`.

## 7. Limitaciones

- No se generó el manifiesto staged completo por las dos referencias stale del tooling; se usó el contexto backend-only con la allowlist de fuentes.
- No se verificó el `certifi` del contenedor de producción en vivo; eso queda para la Fase 2, después del deploy autorizado.
- No se desplegó, reinició, fusionó ni hizo push.
- No se ejecutó Nemotron ni se generó el video live.
- La imagen nueva es local; no está publicada en un registry.

## 8. Decisión solicitada

Fase 1 está lista para revisión. No se debe desplegar hasta que el owner apruebe la Fase 2. Si se quiere un release staged completo, primero hay que autorizar la corrección de las dos referencias stale del tooling (`solquira-rural-landscape.svg` en la allowlist y `deploy/studio/Dockerfile` en el backend-only check).
