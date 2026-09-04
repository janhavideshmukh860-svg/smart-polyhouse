/**
 * Centralized Smart Polyhouse API client.
 * All backend communication goes through here — base URL, auth token,
 * headers, parsing and error handling live in one place.
 */

export const API_BASE_URL: string =
  (import.meta.env['VITE_API_BASE_URL'] as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000/api/v1";

const TOKEN_KEY = "sp_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  formData?: FormData;
  query?: Record<string, string | number | boolean | undefined | null>;
  auth?: boolean;
};

function buildUrl(path: string, query?: RequestOptions["query"]) {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    }
  }
  return url.toString();
}

export async function apiRequest<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, formData, query, auth = true } = opts;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: formData ?? (body !== undefined ? JSON.stringify(body) : null),
    });
  } catch {
    throw new ApiError(
      `Cannot reach the Smart Polyhouse backend at ${API_BASE_URL}. Make sure it is running.`,
      0,
    );
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    const envelope = data as { error?: { message?: string }; detail?: unknown } | null;
    const message =
      envelope?.error?.message ??
      (typeof envelope?.detail === "string" ? envelope.detail : undefined) ??
      `Request failed (${res.status})`;
    if (res.status === 401) setToken(null);
    throw new ApiError(message, res.status);
  }

  return data as T;
}

/* ------------------------------------------------------------------ */
/* Types mirroring the real FastAPI response schemas                    */
/* ------------------------------------------------------------------ */

export type UserRole = "farmer" | "agronomist" | "admin";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_minutes: number;
}

export interface Polyhouse {
  id: string;
  farm_id: string;
  name: string;
  area_sq_m: number | null;
  external_sensor_reference: string | null;
  created_at: string;
}

export interface Farm {
  id: string;
  owner_id: string;
  name: string;
  location_label: string | null;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
  polyhouses?: Polyhouse[];
}

export interface SensorReading {
  id: string;
  polyhouse_id: string;
  recorded_at: string;
  raw_capacitive_adc: number | null;
  sensor_voltage_v: number | null;
  sensor_board_temperature_c: number | null;
  atm_pressure_inhg: number | null;
  atm_temperature_c: number | null;
  soil_temperature_c: number | null;
  volumetric_moisture_pct: number | null;
  created_at: string;
}

export interface Alert {
  id: string;
  polyhouse_id: string | null;
  alert_type: string;
  severity: "low" | "medium" | "high" | "critical" | string;
  status: "active" | "acknowledged" | "resolved" | string;
  message: string;
  source_reference: Record<string, unknown> | null;
  created_at: string;
  resolved_at: string | null;
}

export interface Recommendation {
  id: string;
  polyhouse_id: string | null;
  domain: string;
  status: string;
  urgency: string;
  recommendation_text: string;
  reason: string;
  risk_factors: string[] | null;
  inputs_snapshot: Record<string, unknown> | null;
  model_confidence: number | null;
  created_at: string;
}

export interface ModelStatusEntry {
  status: string;
  model_type: string | null;
  version: string | null;
  metrics: Record<string, unknown> | null;
  horizons: string[] | null;
  detail: string | null;
}

export interface ModelsStatusResponse {
  irrigation_calibration: ModelStatusEntry;
  irrigation_forecasting: ModelStatusEntry;
  disease: ModelStatusEntry;
}

export interface DashboardResponse {
  polyhouse_id: string | null;
  generated_at: string;
  sensor_state: {
    available: boolean;
    recorded_at?: string | null;
    volumetric_moisture_pct?: number | null;
    soil_temperature_c?: number | null;
    atm_temperature_c?: number | null;
    detail?: string | null;
  };
  irrigation: {
    available: boolean;
    current_moisture?: number | null;
    forecast?: Record<string, number> | null;
    status?: string | null;
    urgency?: string | null;
    recommendation?: string | null;
    detail?: string | null;
  };
  disease: {
    status: string;
    latest_prediction?: Record<string, unknown> | null;
    detail?: string | null;
  };
  active_alerts: Alert[];
  recent_recommendations_count: number;
  model_status: ModelsStatusResponse;
  data_freshness_minutes: number | null;
}

export interface ForecastFeatures {
  Farm_ID: string;
  Volumetric_Moisture_Pct: number;
  Sensor_Board_Temperature_C: number;
  Raw_Capacitive_ADC: number;
  Sensor_Voltage_V: number;
  Atm_Pressure_inHg: number;
  Atm_Temperature_C: number;
  Soil_Temperature_C: number;
  SM_Level_15cm: number;
  SM_Volume_15cm: number;
  SM_Aggregate_Pct: number;
  SM_Volume_Pct: number;
  Hour: number;
  Day: number;
  Month: number;
  DayOfWeek: number;
  DayOfYear: number;
  Hour_sin: number;
  Hour_cos: number;
  Day_sin: number;
  Day_cos: number;
}

export interface ModelInfo {
  name: string;
  version: string;
  task: string;
  status: string;
}

export interface ForecastPredictResponse {
  reference_time: string;
  current_moisture_pct: number;
  forecast_1h: number;
  forecast_6h: number;
  forecast_12h: number;
  forecast_24h: number;
  models: Record<string, ModelInfo>;
}

export interface IrrigationDecisionResponse {
  recommendation_id: string | null;
  status: string;
  urgency: string;
  current_moisture: number;
  forecast: Record<string, number>;
  recommendation: string;
  reason: string;
  risk_factors: string[];
  model_confidence: number | null;
  generated_at: string;
}

export interface DiseasePredictionResult {
  class: string;
  confidence: number;
  canonical_crop: string | null;
  canonical_disease: string | null;
}

export interface DiseasePredictionResponse {
  prediction: DiseasePredictionResult;
  top_k: DiseasePredictionResult[];
  model: ModelInfo;
}

export interface DiseaseStatusResponse {
  status: "MODEL_AVAILABLE" | "MODEL_NOT_TRAINED" | string;
  model_type?: string | null;
  version?: string | null;
  message?: string;
}

/* ------------------------------------------------------------------ */
/* Endpoint wrappers — one function per real FastAPI route              */
/* ------------------------------------------------------------------ */

export const api = {
  // Auth
  register: (payload: { email: string; password: string; full_name?: string | undefined }) =>
    apiRequest<User>("/auth/register", { method: "POST", body: payload, auth: false }),
  login: (payload: { email: string; password: string }) =>
    apiRequest<TokenResponse>("/auth/login", { method: "POST", body: payload, auth: false }),
  me: () => apiRequest<User>("/auth/me"),

  // Farms & polyhouses
  listFarms: () => apiRequest<{ total: number; farms: Farm[] }>("/farms"),
  createFarm: (payload: { name: string; location_label?: string }) =>
    apiRequest<Farm>("/farms", { method: "POST", body: payload }),
  createPolyhouse: (farmId: string, payload: { name: string; area_sq_m?: number }) =>
    apiRequest<Polyhouse>(`/farms/${farmId}/polyhouses`, { method: "POST", body: payload }),

  // Sensors
  sensorHistory: (polyhouseId: string, limit = 100) =>
    apiRequest<{ total: number; readings: SensorReading[] }>(`/sensors/readings/${polyhouseId}`, {
      query: { limit },
    }),
  latestReading: (polyhouseId: string) =>
    apiRequest<SensorReading>(`/sensors/readings/${polyhouseId}/latest`),
  ingestReading: (payload: Record<string, unknown>) =>
    apiRequest<SensorReading>("/sensors/readings", { method: "POST", body: payload }),

  // Dashboard
  dashboard: (polyhouseId: string) => apiRequest<DashboardResponse>(`/dashboard/${polyhouseId}`),

  // Irrigation / forecasting
  forecast: (features: ForecastFeatures) =>
    apiRequest<ForecastPredictResponse>("/irrigation/predict", { method: "POST", body: features }),
  decision: (features: ForecastFeatures & { polyhouse_id?: string }) =>
    apiRequest<IrrigationDecisionResponse>("/irrigation/decision", {
      method: "POST",
      body: features,
    }),

  // Recommendations
  listRecommendations: (polyhouseId?: string, limit = 50, domain?: string) =>
    apiRequest<{ total: number; recommendations: Recommendation[] }>("/recommendations", {
      query: { polyhouse_id: polyhouseId, limit, domain },
    }),

  // Alerts
  listAlerts: (polyhouseId?: string, activeOnly = true, limit = 50) =>
    apiRequest<{ total: number; alerts: Alert[] }>("/alerts", {
      query: { polyhouse_id: polyhouseId, active_only: activeOnly, limit },
    }),
  acknowledgeAlert: (id: string) => apiRequest<Alert>(`/alerts/${id}/acknowledge`, { method: "POST" }),
  resolveAlert: (id: string) => apiRequest<Alert>(`/alerts/${id}/resolve`, { method: "POST" }),

  // Models
  modelsStatus: () => apiRequest<ModelsStatusResponse>("/models/status", { auth: false }),

  // Disease
  diseaseStatus: () => apiRequest<DiseaseStatusResponse>("/disease/status", { auth: false }),
  diseaseClasses: () =>
    apiRequest<{
      total_classes: number;
      total_crops: number;
      classes: { final_class: string; canonical_crop: string; canonical_disease: string }[];
    }>("/disease/classes", { auth: false }),
  diseasePredict: (file: File, polyhouseId?: string, topK = 3) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiRequest<DiseasePredictionResponse>("/disease/predict", {
      method: "POST",
      formData: fd,
      query: { top_k: topK, polyhouse_id: polyhouseId },
    });
  },
  diseaseHistory: (polyhouseId: string, limit = 50) =>
    apiRequest<{
      total: number;
      predictions: {
        id: string;
        predicted_class: string;
        confidence: number;
        canonical_crop: string | null;
        canonical_disease: string | null;
        created_at: string;
      }[];
    }>(`/disease/history/${polyhouseId}`, { query: { limit } }),
};
