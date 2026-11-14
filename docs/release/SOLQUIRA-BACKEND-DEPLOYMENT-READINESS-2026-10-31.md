# Solquira — preparación de despliegue del backend con `certifi` corregido

Fecha: 2026-10-31  
Rama: `fix/certifi-20261019`  
Commits locales: `bd136e7` (lock) y `6dc9369` (tooling)  
Estado: **PREPARACIÓN COMPLETA — sin deploy, sin reinicio, sin inferencia**

## 1. Resumen

Se corrigieron las dos inconsistencias de tooling autorizadas, se ejecutó dos veces el staging oficial con resultados idénticos, se construyó y verificó una imagen final desde el contexto staged y se preparó el procedimiento de transferencia, despliegue y rollback. Producción no fue modificada.

## 2. Diff completo

### 2.1 Seguridad (`bd136e7`)

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

### 2.2 Tooling (`6dc9369`)

```diff
--- a/scripts/release_scan.py
+++ b/scripts/release_scan.py
@@
-ROOT_FILES = {"index.html", "favicon.svg", "robots.txt"}
+ROOT_FILES = {"index.html", "favicon.svg", "robots.txt", "solquira-rural-landscape.svg"}
```

```diff
--- a/scripts/check-studio-package.py
+++ b/scripts/check-studio-package.py
@@
-        shutil.copyfile(ROOT / "deploy/studio/Dockerfile", stage / "Dockerfile")
+        shutil.copyfile(ROOT / "deploy/studio/hosted.Dockerfile", stage / "Dockerfile")
```

No se modificaron frontend, Cesium, NASA, Devpost, YouTube ni configuración de producción.

### 2.3 Justificación del SVG

`solquira-rural-landscape.svg` **sí se usa**: `artifacts/solquira/src/studio/Studio.tsx:112` lo carga como imagen de portada. Se añadió solo ese nombre exacto a `ROOT_FILES`; no se usó wildcard ni se permitieron rutas arbitrarias. El asset mide 53,792 bytes y está presente en `public/` y `dist/public/`.

El cambio a `hosted.Dockerfile` corrige una referencia a un archivo inexistente (`deploy/studio/Dockerfile`). El Dockerfile real y ya usado por el staging oficial es `deploy/studio/hosted.Dockerfile`.

## 3. Staging oficial y reproducibilidad

Se ejecutó dos veces:

```text
output/hosted-release-certifi-20261019-r2
output/hosted-release-certifi-20261019-r3
```

Resultados:

| Elemento               | r2                                                                 | r3                    |
| ---------------------- | ------------------------------------------------------------------ | --------------------- |
| Archivos               | 391                                                                | 391                   |
| Estado                 | `STAGED_NOT_DEPLOYED`                                              | `STAGED_NOT_DEPLOYED` |
| Proveedor activado     | No                                                                 | No                    |
| Imagen verificada      | No (se verifica por separado)                                      | No                    |
| SHA-256 del manifiesto | `B43B0DBAF0C12A1017D24E70E3D39DC68981453665D165944E05D5E1E7825ED6` | mismo                 |
| Reproducible           | **Sí**                                                             | **Sí**                |

Verificaciones del contexto:

- `artifacts/solquira/dist/public/solquira-rural-landscape.svg` presente.
- `artifacts/solquira/backend/requirements.lock.txt` → `certifi==2026.10.19`.
- Sin archivos SQLite, `.db`, `.key`, `.pem`, `.p12`, `.pfx`, `.data`, `output`, `node_modules` ni `__pycache__`.
- El escaneo de secretos del stager pasó en ambas ejecuciones.
- El manifiesto no declara deploy ni activación de proveedor.

También se ejecutó el backend-only check:

```text
{"package_smoke": "pass", "provider": "disabled", "external_network": "blocked", "tools": 5}
{"runtime_files": 33, "frontend_included": false, "credentials_included": false}
```

## 4. Imagen final

Construida desde `output/hosted-release-certifi-20261019-r2/context` con `--no-cache`.

| Elemento                                                                | Valor                                                                     |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Tag                                                                     | `solquira-studio:certifi-20261019-final`                                  |
| Image ID                                                                | `sha256:a969dcf803f8c90830f6deff6745a7a0845a78ca1419aa655c95c45d537bd412` |
| Creada                                                                  | `2026-10-31T19:03:13Z`                                                    |
| Tamaño                                                                  | 57,151,950 bytes                                                          |
| Usuario                                                                 | `10001:10001`                                                             |
| CMD                                                                     | `python scripts/run-studio-hosted.py`                                     |
| Puerto expuesto                                                         | `8000/tcp`                                                                |
| Healthcheck                                                             | `GET /solquira-api/healthz`, 30 s, timeout 5 s, start 15 s, 3 retries     |
| `certifi` dentro                                                        | **2026.10.19**                                                            |
| `pip check`                                                             | **No broken requirements**                                                |
| TLS Token Factory sin credenciales                                      | **401** (handshake válido)                                                |
| TLS Open-Meteo                                                          | **200**                                                                   |
| Tests `test_studio_security` + `test_dryland_brief` dentro de la imagen | **41/41 PASS**                                                            |
| Variables de entorno de aplicación dentro de la imagen                  | **Ninguna**; solo claves base de Python                                   |
| Inferencia consumida                                                    | **0**; contador público 39/600                                            |

Evidencia: `output/certifi-remediation-20261031/docker-build-official.log`, `tests-final-image.log`, `tls-connectivity.log`, `pip-check.log`.

## 5. Comparación con el servicio actual

La configuración exacta del contenedor de producción debe leerse en el host con `docker inspect`; no se incluyen valores de secretos. La imagen nueva solo aporta `User`, `CMD`, `Healthcheck` y `ExposedPorts`; el resto del runtime debe conservarse.

| Requisito                   | Estado / acción                                                                                                                                                                                                                                                              |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Contenedor actual           | `solquira-quality-hour`                                                                                                                                                                                                                                                      |
| Imagen actual reportada     | `sha256:a9cb7b945f68b7c46b4f9ba084449b40f06bc636e3f9bfc23c7e7e02d6a658ac` (reportada en `output/deploy/cesium-mobile-review/PREVIEW_ORIGIN_APPROVAL_REQUEST.md`; **no verificada en vivo**)                                                                                  |
| Volumen persistente         | Preservar `/srv/solquira/data:/data`                                                                                                                                                                                                                                         |
| Presupuesto                 | Preservar `/data/studio-budget.sqlite3`; **no inicializar, reemplazar ni borrar**                                                                                                                                                                                            |
| Env file                    | Preservar `/srv/solquira/app.env` y todas las variables actuales                                                                                                                                                                                                             |
| Variables requeridas        | `SOLQUIRA_STUDIO_HOSTED`, `SOLQUIRA_STUDIO_PROVIDER`, `SOLQUIRA_STUDIO_ALLOWED_HOSTS`, `SOLQUIRA_STUDIO_TRUSTED_PROXY_IPS`, `SOLQUIRA_STUDIO_ALLOWED_ORIGINS`, `SOLQUIRA_STUDIO_GEODATA`, `SOLQUIRA_DATA_DIR`, `PORT`, `SOLQUIRA_BUDGET_*`, `NEBIUS_API_KEY` (solo servidor) |
| Red                         | Preservar el `NetworkMode` actual                                                                                                                                                                                                                                            |
| Puerto                      | Preservar binding actual `127.0.0.1:8000` (la imagen expone `8000/tcp`)                                                                                                                                                                                                      |
| Recursos                    | Preservar `Memory`, `NanoCpus`, `PidsLimit` actuales                                                                                                                                                                                                                         |
| Seguridad                   | Preservar `SecurityOpt`, `ReadonlyRootfs`, `CapAdd`, `CapDrop`, `Tmpfs` actuales                                                                                                                                                                                             |
| Restart / labels            | Preservar `RestartPolicy`, labels, `StopSignal`, `StopTimeout`                                                                                                                                                                                                               |
| Usuario / CMD / healthcheck | La imagen nueva ya usa `10001:10001`, el mismo CMD y healthcheck documentado                                                                                                                                                                                                 |
| Secretos en imagen          | No hay variables de aplicación ni claves dentro de la imagen                                                                                                                                                                                                                 |

La imagen nueva **no** debe arrancar sin el volumen y el env actuales: el presupuesto persistente y la configuración de proveedor son requisitos de `run-studio-hosted.py`.

## 6. Transferencia y verificación en el host (no ejecutada)

Opción preferida: transferir la imagen ya verificada.

```bash
# Workstation
docker save solquira-studio:certifi-20261019-final | gzip > solquira-certifi-20261019-final.tar.gz
sha256sum solquira-certifi-20261019-final.tar.gz > solquira-certifi-20261019-final.tar.gz.sha256
```

```bash
# Host, por canal SSH autorizado
sha256sum -c solquira-certifi-20261019-final.tar.gz.sha256
docker load -i solquira-certifi-20261019-final.tar.gz
docker image inspect solquira-studio:certifi-20261019-final --format '{{.Id}}'
# Debe coincidir con sha256:a969dcf8...d537bd412
docker run --rm --entrypoint python solquira-studio:certifi-20261019-final -c "import certifi; print(certifi.__version__)"
# Debe imprimir 2026.10.19
```

No se transfirió nada. Alternativa: reconstruir en el host desde `output/hosted-release-certifi-20261019-r2/context` y verificar `manifest.sha256.json` (`B43B0DBA…25ED6`), sin copiar el env ni el volumen.

## 7. Rollback corregido

El snippet manual antiguo era incorrecto: un contenedor detenido **conserva su nombre**, por lo que no se puede renombrar el contenedor previo al nombre de producción sin liberar primero ese nombre.

Secuencia correcta, alineada con `rollback_plan()` de `apply_preview_origin.py` (`stop-new`, `rename-failed`, `restore-prev`):

```bash
# Antes del swap: preservar imagen y contenedor actuales
docker inspect solquira-quality-hour --format '{{.Image}} {{.Config.Image}}'
docker image tag <current_image_id> solquira-studio:rollback-certifi-20261031
docker stop solquira-quality-hour
docker rename solquira-quality-hour solquira-quality-hour-prev

# Arrancar el reemplazo con el nombre de producción y la misma configuración
# ... docker run/create con la imagen nueva, env, volumen, red, puerto, recursos y healthcheck actuales

# Si falla la verificación:
docker stop solquira-quality-hour
docker rename solquira-quality-hour solquira-quality-hour-failed-<UTC>
docker rename solquira-quality-hour-prev solquira-quality-hour
docker start solquira-quality-hour
```

No se debe usar `docker rm -f`; el contenedor fallido y el previo se conservan detenidos para logs y evidencia. El volumen `/srv/solquira/data` no se toca. Los tests offline de `apply_preview_origin.py` pasan **30/30 + 5 subtests**, incluidos `RollbackPlanTests`.

## 8. Matriz de pruebas posteriores al despliegue

| Prueba                        | Comando / criterio                                                         | Esperado                                                                |
| ----------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Versión efectiva de `certifi` | `docker exec <new> python -c "import certifi;print(certifi.__version__)"`  | `2026.10.19`                                                            |
| Dependencias                  | `docker exec <new> python -m pip check`                                    | sin conflictos                                                          |
| TLS saliente                  | `httpx` a Token Factory sin auth / Open-Meteo desde el contenedor          | 401 TLS válido / 200                                                    |
| Health                        | `GET /solquira-api/healthz`                                                | 200                                                                     |
| Bootstrap                     | `GET /solquira-api/studio/bootstrap`                                       | 200; `inference.available`, provider/model, `calls_used=39`             |
| Cookies                       | `Set-Cookie` en bootstrap                                                  | `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`; sin imprimir valores |
| CSRF                          | POST sin `X-Solquira-CSRF`                                                 | 403                                                                     |
| Host/Origin                   | Host u Origin inválidos                                                    | 403                                                                     |
| Endpoints privados            | `/docs`, `/openapi.json`, `/api/v1/assistant/tools`                        | 404                                                                     |
| Superficie `/v1`              | `/v1/field-payload` y `/v1/field-brief` sin sesión                         | 401                                                                     |
| Open-Meteo                    | una petición controlada a `/studio/location` con sesión/CSRF               | `ready` o `cached`; sin modelo                                          |
| Fallback determinista         | `/studio/evaluate` o tests/smoke con provider disabled                     | determinista, sin `nebius_live`                                         |
| Presupuesto                   | lectura de `/data/studio-budget.sqlite3`: `PRAGMA quick_check`, contadores | `ok`; contadores y `calls_used` sin reset                               |
| CSP/source maps               | headers y `*.js.map`                                                       | CSP correcta; map 404                                                   |
| Nemotron                      | **no ejecutar** hasta autorización específica                              | 0 llamadas                                                              |

## 9. Riesgos residuales

- La imagen actual de producción (`a9cb…`) está reportada, no verificada en vivo. Confirmar el digest real en el host antes del swap.
- La transferencia de imagen no se ejecutó; la integridad depende de verificar el SHA-256 del archivo y el Image ID.
- El procedimiento de swap no se ejecutó en el host; el primer despliegue debe mantener el rollback preparado y el contenedor previo detenido.
- La imagen final incluye el frontend estático staged; no cambia el frontend servido por Vercel.
- El staging es reproducible, pero no se publicó en un registry.
- No se ejecutó una auditoría CVE completa de todas las dependencias Python; el hallazgo crítico de `certifi` está corregido y `pip check` pasa.
- `calls_used` sigue en 39/600; no se consumió inferencia.

## 10. Decisión solicitada

La preparación está completa. **No se desplegó, reinició, reemplazó contenedores, hizo push ni consumió Nemotron.** Queda pendiente la autorización específica de Fase 2 para transferir/desplegar el backend, verificar producción y luego ejecutar una única inferencia y capturar `04_evidencia_ia_live.mp4`.
