import { useEffect, useRef, useState, type FormEvent } from "react";
import { useStudioPreferences } from "../StudioPreferences";
import type { Point } from "./client";

type Row = { day: string; rain: number | null; temperature: number | null };
type State =
  | "idle"
  | "loading"
  | "ready"
  | "dates"
  | "session"
  | "limited"
  | "disabled"
  | "unavailable"
  | "invalid"
  | "timeout";

function retryDeadline(header: string | null, now: number) {
  const value = header?.trim() ?? "";
  const deadline = /^\d+$/.test(value)
    ? now + Number(value) * 1000
    : Date.parse(value);
  return Number.isFinite(deadline)
    ? Math.max(now + 1000, deadline)
    : now + 60000;
}

function rowsFrom(
  value: Record<string, unknown>,
  start: string,
  end: string,
): Row[] {
  if (
    value.status !== "ok" ||
    value.provider !== "NASA POWER" ||
    value.timeStandard !== "UTC"
  )
    throw new Error("unavailable");
  const units = value.units as Record<string, unknown> | undefined;
  const period = value.period as Record<string, unknown> | undefined;
  const series = value.values as
    Record<string, Record<string, unknown>> | undefined;
  if (
    units?.PRECTOTCORR !== "mm/day" ||
    units?.T2M !== "C" ||
    period?.start !== start ||
    period.end !== end
  )
    throw new Error("invalid");
  const rows: Row[] = [];
  for (
    let day = Date.parse(start);
    day <= Date.parse(end) && rows.length < 31;
    day += 86400000
  ) {
    const iso = new Date(day).toISOString().slice(0, 10);
    const key = iso.replaceAll("-", "");
    const rain = series?.PRECTOTCORR?.[key],
      temperature = series?.T2M?.[key];
    if (
      !(
        rain === null ||
        (typeof rain === "number" && Number.isFinite(rain) && rain >= 0)
      ) ||
      !(
        temperature === null ||
        (typeof temperature === "number" && Number.isFinite(temperature))
      )
    )
      throw new Error("invalid");
    rows.push({ day: iso, rain, temperature });
  }
  if (!rows.length || rows.at(-1)?.day !== end) throw new Error("invalid");
  return rows;
}

export default function PowerContext({
  point,
  csrf,
  retryAt,
  onRetryAt,
  onReconnect,
}: {
  point: Point;
  csrf: string;
  retryAt: number;
  onRetryAt: (deadline: number) => void;
  onReconnect: () => void;
}) {
  const { locale } = useStudioPreferences();
  const t = (en: string, es: string) => (locale === "es" ? es : en);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [state, setState] = useState<State>("idle");
  const [now, setNow] = useState(Date.now);
  const remaining = Math.max(0, Math.ceil((retryAt - now) / 1000));
  const active = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      const request = active.current;
      active.current = null;
      request?.abort();
    },
    [],
  );
  useEffect(() => {
    if (retryAt <= Date.now()) return;
    const timer = window.setInterval(() => {
      const current = Date.now();
      setNow(current);
      if (current >= retryAt) window.clearInterval(timer);
    }, 1000);
    return () => window.clearInterval(timer);
  }, [retryAt]);

  const editDate = (setDate: (date: string) => void, date: string) => {
    setDate(date);
    setRows([]);
    if (state !== "session" && state !== "disabled" && state !== "limited")
      setState("idle");
  };
  const lookup = async (event: FormEvent) => {
    event.preventDefault();
    if (
      !csrf ||
      active.current ||
      state === "session" ||
      state === "disabled" ||
      Date.now() < retryAt
    )
      return;
    const days = (Date.parse(end) - Date.parse(start)) / 86400000;
    setRows([]);
    if (
      !Number.isInteger(days) ||
      days < 0 ||
      days > 30 ||
      end >= new Date().toISOString().slice(0, 10)
    ) {
      setState("dates");
      return;
    }
    const controller = new AbortController();
    active.current = controller;
    const timer = window.setTimeout(() => controller.abort(), 35000);
    setState("loading");
    try {
      const base = (import.meta.env.VITE_API_URL || "/solquira-api").replace(
        /\/$/,
        "",
      );
      const response = await fetch(`${base}/studio/power`, {
        method: "POST",
        credentials: "same-origin",
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          "X-Solquira-CSRF": csrf,
        },
        body: JSON.stringify({ ...point, start, end }),
      });
      if (active.current !== controller) return;
      if (response.status === 429) {
        const receivedAt = Date.now();
        setNow(receivedAt);
        onRetryAt(
          retryDeadline(response.headers.get("Retry-After"), receivedAt),
        );
        setState("limited");
        return;
      }
      if (response.status === 422) {
        setState("dates");
        return;
      }
      if (response.status === 401 || response.status === 403) {
        setState("session");
        return;
      }
      if (!response.ok) {
        setState("unavailable");
        return;
      }
      try {
        const body = await response.json();
        if (active.current !== controller) return;
        if (controller.signal.aborted) {
          setState("timeout");
          return;
        }
        if (body?.status === "disabled") {
          setState("disabled");
          return;
        }
        if (body?.status === "unavailable") {
          setState("unavailable");
          return;
        }
        setRows(rowsFrom(body, start, end));
        setState("ready");
      } catch {
        if (active.current === controller)
          setState(controller.signal.aborted ? "timeout" : "invalid");
      }
    } catch {
      if (active.current === controller)
        setState(controller.signal.aborted ? "timeout" : "unavailable");
    } finally {
      window.clearTimeout(timer);
      if (active.current === controller) active.current = null;
    }
  };
  const number = new Intl.NumberFormat(locale === "es" ? "es-CL" : "en-US", {
    maximumFractionDigits: 2,
  });
  const errors: Partial<Record<State, string>> = {
    dates: t(
      "Choose 1–31 completed days (UTC), with the start on or before the end.",
      "Elige de 1 a 31 días ya completos (UTC), con el inicio igual o anterior al fin.",
    ),
    session: t(
      "The session could not be verified. Reconnect Studio before trying again.",
      "No se pudo verificar la sesión. Reconecta Studio antes de volver a consultar.",
    ),
    disabled: t(
      "NASA POWER is disabled for this session.",
      "NASA POWER no está habilitado para esta sesión.",
    ),
    unavailable: t(
      "NASA POWER is temporarily unavailable. Try again later.",
      "NASA POWER no está disponible temporalmente. Inténtalo más tarde.",
    ),
    invalid: t(
      "The source response could not be verified. No series was displayed.",
      "No se pudo verificar la respuesta de la fuente. No se mostró ninguna serie.",
    ),
    timeout: t(
      "The query timed out. You can try again later.",
      "La consulta superó el tiempo de espera. Puedes intentarlo más tarde.",
    ),
  };
  return (
    <details className="qg-method" data-testid="power-context">
      <summary>
        {t("Historical weather · NASA POWER", "Tiempo histórico · NASA POWER")}
      </summary>
      <p>
        {t(
          "Compare daily rain and temperature for 1–31 completed days. This is gridded historical data, not a parcel measurement.",
          "Compara precipitación y temperatura diarias de 1 a 31 días completos. Son datos históricos de grilla, no mediciones de parcela.",
        )}
      </p>
      <p>
        {t(
          "Only when you request the series, rounded coordinates are sent to NASA POWER.",
          "Solo al consultar la serie se envían coordenadas redondeadas a NASA POWER.",
        )}
      </p>
      <form onSubmit={lookup}>
        <div className="qg-coordinate-inputs">
          <label>
            {t("Start", "Inicio")}{" "}
            <input
              type="date"
              required
              value={start}
              disabled={state === "loading"}
              onChange={(e) => editDate(setStart, e.target.value)}
            />
          </label>
          <label>
            {t("End", "Fin")}{" "}
            <input
              type="date"
              required
              value={end}
              disabled={state === "loading"}
              onChange={(e) => editDate(setEnd, e.target.value)}
            />
          </label>
        </div>
        <button
          type="submit"
          className="qg-load"
          disabled={
            !csrf ||
            state === "loading" ||
            state === "session" ||
            state === "disabled" ||
            remaining > 0
          }
        >
          {state === "loading"
            ? t("Loading…", "Consultando…")
            : t("Load historical weather", "Consultar tiempo histórico")}
        </button>
      </form>
      {errors[state] && <p role="alert">{errors[state]}</p>}
      {state === "session" && (
        <button type="button" className="qg-open" onClick={onReconnect}>
          {t("Reconnect Studio", "Reconectar Studio")}
        </button>
      )}
      {remaining > 0 ? (
        <p role="status" data-testid="power-retry">
          {t(
            "Wait before requesting another NASA POWER series: ",
            "Espera antes de volver a consultar NASA POWER: ",
          )}
          <span role="timer" aria-live="off">
            {number.format(remaining)} s
          </span>
        </p>
      ) : (
        state === "limited" && (
          <p role="status">
            {t(
              "You can request the series again.",
              "Ya puedes volver a consultar la serie.",
            )}
          </p>
        )
      )}
      {state === "ready" && (
        <div aria-live="polite">
          <p>
            <a
              href="https://power.larc.nasa.gov/"
              target="_blank"
              rel="noreferrer"
            >
              NASA POWER
            </a>{" "}
            · {start} — {end} UTC
          </p>
          <table>
            <thead>
              <tr>
                <th scope="col">{t("Day (UTC)", "Día (UTC)")}</th>
                <th scope="col">{t("Rain (mm/day)", "Lluvia (mm/día)")}</th>
                <th scope="col">
                  {t("Mean temperature (°C)", "Temperatura media (°C)")}
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.day}>
                  <th scope="row">{row.day}</th>
                  <td>{row.rain === null ? "—" : number.format(row.rain)}</td>
                  <td>
                    {row.temperature === null
                      ? "—"
                      : number.format(row.temperature)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>
            {t(
              "— means missing. These data do not estimate irrigation water or change the illustrative crop comparison.",
              "— significa dato faltante. Estos datos no estiman agua de riego ni modifican la comparación ilustrativa de cultivos.",
            )}
          </p>
        </div>
      )}
    </details>
  );
}
