import { useState, useCallback, useEffect, useRef } from "react";
import { useStudioPreferences } from "../StudioPreferences";
import type { Point } from "./client";
import "./field-shift.css";

export interface FieldShiftJourneyProps {
  point: Point | null;
  csrfToken?: string;
  onSelectPreset?: (lat: number, lon: number) => void;
}

interface SeasonSample {
  season_year: number;
  days: number;
  precipitation_mm: number;
  dry_day_fraction: number;
  heavy_rain_days: number;
  temperature_mean_c: number;
}

interface SeasonalContext {
  label: string;
  count: number;
  sample_years: number[];
  mean_rainfall_mm: number;
  median_rainfall_mm: number;
  dry_day_fraction: number;
  mean_heavy_rain_days: number;
  mean_temperature_c: number;
  sample: SeasonSample[];
  completeness_rule: string;
}

interface PathwayResult {
  id: string;
  name: string;
  sequence: string[];
  dry_exposure_indicator: number;
  wet_exposure_indicator: number | null;
  primary_indicator: number | null;
  ground_cover_level: number;
  rotation_diversity_level: number;
  observations: string[];
  observations_es?: string[];
  limitation: string;
  limitation_es?: string;
  agronomic_viability: "not_assessed";
}

interface EvaluationResponse {
  version: string;
  status: "historical_evidence_available" | "insufficient_evidence" | "source_unavailable";
  historical_context?: SeasonalContext;
  pathways: PathwayResult[];
  provenance: {
    provider: string;
    dataset: string;
    source_url: string;
    period_start?: string;
    period_end?: string;
    time_standard?: string;
    units: Record<string, string>;
    limitation: string;
  };
  quality?: { requested_days: number; available_days: number; missing_days: number };
  disclaimers: string[];
}

// Demo presets choose a *place* and a question, never soil or drainage measurements.
const PRESETS = [
  {
    id: "coquimbo", name: "Coquimbo",
    descriptionEs: "Explorar déficit de agua", descriptionEn: "Explore water deficit",
    lat: -30.0400, lon: -71.2500, concern: "dry", demoSoil: "sandy", demoDrainage: "well_drained",
  },
  {
    id: "maule", name: "Maule",
    descriptionEs: "Explorar variación estacional", descriptionEn: "Explore seasonal variability",
    lat: -35.4300, lon: -71.6600, concern: "balanced", demoSoil: "loamy", demoDrainage: "well_drained",
  },
  {
    id: "chiloe", name: "Chiloé",
    descriptionEs: "Explorar exceso de humedad", descriptionEn: "Explore excess rainfall",
    lat: -42.4800, lon: -73.7600, concern: "wet", demoSoil: "clayey", demoDrainage: "restricted",
  },
] as const;

const PATHWAY_ES: Record<string, string> = {
  continue: "Mantener la secuencia actual",
  legume: "Diversificar con leguminosas",
  cover: "Priorizar cobertura vegetal",
  forage: "Incorporar forrajeras",
};
const CROP_ES: Record<string, string> = {
  Cereal: "Cereal", Legume: "Leguminosa", Cover: "Cobertura", Forage: "Forrajera",
};

export function FieldShiftJourney({ point, csrfToken, onSelectPreset }: FieldShiftJourneyProps) {
  const { locale } = useStudioPreferences();
  const isEs = locale === "es";

  const [activePreset, setActivePreset] = useState<string | null>(null);
  const [season, setSeason] = useState<"apr_sep" | "oct_mar">("apr_sep");
  const [drainage, setDrainage] = useState<"well_drained" | "restricted" | "unknown">("unknown");
  const [soil, setSoil] = useState<"clayey" | "sandy" | "loamy" | "unknown">("unknown");
  const [priority, setPriority] = useState<"water" | "soil" | "diversity">("water");
  const [concern, setConcern] = useState<"dry" | "wet" | "balanced">("dry");
  const [soilOrigin, setSoilOrigin] = useState<"self_reported" | "illustrative_demo">("self_reported");
  const [drainageOrigin, setDrainageOrigin] = useState<"self_reported" | "illustrative_demo">("self_reported");
  const selectedPreset = PRESETS.find((p) => p.id === activePreset);
  const presetConfirmed = !selectedPreset || Boolean(point &&
    Math.abs(point.latitude - selectedPreset.lat) < 0.0001 &&
    Math.abs(point.longitude - selectedPreset.lon) < 0.0001);

  const [loading, setLoading] = useState(false);
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const requestRef = useRef<AbortController | null>(null);

  const handleApplyPreset = (p: typeof PRESETS[number]) => {
    setActivePreset(p.id);
    setConcern(p.concern);
    // Never represent preset assumptions as farmer self-reported soil data.
    setSoil("unknown");
    setDrainage("unknown");
    setSoilOrigin("self_reported");
    setDrainageOrigin("self_reported");
    if (onSelectPreset) {
      onSelectPreset(p.lat, p.lon);
    }
  };

  useEffect(() => {
    if (!point) return;
    const preset = PRESETS.find((p) => p.id === activePreset);
    if (preset && (Math.abs(point.latitude - preset.lat) > 0.0001 ||
                   Math.abs(point.longitude - preset.lon) > 0.0001)) {
      setActivePreset(null);
      if (soilOrigin === "illustrative_demo") { setSoil("unknown"); setSoilOrigin("self_reported"); }
      if (drainageOrigin === "illustrative_demo") { setDrainage("unknown"); setDrainageOrigin("self_reported"); }
    }
    // A new confirmed point, not a demo-button click, invalidates the old example.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [point?.latitude, point?.longitude]);

  const useIllustrativeProfile = () => {
    if (!selectedPreset || !presetConfirmed) return;
    setSoil(selectedPreset.demoSoil);
    setDrainage(selectedPreset.demoDrainage);
    setSoilOrigin("illustrative_demo");
    setDrainageOrigin("illustrative_demo");
  };

  // Do not show results for a different place, season or reported field state.
  useEffect(() => {
    requestRef.current?.abort();
    requestRef.current = null;
    setLoading(false);
    setEvaluation(null);
    setErrorMsg(null);
    return () => { requestRef.current?.abort(); };
  }, [point?.latitude, point?.longitude, season, drainage, soil, priority, concern, csrfToken, soilOrigin, drainageOrigin]);

  const handleRunEvaluation = useCallback(async () => {
    if (!point || !csrfToken || !presetConfirmed) return;
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setLoading(true);
    setEvaluation(null);
    setErrorMsg(null);

    const payload = {
      latitude: point.latitude,
      longitude: point.longitude,
      season,
      drainage,
      soil,
      soil_origin: soilOrigin,
      drainage_origin: drainageOrigin,
      priority,
      concern,
    };

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (csrfToken) {
        headers["X-Solquira-CSRF"] = csrfToken;
      }

      const res = await fetch("/solquira-api/studio/field-shift/evaluate", {
        method: "POST",
        headers,
        signal: controller.signal,
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        if (res.status === 429) throw new Error("rate_limited");
        if (res.status === 401 || res.status === 403) throw new Error("session");
        throw new Error("unavailable");
      }

      const data: EvaluationResponse = await res.json();
      if (!controller.signal.aborted) setEvaluation(data);
    } catch (err: unknown) {
      if (controller.signal.aborted) return;
      const reason = err instanceof Error ? err.message : "";
      setErrorMsg(
        reason === "rate_limited"
          ? (isEs ? "Límite temporal de consultas alcanzado. Inténtalo más tarde." : "Temporary request limit reached. Try again later.")
          : reason === "session"
            ? (isEs ? "La sesión expiró. Reconecta el Studio para continuar." : "Session expired. Reconnect Studio to continue.")
            : (isEs ? "No se pudo consultar NASA POWER. No se generan datos sustitutivos." : "NASA POWER could not be queried. No substitute data were generated.")
      );
    } finally {
      if (requestRef.current === controller) {
        requestRef.current = null;
        setLoading(false);
      }
    }
  }, [point, season, drainage, soil, priority, concern, csrfToken, isEs, soilOrigin, drainageOrigin, presetConfirmed]);

  return (
    <section id="qs-field-shift" className="field-shift-card" aria-label="Field Shift Decision Support">
      <header className="field-shift-header">
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700 }}>
            {isEs ? "Field Shift — Tu próxima temporada" : "Field Shift — Your next season"}
          </h3>
          <p style={{ margin: "0.2rem 0 0", fontSize: "0.8rem", color: "var(--qs-muted, #718096)" }}>
            {isEs
              ? "Estimaciones históricas de NASA POWER para explorar alternativas de manejo, no predecir la próxima cosecha."
              : "Historical NASA POWER gridded estimates to explore management choices—not predict the next harvest."}
          </p>
        </div>
        <span className="field-shift-badge">NASA Space Apps 2026</span>
      </header>

      {/* Preset Territorials */}
      <div style={{ marginBottom: "0.75rem" }}>
        <div style={{ fontSize: "0.78rem", fontWeight: 600, marginBottom: "0.35rem" }}>
          {isEs ? "Comienza en un territorio de ejemplo; después confirma el lugar:" : "Choose a demonstration area, then confirm the location:"}
        </div>
        <div className="field-shift-presets">
          {PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              className={`preset-chip ${activePreset === p.id ? "active" : ""}`}
              onClick={() => handleApplyPreset(p)}
              title={`${p.name} (${p.lat}, ${p.lon})`}
            >
              <strong>{p.name}</strong> · <span style={{ fontSize: "0.75rem" }}>{isEs ? p.descriptionEs : p.descriptionEn}</span>
            </button>
          ))}
        </div>
        {selectedPreset && (
          <div className="field-shift-demo-option">
            <button className="preset-chip" type="button" disabled={!presetConfirmed} onClick={useIllustrativeProfile}>
              {isEs ? "Cargar perfil de suelo ilustrativo" : "Load illustrative field profile"}
            </button>
            <p>{isEs
              ? "Opcional: supuestos hipotéticos para mostrar cómo cambia la comparación. No son mediciones ni promedios estadísticos regionales."
              : "Optional hypothetical assumptions to explore trade-offs. Neither measurements nor statistical regional averages."}</p>
            {!presetConfirmed && <p role="status">{isEs ? "Primero confirma el lugar de ejemplo." : "Confirm the example location first."}</p>}
          </div>
        )}
      </div>

      {/* Parameters Grid */}
      <div className="field-shift-grid">
        <div className="field-shift-control">
          <label htmlFor="fs-season">{isEs ? "Ventana estacional:" : "Seasonal window:"}</label>
          <select
            id="fs-season"
            value={season}
            onChange={(e) => setSeason(e.target.value as typeof season)}
          >
            <option value="apr_sep">
              {isEs ? "Abril–Septiembre (Otoño/Invierno)" : "April–September (Austral Fall/Winter)"}
            </option>
            <option value="oct_mar">
              {isEs ? "Octubre–Marzo (Primavera/Verano)" : "October–March (Austral Spring/Summer)"}
            </option>
          </select>
        </div>

        <div className="field-shift-control">
          <label htmlFor="fs-concern">{isEs ? "¿Qué quieres explorar?" : "What would you like to explore?"}</label>
          <select id="fs-concern" value={concern} onChange={(e) => setConcern(e.target.value as typeof concern)}>
            <option value="dry">{isEs ? "Déficit hídrico" : "Water deficit"}</option>
            <option value="wet">{isEs ? "Exceso de humedad" : "Excess rainfall"}</option>
            <option value="balanced">{isEs ? "Ambos contextos" : "Both conditions"}</option>
          </select>
        </div>
        <div className="field-shift-control">
          <label htmlFor="fs-drainage">{isEs ? "Drenaje del suelo:" : "Soil drainage:"}</label>
          <select
            id="fs-drainage"
            value={drainage}
            onChange={(e) => { setDrainage(e.target.value as typeof drainage); setDrainageOrigin("self_reported"); }}
          >
            <option value="unknown">{isEs ? "Desconocido / Sin medir" : "Unknown / Unmeasured"}</option>
            <option value="well_drained">{isEs ? "Bien drenado" : "Well drained"}</option>
            <option value="restricted">{isEs ? "Restringido / Lento" : "Restricted / Impeded"}</option>
          </select>
        </div>

        <div className="field-shift-control">
          <label htmlFor="fs-soil">{isEs ? "Textura del suelo:" : "Soil texture:"}</label>
          <select
            id="fs-soil"
            value={soil}
            onChange={(e) => { setSoil(e.target.value as typeof soil); setSoilOrigin("self_reported"); }}
          >
            <option value="unknown">{isEs ? "Desconocida" : "Unknown"}</option>
            <option value="clayey">{isEs ? "Arcilloso (retentivo/lento)" : "Clayey (retentive/slow)"}</option>
            <option value="sandy">{isEs ? "Arenoso (drenaje rápido)" : "Sandy (fast drainage)"}</option>
            <option value="loamy">{isEs ? "Franco (equilibrado)" : "Loamy (balanced)"}</option>
          </select>
        </div>

        <div className="field-shift-control">
          <label htmlFor="fs-priority">{isEs ? "Prioridad del agricultor:" : "Farmer priority:"}</label>
          <select
            id="fs-priority"
            value={priority}
            onChange={(e) => setPriority(e.target.value as typeof priority)}
          >
            <option value="water">{isEs ? "Gestión del agua" : "Water management"}</option>
            <option value="soil">{isEs ? "Cobertura y salud del suelo" : "Soil cover & conservation"}</option>
            <option value="diversity">{isEs ? "Diversidad de rotación" : "Crop rotation diversity"}</option>
          </select>
        </div>
      </div>

      <p className="field-shift-method">
        {isEs
          ? (soilOrigin === "illustrative_demo" || drainageOrigin === "illustrative_demo" ? "Perfil de ejemplo activo: condiciones hipotéticas, no observadas ni representativas de la región." : "Condiciones declaradas por ti o desconocidas: aún sin verificación de terreno.")
          : (soilOrigin === "illustrative_demo" || drainageOrigin === "illustrative_demo" ? "Example profile active: hypothetical conditions, neither observed nor representative of the region." : "Conditions you reported or left unknown; not field-verified.")}
      </p>
      <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
        <button
          type="button"
          className="field-shift-action-btn"
          onClick={handleRunEvaluation}
          disabled={!point || !csrfToken || loading || !presetConfirmed}
        >
          {loading ? (isEs ? "Consultando NASA POWER..." : "Querying NASA POWER...") : (isEs ? "Evaluar alternativas con NASA" : "Evaluate alternatives with NASA")}
        </button>

        {point && (
          <span style={{ fontSize: "0.8rem", color: "var(--qs-muted, #718096)" }}>
            {isEs ? "Punto:" : "Target:"} <strong>{point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}</strong>
          </span>
        )}
      </div>

      {selectedPreset && !presetConfirmed && (
        <p className="field-shift-method" role="status">
          {isEs ? "Confirma el nuevo punto antes de evaluar; no se reutilizan resultados del lugar anterior." : "Confirm the new point before evaluation; previous-place results are not reused."}
        </p>
      )}
      {!point && (
        <p className="field-shift-method" role="status">
          {isEs ? "Confirma primero el territorio seleccionado para habilitar la evaluación." : "Confirm your selected place before running the evaluation."}
        </p>
      )}

      {errorMsg && (
        <div style={{ marginTop: "0.75rem", padding: "0.5rem 0.75rem", background: "rgba(229, 62, 62, 0.1)", color: "#c53030", borderRadius: 4, fontSize: "0.8rem" }}>
          {errorMsg}
        </div>
      )}

      {evaluation && evaluation.status !== "historical_evidence_available" && (
        <div className="field-shift-status" role="status">
          <strong>{isEs ? "Evidencia histórica no disponible" : "Historical evidence unavailable"}</strong>
          <p>{isEs ? "NASA POWER no entregó una serie suficiente y validada. No se muestran índices ni comparaciones sin evidencia." : "NASA POWER did not provide a sufficient validated series. No indices or comparisons are displayed without evidence."}</p>
        </div>
      )}

      {/* Results View */}
      {evaluation && evaluation.status === "historical_evidence_available" && evaluation.historical_context && (
        <div className="field-shift-results">
          <div className="field-shift-evidence-strip">
            <strong>{isEs ? "Contexto histórico, no pronóstico" : "Historical context, not a forecast"}</strong>
            <span>{evaluation.provenance.period_start ?? "2021-01-01"} – {evaluation.provenance.period_end ?? "2025-12-31"}</span>
            <span>{isEs ? "Estimaciones meteorológicas de celdas NASA, no sensores de parcela." : "NASA gridded weather estimates, not parcel sensors."}</span>
            {evaluation.quality && <span>{isEs ? "Días disponibles" : "Available days"}: {evaluation.quality.available_days}/{evaluation.quality.requested_days}</span>}
          </div>
          {/* Seasonal KPI Bar */}
          <div className="seasonal-kpi-bar">
            <div className="kpi-item">
              <span className="kpi-val">{evaluation.historical_context.mean_rainfall_mm} mm</span>
              <span className="kpi-lbl">{isEs ? "Precipitación estacional media" : "Mean seasonal rainfall"}</span>
            </div>
            <div className="kpi-item">
              <span className="kpi-val">{(evaluation.historical_context.dry_day_fraction * 100).toFixed(1)}%</span>
              <span className="kpi-lbl">{isEs ? "Días secos (<1mm/día)" : "Dry days share (<1mm/d)"}</span>
            </div>
            <div className="kpi-item">
              <span className="kpi-val">{evaluation.historical_context.mean_heavy_rain_days}</span>
              <span className="kpi-lbl">{isEs ? "Días con lluvia >=20mm" : "Days with rain >=20mm"}</span>
            </div>
            <div className="kpi-item">
              <span className="kpi-val">{evaluation.historical_context.mean_temperature_c} °C</span>
              <span className="kpi-lbl">{isEs ? "Temperatura media 2m" : "Mean 2m temperature"}</span>
            </div>
            <div className="kpi-item">
              <span className="kpi-val">{evaluation.historical_context.count} {isEs ? "años" : "yrs"}</span>
              <span className="kpi-lbl">{isEs ? "Temporadas completas" : "Complete seasons"}</span>
            </div>
          </div>

          <div className="field-shift-season-chart" aria-label={isEs ? "Precipitación por temporada histórica" : "Rainfall by historical season"}>
            <h4>{isEs ? "Cómo varió la lluvia entre temporadas" : "How rainfall varied between seasons"}</h4>
            <div className="field-shift-season-bars">
              {evaluation.historical_context.sample.map((sample) => {
                const peak = Math.max(1, ...evaluation.historical_context!.sample.map((entry) => entry.precipitation_mm));
                return (
                  <div className="field-shift-season-row" key={sample.season_year}>
                    <span>{sample.season_year}{season === "oct_mar" ? "–" + String(sample.season_year + 1).slice(-2) : ""}</span>
                    <div className="field-shift-season-track" role="img" aria-label={isEs ? String(sample.precipitation_mm) + " milímetros" : String(sample.precipitation_mm) + " millimetres"}>
                      <div style={{ width: String((sample.precipitation_mm / peak) * 100) + "%" }} />
                    </div>
                    <span>{sample.precipitation_mm} mm</span>
                  </div>
                );
              })}
            </div>
            <p>{isEs ? "Totales históricos por temporada completa. La diferencia entre barras no pronostica la lluvia futura." : "Historical totals for complete seasons. Differences between bars do not forecast future rainfall."}</p>
          </div>
          <p className="field-shift-method">
            {isEs ? "Los valores 0–100 que siguen son índices comparativos construidos con reglas declaradas: NO son probabilidades, predicciones de rendimiento ni mediciones de suelo." : "The following 0–100 values are rule-based comparative indices, NOT probabilities, yield forecasts or measured soil conditions."}
          </p>
          {/* Pathways List */}
          <div className="pathways-list">
            <h4 style={{ margin: "0.5rem 0 0.25rem", fontSize: "0.9rem", fontWeight: 700 }}>
              {isEs ? "Comparación exploratoria de rotaciones:" : "Exploratory rotation comparison:"}
            </h4>

            {evaluation.pathways.map((plan) => (
              <article key={plan.id} className="pathway-card">
                <div className="pathway-head">
                  <span className="pathway-name">{isEs ? PATHWAY_ES[plan.id] ?? plan.name : plan.name}</span>
                  <span style={{ fontSize: "0.72rem", background: "rgba(0,0,0,0.05)", padding: "0.2rem 0.4rem", borderRadius: 4 }}>
                    {isEs ? "Viabilidad agronómica:" : "Agronomic viability:"} <strong>{isEs ? "No evaluada" : "Not assessed"}</strong>
                  </span>
                </div>

                <div className="pathway-sequence">
                  {plan.sequence.map((crop, idx) => (
                    <span key={idx} className="seq-tag">
                      {idx + 1}. {isEs ? CROP_ES[crop] ?? crop : crop}
                    </span>
                  ))}
                </div>

                <div className="indicator-bar-container">
                  <span style={{ width: 120 }}>{isEs ? "Índice de exposición a sequedad:" : "Dry-exposure index:"}</span>
                  <div className="progress-track">
                    <div
                      className="progress-fill fill-dry"
                      style={{ width: `${plan.dry_exposure_indicator}%` }}
                    />
                  </div>
                  <span style={{ width: 35, textAlign: "right" }}>{plan.dry_exposure_indicator}/100</span>
                </div>

                {plan.wet_exposure_indicator !== null && (
                  <div className="indicator-bar-container">
                    <span style={{ width: 120 }}>{isEs ? "Índice de exposición a humedad:" : "Wet-exposure index:"}</span>
                    <div className="progress-track">
                      <div
                        className="progress-fill fill-wet"
                        style={{ width: `${plan.wet_exposure_indicator}%` }}
                      />
                    </div>
                    <span style={{ width: 35, textAlign: "right" }}>{plan.wet_exposure_indicator}/100</span>
                  </div>
                )}

                <ul className="pathway-obs">
                  {(isEs && plan.observations_es?.length ? plan.observations_es : plan.observations).map((obs, i) => (
                    <li key={i}>{obs}</li>
                  ))}
                </ul>
                <p className="field-shift-method">{isEs ? plan.limitation_es ?? plan.limitation : plan.limitation}</p>
              </article>
            ))}
          </div>

          {/* Scientific Provenance Note */}
          <footer className="provenance-note">
            <div>
              <strong>{isEs ? "Procedencia de datos:" : "Data provenance:"}</strong> {evaluation.provenance.provider} ({evaluation.provenance.dataset}) · {evaluation.provenance.time_standard} ·{" "}
              <a href={evaluation.provenance.source_url} target="_blank" rel="noopener noreferrer">
                {isEs ? "Consulta NASA POWER" : "NASA POWER source request"}
              </a>
            </div>
            <div style={{ marginTop: "0.2rem" }}>
              {isEs ? "Estimaciones de una celda meteorológica histórica; no son mediciones de parcela, pronósticos estacionales ni una evaluación de aptitud agronómica." : evaluation.provenance.limitation}
            </div>
          </footer>
        </div>
      )}
    </section>
  );
}
