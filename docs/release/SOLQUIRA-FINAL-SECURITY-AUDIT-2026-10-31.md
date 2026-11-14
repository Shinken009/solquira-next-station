# Solquira — auditoría final de seguridad, privacidad e integridad de entrega

Fecha: 2026-10-31  
Alcance: repositorio `C:\Users\rober\PROYECTOS\Qanema`, rama `main`, producción `https://solquira.vercel.app`, backend `https://api-solquira.r4logic.lat` y entrega Devpost.  
Modo: solo lectura. No se modificó código, configuración, Git, Vercel, OpenCode, MCP ni credenciales. Este informe es el único archivo creado.

## 1. Resumen ejecutivo y dictamen

**Dictamen: GO WITH CONDITIONS.**

- El frontend estático publicado, el mapa Cesium/OSM, la geolocalización, el pronóstico real y la CSP están en buen estado. No se encontraron secretos en el árbol público ni en el historial alcanzable de GitHub; GitHub secret scanning reporta **0 alertas**.
- El backend aplica controles efectivos de sesión, CSRF, Host/Origin, cookies, límites de tasa, validación de entrada y presupuesto persistente. Los endpoints legacy, `/docs` y `/openapi.json` responden **404** en Studio.
- **Hallazgo crítico:** el lockfile del backend fija `certifi==2026.7.22`, afectado por una vulnerabilidad **CRITICAL** de confianza TLS (CWE-295, CAs emSign comprometidas; corregido en `2026.10.18`). El backend usa `httpx` para Open-Meteo y Token Factory; una intercepción TLS podría comprometer la clave de Nebius. **No se modificó el lockfile ni se desplegó nada.**
- **Hallazgo medio:** `deploy/vercel/vercel.template.json` conserva la CSP antigua sin OSM/MapTiler; un despliegue staged futuro podría bloquear el mapa. La producción actual usa el `vercel.json` correcto.
- **Hallazgo medio:** el `Dockerfile` copia `artifacts/` y no hay `.dockerignore`; un build directo desde el árbol sucio incluiría `artifacts/solquira/backend/.data/qanema.sqlite3`. El proceso de staging sí usa una allowlist que lo excluye.
- No se observaron exposiciones de datos personales ni claves en el árbol público, el bundle servido o los headers de Vercel; el metadato de autor se trata aparte.

**Condiciones para GO pleno:** actualizar `certifi` en el backend a `>=2026.10.18` y reconstruir/redeployar el backend con autorización; sincronizar la CSP de la plantilla Vercel antes de un futuro despliegue staged; añadir `.dockerignore` o exigir el contexto staged antes del próximo build de imagen. El frontend publicado no requiere cambios.

## 2. Commit, rama y entorno auditados

| Elemento                    | Valor verificado                                                                    |
| --------------------------- | ----------------------------------------------------------------------------------- |
| Rama local                  | `main`                                                                              |
| HEAD local                  | `4e1e456`                                                                           |
| `origin/main`               | `4e1e456`                                                                           |
| Estado del working tree     | limpio (`git diff --stat origin/main` vacío)                                        |
| Remoto                      | `Shinken009/solquira`, público, Apache-2.0                                          |
| Ramas remotas               | `main` (`4e1e456`) y `fix/responsive-cesium-map-20261031` (`477f70b`, ya fusionada) |
| Producción                  | `https://solquira.vercel.app`, HTTP 200                                             |
| Bundle de producción        | `index-DvtTgwDe.js`                                                                 |
| SHA-256 local vs producción | `C0ACD66C…FB23A` en ambos; **MATCH**                                                |
| Deployment reportado        | `dpl_HcMfHoL5kYTAxcyhFiQkzoqtN9LL`                                                  |
| Backend directo             | `https://api-solquira.r4logic.lat`                                                  |
| Runtime backend declarado   | Docker `python:3.12-slim`, `requirements.lock.txt`                                  |
| Runtime local de pruebas    | Python 3.14.7, Node 25.8.2; no es el runtime exacto del contenedor                  |

## 3. Matriz de controles

| Control                                              | Estado                 | Evidencia                                                                                                                                                    |
| ---------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Secretos en árbol público                            | **PASS**               | Solo `scripts/secrets.local.env.example` (plantilla sin valores); GitHub secret scanning = 0                                                                 |
| Secretos en historial público alcanzable             | **PASS**               | Sin claves reales; los hallazgos de PII en docs borrados están en ramas locales no publicadas (API de GitHub devuelve 422 para esos SHAs)                    |
| Documentos personales / PDF / ZIP / imágenes en repo | **PASS**               | Sin archivos de esas categorías en el árbol público                                                                                                          |
| Archivos grandes o binarios innecesarios             | **PASS**               | Ningún archivo rastreado >500 KB; repo pequeño (~1.3 MiB de pack)                                                                                            |
| Symlinks                                             | **PASS**               | Ningún modo `120000` en `git ls-files -s`                                                                                                                    |
| `.gitignore` / `.vercelignore`                       | **PASS**               | Excluyen `.env`, `.env.*`, secretos locales, `output/`, `.data`, SQLite, `node_modules`, `dist`, `docs/`, `deploy/`, prototipos y scripts de captura         |
| Secretos locales fuera de Git                        | **PASS (privado)**     | Archivo `.env` local ignorado y token local de Vercel ignorado; no se reprodujeron valores ni se publicaron                                                  |
| CSRF de Studio                                       | **PASS**               | POST sin `X-Solquira-CSRF` vía Vercel: **403**; comparación `hmac.compare_digest` en `studio_api.py:156-161`                                                 |
| Sesión opaca y cookies                               | **PASS**               | Vercel `Set-Cookie`: `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`, `Max-Age`; verificado sin imprimir el valor                                          |
| Host / Origin / cross-site                           | **PASS**               | Host inválido: 403; Origin inválido: 403; `Sec-Fetch-Site: cross-site`: 403; `studio_api.py:317-394`                                                         |
| CORS                                                 | **PASS**               | Sin `Access-Control-Allow-Origin` en backend directo; CORS por allowlist (`CORS_ORIGINS`), no wildcard                                                       |
| Rate limiting / admisión                             | **PASS**               | 24 req/min por sesión, 120/min global, 4 activas, 30 bootstrap/IP/min, 240/min global (`studio_api.py:51-58,111-181`)                                        |
| Tamaño y tipo de body                                | **PASS**               | JSON obligatorio, 8 KiB, timeout de lectura 5 s (`studio_api.py:409-435`)                                                                                    |
| Validación de coordenadas                            | **PASS**               | `StudioLocation` limita lat -90..90 y lon -180..180 (`studio_schema.py:56-59`)                                                                               |
| SSRF                                                 | **PASS**               | Open-Meteo URL fija, `follow_redirects=False`, `trust_env=False` (`studio_geo.py:14,68-72`); no hay URL controlada por usuario                               |
| Exposición de docs/admin/legacy                      | **PASS**               | `/docs`, `/openapi.json`, `/api/v1/assistant/tools`: **404**; middleware de Studio bloquea superficies privadas (`main.py:502-558`)                          |
| Acceso directo al backend                            | **PASS (con límites)** | `/healthz` 200; `/v1/field-payload` y `/v1/field-brief` sin sesión: **401**; CSRF y rate limits también aplican directo                                      |
| Errores internos / trazas                            | **PASS**               | Respuestas genéricas 503/422; sin stack traces; `Cache-Control: no-store`                                                                                    |
| Claves en frontend/bundle                            | **PASS**               | Sin `NEBIUS_API_KEY`, `tokenfactory` ni patrones de clave; solo un `Bearer` genérico dentro de Cesium                                                        |
| Source maps públicos                                 | **PASS**               | `index-DvtTgwDe.js.map`: **404**; no hay `.map` en `dist/public/assets`                                                                                      |
| CSP / headers web                                    | **PASS**               | CSP con OSM/MapTiler, HSTS, XCTO, XFO, Referrer-Policy, Permissions-Policy; sin `unsafe-eval`                                                                |
| Modelo y proveedor                                   | **PASS**               | `NANO_MODEL = nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`; Token Factory `https://api.tokenfactory.nebius.com/v1/`; Bearer server-side                            |
| Límites de tokens/tiempo                             | **PASS**               | `MAX_TOKENS=350`, `TIMEOUT_S=3.0`, cap de 700; presupuesto persistente                                                                                       |
| Fallback determinista                                | **PASS**               | `compose_brief` devuelve `fallback_brief` y outcomes `disabled/timeout/provider_error`; validación `parse_compact` antes de aceptar                          |
| Coordenadas hacia el modelo                          | **PASS**               | `weather_evidence` excluye coordenadas (`studio_brief.py`); `studio_service.py:107-110` elimina lat/lon del parcel antes del modelo                          |
| Presupuesto persistente                              | **PASS**               | Ledger SQLite con política, reservas y contadores; no guarda queries ni claves (`studio_budget.py:1-10`)                                                     |
| Dependencia TLS del backend                          | **FAIL (CRITICAL)**    | `certifi==2026.7.22`; OSV/GitHub: CWE-295, CAs emSign comprometidas; fix `>=2026.10.18`                                                                      |
| Plantilla CSP de Vercel                              | **FAIL (MEDIUM)**      | `deploy/vercel/vercel.template.json` sin OSM/MapTiler; root `vercel.json` correcto                                                                           |
| Contexto de build Docker                             | **PARTIAL (MEDIUM)**   | Sin `.dockerignore`; `artifacts/` incluye `.data/qanema.sqlite3`; el staging allowlist lo excluye                                                            |
| Dependencias Node del workspace                      | **PASS / N/A**         | `pnpm audit` reporta critical/high en Express/zod, pero no están en el camino de producción Solquira (Vite estático + FastAPI; sin imports de zod en la app) |
| Devpost / video                                      | **NOT VERIFIED**       | Página responde 200 pero Cloudflare challenge impide verificación automatizada; owner confirma SUBMITTED y Late submission granted                           |
| Licencia / README / ejecución local                  | **PASS**               | Apache-2.0; README con requisitos, comandos de build, tests y límites                                                                                        |

## 4. Hallazgos

### 4.1 CRÍTICO — `certifi` vulnerable en el lockfile del backend

- **Evidencia:** `artifacts/solquira/backend/requirements.lock.txt:4` → `certifi==2026.7.22`.
- **Build:** `deploy/studio/hosted.Dockerfile:4-5` instala exactamente `requirements.lock.txt`.
- **Advisory:** `GHSA-6q48-6c7w-9gw2` / `PYSEC-2026-4320`, CWE-295, severidad **CRITICAL**; “certifi bundles emSign root CAs with compromised intermediate CA keys”; rango afectado desde 2019.03.09, corregido en **2026.10.18**.
- **Impacto:** el backend usa `httpx` para Open-Meteo y Token Factory. Una intercepción TLS con una cadena emitida por una CA comprometida podría exponer la clave de Nebius o alterar respuestas. La complejidad de ataque es alta, pero el impacto es alto.
- **Alcance:** el frontend estático no usa `certifi`; el riesgo es del backend Python y del camino de inferencia live. La versión exacta del contenedor en ejecución no se pudo consultar sin acceso a infraestructura; el lockfile es la fuente de build.
- **Corrección mínima:** actualizar `certifi` a `>=2026.10.18` en `requirements.lock.txt`, reconstruir la imagen del backend, redeployar el backend con autorización y verificar `/solquira-api/healthz` + una llamada controlada. No requiere cambiar el frontend.
- **Estado:** **NO corregido** (solo lectura, sin autorización).

### 4.2 MEDIO — plantilla Vercel con CSP antigua

- **Evidencia:** `deploy/vercel/vercel.template.json` CSP de 330 caracteres sin `tile.openstreetmap.org` ni `api.maptiler.com`; `vercel.json` CSP de 488 caracteres con ambos.
- **Impacto:** un despliegue staged que use la plantilla bloquearía las teselas OSM/MapTiler y degradaría el mapa a Natural Earth. La producción actual usa el `vercel.json` correcto; no afecta la versión ya publicada.
- **Corrección mínima:** sincronizar la CSP de la plantilla con `vercel.json` antes del próximo despliegue staged. No se modificó.

### 4.3 MEDIO — contexto de build Docker y datos locales

- **Evidencia:** `artifacts/solquira/backend/.data/qanema.sqlite3` existe localmente (8 KB, no se leyó su contenido). `deploy/studio/hosted.Dockerfile:9-10` copia `artifacts/` y `prototypes/`; no hay `.dockerignore`.
- **Mitigación existente:** `scripts/check-studio-package.py:25-61` define una allowlist exacta de módulos; `scripts/stage-hosted-release.py` construye el contexto con `stage_source` y excluye `.data`/secretos. El Dockerfile declara que debe usarse ese contexto staged.
- **Riesgo:** un `docker build` directo desde el árbol sucio incluiría el SQLite local (y potencialmente otros archivos ignorados) en la imagen. No hay evidencia de que eso haya ocurrido en la imagen de producción.
- **Corrección mínima:** añadir `.dockerignore` o hacer obligatorio el contexto staged antes del próximo build. No incluir `.data`, `output/` ni archivos de credenciales en paquetes de entrega.

### 4.4 BAJO — path legacy de inferencia con Llama/Nebius Studio

- **Evidencia:** `artifacts/solquira/backend/assistant_inference.py:20-25` usa por defecto `https://api.studio.nebius.ai/v1` y `meta-llama/Llama-3.2-11B-Vision-Instruct`, no Token Factory/Nemotron. `main.py:26-29,636-639` solo monta el router legacy si `studio_mode()` es falso. Producción responde 404 en `/api/v1/assistant/tools`.
- **Impacto:** no está activo en Studio; si se arrancara el backend fuera de `SOLQUIRA_STUDIO_MODE=1`, el path legacy contradiría la narrativa Nemotron/Token Factory. Mantener Studio mode y documentar/retirar el legado a futuro.
- **Estado:** no es una exposición actual.

### 4.5 BAJO — dependencias Node del workspace no usadas en producción

`pnpm audit --prod` reporta:

| Módulo              | Severidad | Advisory                                 | Relevancia Solquira                                                                                         |
| ------------------- | --------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `proxy-addr` 2.0.7  | CRITICAL  | IP spoofing vía IPv4-mapped IPv6         | Express/workspace Node; `pnpm why` no lo encuentra en el camino de Solquira; no está en Vite ni FastAPI     |
| `body-parser` 2.3.0 | HIGH      | DoS por trailing bytes                   | Express/workspace Node; no producción                                                                       |
| `qs` 6.x            | MODERATE  | DoS con `arrayFormat: comma`             | Express/workspace Node; no producción                                                                       |
| `zod` 3.25.76       | HIGH      | Memory exhaustion en colecciones grandes | DevDependency de `@workspace/solquira`; sin imports en `src`; no aparece en el bundle; backend usa Pydantic |

No se elevan a hallazgos de producción porque no están en el bundle servido ni en el backend FastAPI. Actualizar si el workspace Express/API se despliega.

### 4.6 BAJO — endurecimiento web opcional

- `style-src 'unsafe-inline'` es necesario para los estilos inline de React/Cesium; no hay `unsafe-eval` en `script-src`. Aceptable para esta app.
- No se observan `Cross-Origin-Opener-Policy` ni `Cross-Origin-Resource-Policy`. No es un requisito del concurso; evaluar si se endurece el deployment.
- Dependabot y CodeQL están desactivados; no bloquea el concurso, pero reduce detección temprana.

### 4.7 INFORMATIVO — metadatos y archivos locales

- El nombre y correo del autor son visibles en la metadata de commits públicos. El owner indicó que no constituyen una incidencia; **no se propone reescritura de historial**.
- `scripts/secrets.local.env.example` es una plantilla sin valores; `artifacts/solquira/.env.example` también. Los archivos `.env`/token locales están ignorados por Git y `.vercelignore`; no se reprodujeron valores ni se incluyeron en este informe.
- `output/` contiene artefactos históricos y `node_modules` extraídos; está ignorado y no pertenece al repo público. No incluir en ZIP, imagen ni entrega.
- El escaneo `git status --ignored` agotó tiempo por los `node_modules` bajo `output/gates`; se verificó el árbol público y las categorías de archivos por otras vías.

## 5. Riesgos de exposición pública

| Riesgo                          | Estado                                                                                                                                                                            |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Claves en GitHub/GitHub history | No detectadas; secret scanning 0                                                                                                                                                  |
| Documentos personales/PDF/ZIP   | No presentes en el árbol público                                                                                                                                                  |
| PII en commits                  | Nombre/correo de autor público; owner lo acepta; no se reescribe                                                                                                                  |
| Datos locales en imagen Docker  | Mitigado por staging allowlist; riesgo si se construye directo sin `.dockerignore`                                                                                                |
| Clave Nebius en frontend        | No; solo servidor                                                                                                                                                                 |
| Clave Nebius en logs            | No se loguean queries, coordenadas ni claves; `dryland_brief.py` lo declara                                                                                                       |
| Coordenadas de usuario          | Redondeadas a 0.001°; el modelo recibe solo evidencia meteorológica agregada, sin coordenadas                                                                                     |
| Open-Meteo / OSM / GIBS         | Reciben coordenadas redondeadas o teselas de la vista; documentado en UI/README                                                                                                   |
| Inferencia pública              | Sesión + CSRF + límites + presupuesto; cualquiera puede obtener una sesión y consumir dentro de los caps. Es un riesgo de abuso/agotamiento del presupuesto, no de acceso a datos |

## 6. Diferencias local / GitHub / producción

| Aspecto       | Diferencia                                                                                                      | Impacto                                                                             |
| ------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Código        | Local `main` = `origin/main` = `4e1e456`; working tree limpio                                                   | Sin drift de código                                                                 |
| Bundle        | SHA-256 local de `index-DvtTgwDe.js` = producción                                                               | Integridad frontend verificada                                                      |
| CSP           | Producción y root `vercel.json` actualizados; plantilla Vercel stale                                            | Solo afecta futuros despliegues staged                                              |
| Python        | Local 3.14.7 / FastAPI 0.136.0 / Pydantic 2.12.5 / Starlette 1.6.0; Docker 3.12 / lock 0.143.0 / 2.14.0 / 1.7.0 | Tests locales no son paridad exacta del contenedor; lock es la fuente de producción |
| Node          | Local 25.8.2; Vercel 22.x                                                                                       | Build Vercel con `pnpm install --frozen-lockfile` OK; bundle hash coincide          |
| Datos locales | `.data/qanema.sqlite3` y `output/` solo locales                                                                 | No públicos; no empaquetar                                                          |
| Devpost       | Página detrás de Cloudflare challenge                                                                           | Contenido/video no verificados automáticamente; owner confirma SUBMITTED            |

## 7. Pruebas ejecutadas

| Prueba                                                     | Resultado                                                                                      |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `pnpm --filter @workspace/solquira typecheck`              | **PASS**                                                                                       |
| `pnpm --filter @workspace/solquira build`                  | **PASS**; bundle `index-DvtTgwDe.js`                                                           |
| Unitarias de cartografía                                   | **13/13 PASS** (`rasterLoad` + `basemap`)                                                      |
| Playwright local (mocks de API/teselas)                    | **19/19 PASS**; 360/390/768/1366/1920; 2D/3D; resize; orientación; OSM/NASA fallback; CSP      |
| Python `test_studio_security.py` + `test_dryland_brief.py` | **41 passed, 80 subtests**; sin red real; `SOLQUIRA_STUDIO_MODE=1`                             |
| Producción 390×844                                         | PASS: OSM, 2D, geolocalización, NASA recibida, 0 errores consola/CSP/página                    |
| Producción 1366×900                                        | PASS en la verificación post-deploy previa: OSM, 3D, NASA 46/46, 0 errores                     |
| Headers producción                                         | PASS: CSP, HSTS, XCTO, XFO, Referrer, Permissions                                              |
| CSRF/cookies/Host/Origin                                   | PASS: 403 sin CSRF, cookie Secure/HttpOnly/Strict, Host/Origin inválidos 403                   |
| `/docs`, `/openapi.json`, legacy assistant                 | PASS: 404                                                                                      |
| `/v1/field-payload`, `/v1/field-brief` sin sesión          | PASS: 401                                                                                      |
| Source map                                                 | PASS: 404                                                                                      |
| Bundle vs producción                                       | PASS: SHA-256 idéntico                                                                         |
| `pnpm audit --prod`                                        | 1 critical, 2 high, 1 moderate; todos fuera del camino de producción salvo revisión contextual |
| OSV Python (22 paquetes)                                   | 1 vulnerable: `certifi==2026.7.22` (CRITICAL); corregido en 2026.10.18                         |
| Devpost                                                    | **NOT VERIFIED** por Cloudflare; owner confirma SUBMITTED + Late submission granted            |

## 8. Acciones correctivas estrictamente necesarias

1. **CRÍTICO — backend:** actualizar `certifi` en `artifacts/solquira/backend/requirements.lock.txt` a `>=2026.10.18`; reconstruir la imagen del backend; redeployar el backend con autorización; verificar health y una ejecución controlada. Hasta entonces, evitar inferencia live con la clave de Nebius si se quiere eliminación estricta del riesgo TLS.
2. **MEDIO — plantilla Vercel:** sincronizar la CSP de `deploy/vercel/vercel.template.json` con `vercel.json` antes de un futuro despliegue staged.
3. **MEDIO — build Docker:** añadir `.dockerignore` o hacer obligatorio el contexto staged; excluir `.data`, `.env`, `output/`, `node_modules` y SQLite.
4. **BAJO — legado:** mantener `SOLQUIRA_STUDIO_MODE=1` y documentar/retirar el path `assistant_inference.py` (Llama/Nebius Studio) en una tarea futura.
5. **BAJO — dependencias Node:** actualizar `proxy-addr`, `body-parser`, `qs` y `zod` si el workspace Express/API se despliega; no es necesario para la versión estática actual.

Ninguna de estas acciones se aplicó: la auditoría fue solo lectura y no se desplegó ni reinició nada.

## 9. Riesgos residuales aceptables

- El demo es público y cualquiera puede obtener una sesión y consumir geodatos/inferencia dentro de los límites (24/min sesión, 120/min global, 100 llamadas/día, 600 lifetime). El fallback determinista mantiene la app usable si el presupuesto se agota; no hay acceso a datos de otros usuarios.
- OpenStreetMap público es best-effort; NASA GIBS puede tardar ~21 s y no tiene SLA. El mapa cae a Natural Earth y lo informa.
- La validación de navegador se hizo en Chromium headless; no sustituye iOS/Safari físico ni una pérdida real de contexto WebGL.
- El video de Devpost no se pudo verificar por Cloudflare; el owner confirma su incorporación.
- La paridad exacta del runtime Python de producción no se verificó; el lockfile y el Dockerfile son la fuente de build.

## 10. Recomendación final

**GO WITH CONDITIONS.** La versión estática publicada y el recorrido funcional pueden mantenerse sin cambios para la evaluación. El backend no debe considerarse plenamente GO hasta actualizar `certifi` y reconstruir la imagen; la plantilla Vercel y el `.dockerignore` deben corregirse antes del próximo despliegue staged. No se recomienda tocar el frontend, el mapa, NASA ni la postulación.

Si el owner no autoriza el bump de `certifi` y el rebuild del backend, la recomendación estricta para el camino de inferencia live es **NO-GO**; el frontend/fallback puede seguir público, pero la clave de Nebius queda expuesta a un riesgo TLS crítico conocido.
