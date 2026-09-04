/**
 * DEMO MODE — Synthetic demonstration data for hackathon recording.
 *
 * When DEMO_MODE is true the frontend uses this predetermined data
 * instead of calling the real backend / ML pipeline.  The real API
 * layer (src/lib/api.ts) is completely preserved and will be used
 * when DEMO_MODE is set to false.
 *
 * To disable demo mode and use the real backend:
 *   Set DEMO_MODE = false below.
 */

import type {
  Alert,
  DashboardResponse,
  DiseaseStatusResponse,
  DiseasePredictionResponse,
  ForecastPredictResponse,
  IrrigationDecisionResponse,
  ModelsStatusResponse,
  Recommendation,
  SensorReading,
  User,
  Farm,
  Polyhouse,
} from "./api";

// ═══════════════════════════════════════════════════
// MASTER TOGGLE
// ═══════════════════════════════════════════════════
export const DEMO_MODE = true;
export const DEMO_BADGE = "DEMO MODE · SYNTHETIC ANALYSIS";

// ═══════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════
function hoursAgo(h: number): string {
  return new Date(Date.now() - h * 3_600_000).toISOString();
}
function minutesAgo(m: number): string {
  return new Date(Date.now() - m * 60_000).toISOString();
}

// ═══════════════════════════════════════════════════
// USER / FARM / POLYHOUSE
// ═══════════════════════════════════════════════════
export const demoUser: User = {
  id: "demo-user-1",
  email: "demo@smartpolyhouse.io",
  full_name: "Demo Operator",
  role: "farmer",
  is_active: true,
  created_at: hoursAgo(720),
};

export const demoPolyhouse: Polyhouse = {
  id: "demo-ph-1",
  farm_id: "demo-farm-1",
  name: "Demo Polyhouse",
  area_sq_m: 500,
  external_sensor_reference: null,
  created_at: hoursAgo(720),
};

export const demoFarm: Farm = {
  id: "demo-farm-1",
  owner_id: "demo-user-1",
  name: "Demo Farm",
  location_label: "Smart Agriculture Research Center",
  latitude: 18.52,
  longitude: 73.85,
  created_at: hoursAgo(720),
  polyhouses: [demoPolyhouse],
};

// ═══════════════════════════════════════════════════
// DISEASE DETECTION
// ═══════════════════════════════════════════════════
export const demoDiseaseStatus: DiseaseStatusResponse = {
  status: "MODEL_AVAILABLE",
  model_type: "CNN",
  version: "v1.0-demo",
  message: "Demo mode — synthetic classification active.",
};

export const demoPredictionResponse: DiseasePredictionResponse = {
  prediction: {
    class: "Cercospora Leaf Spot",
    confidence: 0.94,
    canonical_crop: "General Foliage",
    canonical_disease: "Cercospora Leaf Spot",
  },
  top_k: [
    { class: "Cercospora Leaf Spot", confidence: 0.94, canonical_crop: "General Foliage", canonical_disease: "Cercospora Leaf Spot" },
    { class: "Leaf Blight", confidence: 0.03, canonical_crop: "General Foliage", canonical_disease: "Leaf Blight" },
    { class: "Healthy", confidence: 0.02, canonical_crop: "General Foliage", canonical_disease: null },
  ],
  model: {
    name: "Disease Detection Model",
    version: "v1.0-demo",
    task: "image_classification",
    status: "READY",
  },
};

/** Extended disease information for demo UI — not part of real API schema. */
export const demoDiseaseInfo = {
  disease_name: "Cercospora Leaf Spot",
  classification: "Disease Detected",
  confidence: 0.94,
  severity: "Moderate",
  analysisStatus: "Analysis Complete",
  cause:
    "Favorable conditions such as elevated humidity, prolonged leaf moisture, limited airflow, and environmental stress can contribute to the development and spread of leaf-spot diseases.",
  treatment:
    "Remove severely affected leaves, improve airflow around the crop, avoid unnecessary leaf wetness, and follow locally approved plant-disease treatment guidance.",
  treatmentType:
    "Fungicidal treatment may be considered under agricultural expert guidance.",
  prevention: [
    "Maintain proper greenhouse ventilation",
    "Avoid excessive moisture on foliage",
    "Prefer appropriate irrigation practices that minimize unnecessary leaf wetness",
    "Maintain adequate spacing between plants",
    "Remove severely affected plant material",
    "Regularly inspect nearby plants",
    "Monitor greenhouse humidity",
    "Maintain good crop hygiene",
  ],
};

export const demoDiseaseHistory = {
  total: 3,
  predictions: [
    {
      id: "demo-dh-1",
      predicted_class: "Cercospora Leaf Spot",
      confidence: 0.94,
      canonical_crop: "General Foliage",
      canonical_disease: "Cercospora Leaf Spot",
      created_at: minutesAgo(5),
    },
    {
      id: "demo-dh-2",
      predicted_class: "Healthy Leaf",
      confidence: 0.97,
      canonical_crop: "General Foliage",
      canonical_disease: null,
      created_at: hoursAgo(24),
    },
    {
      id: "demo-dh-3",
      predicted_class: "Leaf Spot",
      confidence: 0.88,
      canonical_crop: "General Foliage",
      canonical_disease: "Leaf Spot",
      created_at: hoursAgo(48),
    },
  ],
};

// ═══════════════════════════════════════════════════
// SENSORS
// ═══════════════════════════════════════════════════
export const demoLatestSensor: SensorReading = {
  id: "demo-sr-1",
  polyhouse_id: "demo-ph-1",
  recorded_at: minutesAgo(1),
  raw_capacitive_adc: 420,
  sensor_voltage_v: 3.28,
  sensor_board_temperature_c: 27.5,
  atm_pressure_inhg: 29.92,
  atm_temperature_c: 28.0,
  soil_temperature_c: 26.5,
  volumetric_moisture_pct: 68.0,
  created_at: minutesAgo(1),
};

/** Additional sensor display values for demo (not in real SensorReading schema). */
export const demoSensorExtras = {
  humidity: 72,
  lightIntensity: "Good",
  co2: "Normal",
  networkStatus: "Online",
  lastUpdated: "Just now",
};

function generateDemoSensorHistory(): SensorReading[] {
  const readings: SensorReading[] = [];
  for (let i = 23; i >= 0; i--) {
    readings.push({
      id: `demo-sh-${i}`,
      polyhouse_id: "demo-ph-1",
      recorded_at: hoursAgo(i),
      raw_capacitive_adc: 400 + Math.round(Math.random() * 40),
      sensor_voltage_v: 3.2 + Math.random() * 0.15,
      sensor_board_temperature_c: 26 + Math.random() * 3,
      atm_pressure_inhg: 29.8 + Math.random() * 0.3,
      atm_temperature_c: 26 + Math.random() * 4,
      soil_temperature_c: 25 + Math.random() * 3,
      volumetric_moisture_pct: 62 + Math.random() * 12,
      created_at: hoursAgo(i),
    });
  }
  return readings;
}

export const demoSensorHistory = {
  total: 24,
  readings: generateDemoSensorHistory(),
};

// ═══════════════════════════════════════════════════
// IRRIGATION
// ═══════════════════════════════════════════════════
export const demoIrrigationDecision: IrrigationDecisionResponse = {
  recommendation_id: "demo-rec-irr-1",
  status: "optimal",
  urgency: "low",
  current_moisture: 68.0,
  forecast: { "1h": 66.5, "6h": 62.0, "12h": 58.5, "24h": 55.0 },
  recommendation:
    "No immediate irrigation required. Soil moisture is currently at 68%, which is within the optimal range. Next irrigation recommended in approximately 3 hours.",
  reason:
    "Current moisture levels are adequate for the crop growth stage. Forecast indicates gradual decline within acceptable bounds.",
  risk_factors: [],
  model_confidence: 0.91,
  generated_at: minutesAgo(2),
};

/** Additional irrigation display values for demo. */
export const demoIrrigationExtras = {
  irrigationStatus: "Optimal",
  soilMoisture: "68%",
  waterRequirement: "Moderate",
  nextIrrigation: "Approximately 3 hours",
  currentDecision: "No immediate irrigation required",
  irrigationSystem: "Online",
  dataSource: "Synthetic Demo Data",
};

// ═══════════════════════════════════════════════════
// FORECAST
// ═══════════════════════════════════════════════════
export const demoForecastResult: ForecastPredictResponse = {
  reference_time: minutesAgo(2),
  current_moisture_pct: 68.0,
  forecast_1h: 66.5,
  forecast_6h: 62.0,
  forecast_12h: 58.5,
  forecast_24h: 55.0,
  models: {
    forecast_1h: { name: "Irrigation Forecast 1h", version: "v1.0-demo", task: "regression", status: "READY" },
    forecast_6h: { name: "Irrigation Forecast 6h", version: "v1.0-demo", task: "regression", status: "READY" },
    forecast_12h: { name: "Irrigation Forecast 12h", version: "v1.0-demo", task: "regression", status: "READY" },
    forecast_24h: { name: "Irrigation Forecast 24h", version: "v1.0-demo", task: "regression", status: "READY" },
  },
};

/** Additional forecast display values for demo. */
export const demoForecastExtras = {
  temperature: "28°C",
  humidity: "72%",
  rainProbability: "30%",
  weather: "Partly Cloudy",
  forecastStatus: "Favorable",
  environmentalRisk: "Moderate",
  dataSource: "Synthetic Demo Data",
};

// ═══════════════════════════════════════════════════
// ALERTS
// ═══════════════════════════════════════════════════
export const demoAlerts: { total: number; alerts: Alert[] } = {
  total: 3,
  alerts: [
    {
      id: "demo-alert-1",
      polyhouse_id: "demo-ph-1",
      alert_type: "Disease Detected",
      severity: "medium",
      status: "active",
      message: "Leaf-spot symptoms detected during demo image analysis.",
      source_reference: null,
      created_at: minutesAgo(5),
      resolved_at: null,
    },
    {
      id: "demo-alert-2",
      polyhouse_id: "demo-ph-1",
      alert_type: "Humidity Elevated",
      severity: "low",
      status: "active",
      message: "Greenhouse humidity is currently above the preferred monitoring range.",
      source_reference: null,
      created_at: minutesAgo(30),
      resolved_at: null,
    },
    {
      id: "demo-alert-3",
      polyhouse_id: "demo-ph-1",
      alert_type: "Sensor Network Online",
      severity: "low",
      status: "active",
      message: "All demonstration sensors are reporting normally.",
      source_reference: null,
      created_at: hoursAgo(1),
      resolved_at: null,
    },
  ],
};

// ═══════════════════════════════════════════════════
// RECOMMENDATIONS
// ═══════════════════════════════════════════════════
export const demoRecommendations: { total: number; recommendations: Recommendation[] } = {
  total: 6,
  recommendations: [
    {
      id: "demo-rec-1",
      polyhouse_id: "demo-ph-1",
      domain: "disease",
      status: "active",
      urgency: "high",
      recommendation_text: "Improve airflow around affected plants.",
      reason: "Reduced airflow contributes to fungal disease spread.",
      risk_factors: ["leaf_spot_detected"],
      inputs_snapshot: null,
      model_confidence: 0.94,
      created_at: minutesAgo(5),
    },
    {
      id: "demo-rec-2",
      polyhouse_id: "demo-ph-1",
      domain: "disease",
      status: "active",
      urgency: "high",
      recommendation_text: "Monitor humidity regularly.",
      reason: "Elevated humidity favors disease development.",
      risk_factors: ["high_humidity"],
      inputs_snapshot: null,
      model_confidence: 0.91,
      created_at: minutesAgo(5),
    },
    {
      id: "demo-rec-3",
      polyhouse_id: "demo-ph-1",
      domain: "disease",
      status: "active",
      urgency: "medium",
      recommendation_text: "Inspect surrounding leaves for similar symptoms.",
      reason: "Early detection prevents spread to healthy plants.",
      risk_factors: null,
      inputs_snapshot: null,
      model_confidence: 0.88,
      created_at: minutesAgo(10),
    },
    {
      id: "demo-rec-4",
      polyhouse_id: "demo-ph-1",
      domain: "irrigation",
      status: "active",
      urgency: "medium",
      recommendation_text: "Maintain controlled irrigation.",
      reason: "Excessive watering increases leaf wetness and disease risk.",
      risk_factors: null,
      inputs_snapshot: null,
      model_confidence: 0.85,
      created_at: minutesAgo(15),
    },
    {
      id: "demo-rec-5",
      polyhouse_id: "demo-ph-1",
      domain: "disease",
      status: "active",
      urgency: "high",
      recommendation_text: "Remove severely affected leaves.",
      reason: "Removing infected material reduces pathogen load.",
      risk_factors: ["leaf_spot_detected"],
      inputs_snapshot: null,
      model_confidence: 0.92,
      created_at: minutesAgo(5),
    },
    {
      id: "demo-rec-6",
      polyhouse_id: "demo-ph-1",
      domain: "disease",
      status: "active",
      urgency: "low",
      recommendation_text: "Continue regular crop monitoring.",
      reason: "Ongoing observation enables early intervention.",
      risk_factors: null,
      inputs_snapshot: null,
      model_confidence: 0.80,
      created_at: minutesAgo(20),
    },
  ],
};

// ═══════════════════════════════════════════════════
// MODELS
// ═══════════════════════════════════════════════════
export const demoModelsStatus: ModelsStatusResponse = {
  irrigation_calibration: {
    status: "READY",
    model_type: "Gradient Boosted Regressor",
    version: "v1.0-demo",
    metrics: { r2_score: 0.803 },
    horizons: null,
    detail: "Synthetic Demo Mode",
  },
  irrigation_forecasting: {
    status: "READY",
    model_type: "Gradient Boosted Regressor",
    version: "v1.0-demo",
    metrics: { "1h_r2": 0.898, "6h_r2": 0.648, "12h_r2": 0.194 },
    horizons: ["1h", "6h", "12h", "24h"],
    detail: "Synthetic Demo Mode",
  },
  disease: {
    status: "READY",
    model_type: "CNN",
    version: "v1.0-demo",
    metrics: { accuracy: 0.94 },
    horizons: null,
    detail: "Synthetic Demo Mode",
  },
};

/** Extended model cards for the demo models page (4 models as requested). */
export const demoModelCards = [
  {
    name: "Disease Detection Model",
    version: "v1.0-demo",
    status: "Ready",
    mode: "Synthetic Demo",
    description: "Leaf-image classifier used by the disease analysis page.",
  },
  {
    name: "Irrigation Forecast Model",
    version: "v1.0-demo",
    status: "Ready",
    mode: "Synthetic Demo",
    description: "Per-horizon soil-moisture forecasting models (1h, 6h, 12h, 24h).",
  },
  {
    name: "Recommendation Engine",
    version: "v1.0-demo",
    status: "Ready",
    mode: "Synthetic Demo",
    description: "Generates actionable recommendations from model outputs and rules.",
  },
  {
    name: "Sensor Analysis Model",
    version: "v1.0-demo",
    status: "Ready",
    mode: "Synthetic Demo",
    description: "Processes and calibrates raw sensor data for dashboard display.",
  },
];

// ═══════════════════════════════════════════════════
// DASHBOARD  (aggregates other demo data)
// ═══════════════════════════════════════════════════
export const demoDashboardData: DashboardResponse = {
  polyhouse_id: "demo-ph-1",
  generated_at: minutesAgo(1),
  sensor_state: {
    available: true,
    recorded_at: minutesAgo(1),
    volumetric_moisture_pct: 68.0,
    soil_temperature_c: 26.5,
    atm_temperature_c: 28.0,
  },
  irrigation: {
    available: true,
    current_moisture: 68.0,
    forecast: { "1h": 66.5, "6h": 62.0, "12h": 58.5, "24h": 55.0 },
    status: "optimal",
    urgency: "low",
    recommendation:
      "No immediate irrigation required. Soil moisture is within optimal range.",
    detail: null,
  },
  disease: {
    status: "MODEL_AVAILABLE",
    latest_prediction: {
      class: "Cercospora Leaf Spot",
      confidence: "94%",
      severity: "Moderate",
    },
    detail: null,
  },
  active_alerts: demoAlerts.alerts,
  recent_recommendations_count: 6,
  model_status: demoModelsStatus,
  data_freshness_minutes: 1,
};

// ═══════════════════════════════════════════════════
// PROCESSING SETTINGS
// ═══════════════════════════════════════════════════
export const demoProcessingSettings = {
  processingMode: "Demo Mode",
  imageAnalysis: "Enabled",
  diseaseDetection: "Enabled",
  irrigationAnalysis: "Enabled",
  forecastAnalysis: "Enabled",
  sensorAnalysis: "Enabled",
  recommendationEngine: "Enabled",
  dataSource: "Synthetic Demo Data",
  backend: "Available",
  mlModel: "Demo Fallback",
};
