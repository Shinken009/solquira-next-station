import { useState, useCallback } from "react";
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
  limitation: string;
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
    time_standard?: string;
    units: Record<string, string>;
    limitation: string;
  };
  disclaimers: string[];
}

const PRESETS = [
  {
    id: "coquimbo",
    name: "Coquimbo",
    description: "Déficit hídrico & secano semiárido",
    lat: -30.0400,
    lon: -71.2500,
    concern: "dry",
    soil: "sandy",
    drainage: "well_drained",
  },
  {
    id: "maule",
    name: "Maule",
    description: "Transición mediterránea & rotación",
    lat: -35.4300,
    lon: -71.6600,
    concern: "dry",
    soil: "loamy",
    drainage: "well_drained",
  },
  {
    id: "chiloe",
    name: "Chiloé",
    description: "Paisaje húmedo & drenaje superficial",
    lat: -42.4800,
    lon: -73.7600,
    concern: "wet",
    soil: "clayey",
    drainage: "restricted",
  },
];

export function FieldShiftJourney({ point, csrfToken, onSelectPreset }: FieldShiftJourneyProps) {
  const { locale } = useStudioPreferences();
  const isEs = locale === "es";

  const [activePreset, setActivePreset] = useState<string | null>(null);
  const [season, setSeason] = useState<"apr_sep" | "oct_mar">("apr_sep");
  const [drainage, setDrainage] = useState<"well_drained" | "restricted" | "unknown">("unknown");
  const [soil, setSoil] = useState<"clayey" | "sandy" | "loamy" | "unknown">("unknown");
  const [priority, setPriority] = useState<"water" | "soil" | "diversity">("water");
  const [concern, setConcern] = useState<"dry" | "wet" | "balanced">("dry");

  const [loading, setLoading] = useState(false);
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleApplyPreset = (p: typeof PRESETS[0]) => {
    setActivePreset(p.id);
    setConcern(p.concern as any);
    setSoil(p.soil as any);
    setDrainage(p.drainage as any);
    if (onSelectPreset) {
      onSelectPreset(p.lat, p.lon);
    }
  };

  const handleRunEvaluation = useCallback(async () => {
    if (!point) return;
    setLoading(true);
    setErrorMsg(null);

    const payload = {
      latitude: point.latitude,
      longitude: point.longitude,
      season,
      drainage,
      soil,
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
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data: EvaluationResponse = await res.json();
      setEvaluation(data);
    } catch (err: any) {
      setErrorMsg(
        isEs
          ? "No se pudo conectar con el adaptador de NASA POWER. Se mantiene la política fail-closed."
          : "Could not reach NASA POWER adapter. Fail-closed policy active; no synthetic data."
      );
    } finally {
      setLoading(false);
    }
  }, [point, season, drainage, soil, priority, concern, csrfToken, isEs]);

  return (
    <section className="field-shift-card" aria-label="Field Shift Decision Support">
      <header className="field-shift-header">
        <div>
          <h3 style={{ margin: 0, fontSize: "1.05rem", fontWeight: 700 }}>
            {isEs ? "Field Shift — Decisión Estacional" : "Field Shift — Seasonal Adaptation"}
          </h3>
          <p style={{ margin: "0.2rem 0 0", fontSize: "0.8rem", color: "var(--qs-muted, #718096)" }}>
            {isEs
              ? "Observaciones históricas NASA POWER vinculadas a decisiones de manejo y rotación."
              : "Historical NASA POWER observations tied to field management and rotation choices."}
          </p>
        </div>
        <span className="field-shift-badge">NASA Space Apps 2026</span>
      </header>

      {/* Preset Territorials */}
      <div style={{ marginBottom: "0.75rem" }}>
        <div style={{ fontSize: "0.78rem", fontWeight: 600, marginBottom: "0.35rem" }}>
          {isEs ? "Territorios demostrativos de inicio rápido:" : "Rapid exploration presets:"}
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
              <strong>{p.name}</strong> · <span style={{ fontSize: "0.75rem" }}>{p.description}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Parameters Grid */}
      <div className="field-shift-grid">
        <div className="field-shift-control">
          <label htmlFor="fs-season">{isEs ? "Ventana estacional:" : "Seasonal window:"}</label>
          <select
            id="fs-season"
            value={season}
            onChange={(e) => setSeason(e.target.value as any)}
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
          <label htmlFor="fs-drainage">{isEs ? "Drenaje de suelo (auto-reportado):" : "Soil drainage (self-reported):"}</label>
          <select
            id="fs-drainage"
            value={drainage}
            onChange={(e) => setDrainage(e.target.value as any)}
          >
            <option value="unknown">{isEs ? "Desconocido / Sin medir" : "Unknown / Unmeasured"}</option>
            <option value="well_drained">{isEs ? "Bien drenado" : "Well drained"}</option>
            <option value="restricted">{isEs ? "Restringido / Lento" : "Restricted / Impeded"}</option>
          </select>
        </div>

        <div className="field-shift-control">
          <label htmlFor="fs-soil">{isEs ? "Textura del suelo (auto-reportada):" : "Soil texture (self-reported):"}</label>
          <select
            id="fs-soil"
            value={soil}
            onChange={(e) => setSoil(e.target.value as any)}
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
            onChange={(e) => setPriority(e.target.value as any)}
          >
            <option value="water">{isEs ? "Resiliencia hídrica (déficit)" : "Water resilience (deficit)"}</option>
            <option value="soil">{isEs ? "Cobertura y salud del suelo" : "Soil cover & conservation"}</option>
            <option value="diversity">{isEs ? "Diversidad de rotación" : "Crop rotation diversity"}</option>
          </select>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <button
          type="button"
          className="field-shift-action-btn"
          onClick={handleRunEvaluation}
          disabled={!point || loading}
        >
          {loading ? (isEs ? "Consultando NASA POWER..." : "Querying NASA POWER...") : (isEs ? "Evaluar alternativas con NASA" : "Evaluate alternatives with NASA")}
        </button>

        {point && (
          <span style={{ fontSize: "0.8rem", color: "var(--qs-muted, #718096)" }}>
            {isEs ? "Punto:" : "Target:"} <strong>{point.latitude.toFixed(4)}, {point.longitude.toFixed(4)}</strong>
          </span>
        )}
      </div>

      {errorMsg && (
        <div style={{ marginTop: "0.75rem", padding: "0.5rem 0.75rem", background: "rgba(229, 62, 62, 0.1)", color: "#c53030", borderRadius: 4, fontSize: "0.8rem" }}>
          {errorMsg}
        </div>
      )}

      {/* Results View */}
      {evaluation && evaluation.historical_context && (
        <div className="field-shift-results">
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
              <span className="kpi-lbl">{isEs ? "Ventanas 100% completas" : "100% complete windows"}</span>
            </div>
          </div>

          {/* Pathways List */}
          <div className="pathways-list">
            <h4 style={{ margin: "0.5rem 0 0.25rem", fontSize: "0.9rem", fontWeight: 700 }}>
              {isEs ? "Comparación exploratoria de rotaciones:" : "Exploratory rotation comparison:"}
            </h4>

            {evaluation.pathways.map((plan) => (
              <article key={plan.id} className="pathway-card">
                <div className="pathway-head">
                  <span className="pathway-name">{plan.name}</span>
                  <span style={{ fontSize: "0.72rem", background: "rgba(0,0,0,0.05)", padding: "0.2rem 0.4rem", borderRadius: 4 }}>
                    {isEs ? "Viabilidad agronómica:" : "Agronomic viability:"} <strong>{isEs ? "No evaluada" : "Not assessed"}</strong>
                  </span>
                </div>

                <div className="pathway-sequence">
                  {plan.sequence.map((crop, idx) => (
                    <span key={idx} className="seq-tag">
                      {idx + 1}. {crop}
                    </span>
                  ))}
                </div>

                <div className="indicator-bar-container">
                  <span style={{ width: 120 }}>{isEs ? "Déficit hídrico:" : "Drought exposure:"}</span>
                  <div className="progress-track">
                    <div
                      className="progress-fill fill-dry"
                      style={{ width: `${plan.dry_exposure_indicator}%` }}
                    />
                  </div>
                  <span style={{ width: 35, textAlign: "right" }}>{plan.dry_exposure_indicator}%</span>
                </div>

                {plan.wet_exposure_indicator !== null && (
                  <div className="indicator-bar-container">
                    <span style={{ width: 120 }}>{isEs ? "Anegamiento:" : "Wet soil exposure:"}</span>
                    <div className="progress-track">
                      <div
                        className="progress-fill fill-wet"
                        style={{ width: `${plan.wet_exposure_indicator}%` }}
                      />
                    </div>
                    <span style={{ width: 35, textAlign: "right" }}>{plan.wet_exposure_indicator}%</span>
                  </div>
                )}

                <ul className="pathway-obs">
                  {plan.observations.map((obs, i) => (
                    <li key={i}>{obs}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>

          {/* Scientific Provenance Note */}
          <footer className="provenance-note">
            <div>
              <strong>{isEs ? "Procedencia de datos:" : "Data provenance:"}</strong> {evaluation.provenance.provider} ({evaluation.provenance.dataset}) · {evaluation.provenance.time_standard} ·{" "}
              <a href={evaluation.provenance.source_url} target="_blank" rel="noopener noreferrer">
                NASA POWER API Doc
              </a>
            </div>
            <div style={{ marginTop: "0.2rem" }}>
              {evaluation.provenance.limitation}
            </div>
          </footer>
        </div>
      )}
    </section>
  );
}
