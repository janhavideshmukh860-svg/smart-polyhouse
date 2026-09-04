/**
 * Helpers for assembling the irrigation model feature payload.
 *
 * The FastAPI forecasting/decision endpoints require the exact feature
 * columns of the authoritative irrigation dataset. Some of those columns
 * (Farm_ID and the SM_* depth-probe columns) are NOT part of the generic
 * sensor_readings table, so they can never be derived from an ingested
 * reading — the UI asks the operator for them explicitly instead of
 * inventing values.
 */
import type { ForecastFeatures, SensorReading } from "./api";

/** Fields the backend needs that a stored sensor reading can provide. */
export const MEASURED_FROM_READING = [
  "volumetric_moisture_pct",
  "sensor_board_temperature_c",
  "raw_capacitive_adc",
  "sensor_voltage_v",
  "atm_pressure_inhg",
  "atm_temperature_c",
  "soil_temperature_c",
] as const;

export type ManualFieldKey =
  | "Farm_ID"
  | "SM_Level_15cm"
  | "SM_Volume_15cm"
  | "SM_Aggregate_Pct"
  | "SM_Volume_Pct";

export const MANUAL_FIELDS: { key: ManualFieldKey; label: string; hint: string; numeric: boolean }[] =
  [
    {
      key: "Farm_ID",
      label: "Farm_ID",
      hint: "Dataset farm identifier expected by the model",
      numeric: false,
    },
    {
      key: "SM_Level_15cm",
      label: "SM_Level_15cm",
      hint: "Depth-probe soil moisture level at 15 cm",
      numeric: true,
    },
    {
      key: "SM_Volume_15cm",
      label: "SM_Volume_15cm",
      hint: "Depth-probe soil moisture volume at 15 cm",
      numeric: true,
    },
    {
      key: "SM_Aggregate_Pct",
      label: "SM_Aggregate_Pct",
      hint: "Aggregate soil moisture percentage",
      numeric: true,
    },
    {
      key: "SM_Volume_Pct",
      label: "SM_Volume_Pct",
      hint: "Volumetric soil moisture percentage from the depth probe",
      numeric: true,
    },
  ];

export interface MissingInfo {
  /** Reading-derived fields that are null in the latest stored reading. */
  fromReading: string[];
}

export function missingMeasuredFields(reading: SensorReading | null | undefined): string[] {
  if (!reading) return [...MEASURED_FROM_READING];
  return MEASURED_FROM_READING.filter((k) => reading[k] === null || reading[k] === undefined);
}

function timeParts(date: Date) {
  const start = Date.UTC(date.getUTCFullYear(), 0, 0);
  const dayOfYear = Math.floor((date.getTime() - start) / 86_400_000);
  const hour = date.getUTCHours();
  return {
    Hour: hour,
    Day: date.getUTCDate(),
    Month: date.getUTCMonth() + 1,
    DayOfWeek: date.getUTCDay() === 0 ? 6 : date.getUTCDay() - 1,
    DayOfYear: dayOfYear,
    Hour_sin: Math.sin((2 * Math.PI * hour) / 24),
    Hour_cos: Math.cos((2 * Math.PI * hour) / 24),
    Day_sin: Math.sin((2 * Math.PI * dayOfYear) / 365),
    Day_cos: Math.cos((2 * Math.PI * dayOfYear) / 365),
  };
}

/**
 * Builds the exact ForecastFeatures payload. Returns null when the
 * measured reading is missing any required value — the caller then shows
 * the operator what is missing instead of substituting a placeholder.
 */
export function buildForecastFeatures(
  reading: SensorReading,
  manual: Record<ManualFieldKey, string>,
): ForecastFeatures | null {
  if (missingMeasuredFields(reading).length > 0) return null;
  const nums = {
    SM_Level_15cm: Number(manual.SM_Level_15cm),
    SM_Volume_15cm: Number(manual.SM_Volume_15cm),
    SM_Aggregate_Pct: Number(manual.SM_Aggregate_Pct),
    SM_Volume_Pct: Number(manual.SM_Volume_Pct),
  };
  if (!manual.Farm_ID.trim()) return null;
  if (Object.values(nums).some((v) => !Number.isFinite(v))) return null;

  return {
    Farm_ID: manual.Farm_ID.trim(),
    Volumetric_Moisture_Pct: reading.volumetric_moisture_pct!,
    Sensor_Board_Temperature_C: reading.sensor_board_temperature_c!,
    Raw_Capacitive_ADC: reading.raw_capacitive_adc!,
    Sensor_Voltage_V: reading.sensor_voltage_v!,
    Atm_Pressure_inHg: reading.atm_pressure_inhg!,
    Atm_Temperature_C: reading.atm_temperature_c!,
    Soil_Temperature_C: reading.soil_temperature_c!,
    ...nums,
    ...timeParts(new Date(reading.recorded_at)),
  };
}

export function fmt(value: number | null | undefined, digits = 1, suffix = ""): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return `${value.toFixed(digits)}${suffix}`;
}

export function fmtTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
