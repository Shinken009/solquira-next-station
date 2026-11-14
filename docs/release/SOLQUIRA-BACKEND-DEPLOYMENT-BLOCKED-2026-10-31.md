# Solquira — Fase 2 detenida por falta de acceso al host

Fecha: 2026-10-31  
Rama: `fix/certifi-20261019`  
Estado: **NO DESPLEGADO — bloqueo en la verificación previa A.5/A.6**

## 1. Resultado

La Fase 2 no se ejecutó. No se transfirió la imagen, no se reemplazó el contenedor, no se reinició nada, no se consumió inferencia y no se generó `04_evidencia_ia_live.mp4`.

Producción sigue respondiendo:

- `GET https://api-solquira.r4logic.lat/solquira-api/healthz` → **200**
- Bootstrap público: `inference.available=true`, `calls_used=39/600`

## 2. Verificación de acceso

Host reportado por los artefactos: `solquira-demo`, `172.238.217.78`, usuario `deploy`.

| Prueba                                                          | Resultado                            |
| --------------------------------------------------------------- | ------------------------------------ |
| TCP/22 a `172.238.217.78`                                       | **False / timeout**                  |
| `ssh -o BatchMode=yes deploy@172.238.217.78 "id -un; hostname"` | **exit 255**, `Connection timed out` |
| Health público                                                  | 200                                  |

La documentación del host (`output/deploy/TAILSCALE-ADMIN.md`) ya registraba:

- Firewall de Akamai con SSH permitido solo desde `179.8.13.244/32`; la IP actual es distinta.
- Clave `solquira_akamai_ed25519` con passphrase interactiva, no cargada en un agente.
- SSH interactivo del owner requerido; no se debe pedir passphrase ni activar ssh-agent.

No se intentó abrir el firewall, usar LISH, Tailscale, la API de Akamai ni solicitar la passphrase. Eso queda fuera de esta autorización y no se hizo.

## 3. Imagen preparada y bundle

La imagen final sigue lista y verificada:

- Tag: `solquira-studio:certifi-20261019-final`
- Image ID: `sha256:a969dcf803f8c90830f6deff6745a7a0845a78ca1419aa655c95c45d537bd412`
- `certifi=2026.10.19`, `pip check` limpio, TLS 401/200, 41/41 tests.

Bundle local preparado para transferencia:

```text
output/certifi-remediation-20261031/deploy/
├── solquira-certifi-20261019-final.tar  (57,172,992 bytes)
├── manifest.sha256.json
└── image-inspect.json
```

SHA-256 del tar:

```text
357600379A5CE60AE7EEB976524DAD3E3967CA365C124D6C0F9FB416FA7E40F7
```

No se transfirió el tar. No se copió `/srv/solquira/app.env` ni la base SQLite. No se expusieron secretos.

## 4. Qué falta para continuar

Se necesita una de estas opciones, con autorización específica:

1. Abrir TCP/22 en el firewall de Akamai solo para la IP actual del owner (o el rango mínimo necesario) y mantener la clave/passphrase en una sesión interactiva del owner.
2. Proporcionar una sesión SSH interactiva ya autenticada al host `solquira-demo`.
3. Ejecutar el bundle preparado en el host desde una sesión del owner; el procedimiento de preflight, backup, swap y rollback está en `docs/release/SOLQUIRA-BACKEND-DEPLOYMENT-READINESS-2026-10-31.md`.

No se debe reemplazar el contenedor ni ejecutar inferencia hasta completar:

- Confirmación del digest real de la imagen actual.
- Backup consistente de `/srv/solquira/data/studio-budget.sqlite3`.
- Preservación de configuración, volumen, env, red, puerto, recursos, seguridad y restart.
- Rollback probado.

## 5. Riesgos residuales

- El backend de producción sigue con el lockfile vulnerable `certifi==2026.7.22` hasta que se autorice y ejecute el reemplazo; no se verificó su versión en vivo.
- La imagen corregida está lista, pero no desplegada.
- El contador de inferencia sigue en 39/600; no se consumió nada.
- No hay cambios en frontend, Vercel, Cesium, NASA, Devpost ni YouTube.

## 6. Decisión

**Detenido correctamente antes de cualquier cambio.** La Fase 2 queda pendiente de acceso operativo al host. No se ejecutó rollback porque no hubo modificación que revertir.

## 7. Reintento por Tailscale (2026-10-31)

Se intentó retomar la Fase 2 exclusivamente por la red privada, sin tocar firewall, ACL, claves, ssh-agent ni Tailscale.

| Prueba                   | Resultado                                                     |
| ------------------------ | ------------------------------------------------------------- |
| Servicio local Tailscale | `Running` / `Automatic`                                       |
| `tailscale status`       | `BackendState=NoState`; “Tailscale is starting. Please wait.” |
| `TailscaleIPs` locales   | vacío                                                         |
| Peer `solquira-demo`     | no visible en `status --json`                                 |
| Espera de 40 s           | mismo `NoState`                                               |
| `tailscale ping`         | no ejecutado: no hay IP/nombre del peer                       |
| TCP/22 por IP privada    | no ejecutado: no hay IP privada                               |
| SSH                      | no intentado: se detuvo antes                                 |

No se ejecutó `tailscale up`, login, reinicio de servicio, cambio de ACL ni modificación de claves/ssh-agent. No se abrió SSH público ni se usó LISH/Akamai API.

**Etapa exacta de fallo:** conexión/autenticación de Tailscale en el equipo local (`NoState`, sin `TailscaleIPs`), antes de poder resolver o alcanzar `solquira-demo`. El owner debe completar la conexión de Tailscale en su interfaz/terminal; después se puede reanudar `tailscale ping`, TCP/22 privado y SSH sin passphrase interactiva.

La imagen `solquira-studio:certifi-20261019-final`, el bundle y el procedimiento siguen preparados. Producción no fue modificada; `calls_used` permanece en 39/600 y no se generó `04_evidencia_ia_live.mp4`.

## 8. Reintento con Tailscale conectado (2026-10-31)

Con Tailscale abierto por el owner:

| Prueba                               | Resultado                                           |
| ------------------------------------ | --------------------------------------------------- |
| `BackendState`                       | `Running`                                           |
| IP local Tailscale                   | `100.120.215.108`                                   |
| Peer `solquira-demo`                 | `100.105.45.41`, online                             |
| MagicDNS                             | `solquira-demo.tailc49605.ts.net.`                  |
| `tailscale ping solquira-demo`       | **pong** (DERP/directo, ~100-600 ms)                |
| TCP/22 a `100.105.45.41`             | **True**                                            |
| SSH BatchMode `deploy@100.105.45.41` | **Permission denied (publickey)**, exit 255         |
| `ssh-add -l`                         | agente SSH no disponible                            |
| Identidades por defecto              | solo `id_rsa`; la clave documentada no está cargada |

**Etapa exacta de fallo:** autenticación de clave pública SSH, después de que Tailscale y TCP/22 funcionaran. No se usó `-i`, no se leyó la clave, no se inició/cargó `ssh-agent`, no se modificaron claves, ACL ni Tailscale. No se solicitó passphrase.

El owner debe completar la autenticación SSH en su terminal (o cargar la clave en su agente como acción propia). Después se puede continuar con preflight, backup SQLite, transferencia de la imagen, swap y validación.

## 9. Bloqueo de la ruta explícita de clave (2026-10-31)

El owner indicó que la clave `solquira_akamai_ed25519` está disponible mediante el agente SSH de Windows. Se intentó la comprobación solicitada:

```text
ssh -o BatchMode=yes -o IdentitiesOnly=yes \
  -i <ruta-de-la-clave> deploy@100.105.45.41 "id -un; hostname"
```

La capa local **CC Safety Net** bloqueó el comando **antes de ejecutarlo**:

```text
Rule: secret.home.ssh
Reason: Access to a sensitive path is not allowed.
```

No hubo intento SSH, no se leyó la clave y no se ejecutó `ssh-add`. No se intentó ningún workaround (copia de la clave, ruta alternativa, `-i` indirecto, config SSH ni carga de agente).

**Etapa exacta de fallo:** política local de acceso a `~/.ssh`, anterior a la autenticación. Tailscale y TCP/22 privados siguen funcionando. Para continuar hace falta una de estas acciones del owner:

1. Ejecutar el bundle `README_DEPLOY.md` en su terminal autenticada y avisar al terminar el preflight/swap.
2. Autorizar explícitamente el uso **solo del agente SSH** (sin `-i` y sin tocar `~/.ssh`) para que esta sesión pueda ejecutar el preflight; el agente debe estar disponible para el proceso.
3. Proporcionar una sesión autenticada equivalente que no requiera que esta herramienta acceda a la ruta protegida.

Producción no fue modificada; `calls_used` sigue en 39/600 y no se generó `04_evidencia_ia_live.mp4`.

## 10. Intento solo con agente SSH (2026-10-31)

El owner autorizó usar exclusivamente el agente SSH, sin `-i` y sin tocar `~/.ssh`.

| Prueba                                                            | Resultado                                                |
| ----------------------------------------------------------------- | -------------------------------------------------------- |
| Servicio Windows `ssh-agent`                                      | **Stopped / Disabled**                                   |
| `ssh-add -l`                                                      | **Error connecting to agent: No such file or directory** |
| `ssh -o BatchMode=yes -o IdentitiesOnly=yes deploy@100.105.45.41` | **Permission denied (publickey)**, exit 255              |
| Identidades ofrecidas por OpenSSH                                 | ninguna; el agente no es visible                         |

**Etapa exacta de fallo:** el cliente OpenSSH no tiene un agente accesible (servicio `ssh-agent` detenido/deshabilitado) ni una identidad por defecto aceptada por el servidor. La ruta explícita a la clave sigue bloqueada por CC Safety Net. No se inició el servicio, no se ejecutó `ssh-add`, no se cargó ninguna clave y no se modificó el agente.

Para continuar, el owner debe elegir una opción:

1. Habilitar/iniciar el agente OpenSSH de Windows y cargar la clave como acción propia; luego se puede reintentar el SSH sin `-i`.
2. Ejecutar el bundle `README_DEPLOY.md` en su terminal autenticada.
3. Autorizar explícitamente una suspensión temporal y reversible de CC Safety Net para usar `-i`, con backup de configuración y reactivación inmediata.

Producción intacta; `calls_used=39/600`; sin video live.
