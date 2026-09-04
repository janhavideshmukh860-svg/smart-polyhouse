import { useState } from "react";
import { AlertTriangle, Cpu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { KeyValue, LayerLabel, Pill, SectionCard } from "@/components/data-bits";
import type { ForecastFeatures, SensorReading } from "@/lib/api";
import {
  MANUAL_FIELDS,
  buildForecastFeatures,
  fmt,
  fmtTime,
  missingMeasuredFields,
  type ManualFieldKey,
} from "@/lib/features";

const EMPTY: Record<ManualFieldKey, string> = {
  Farm_ID: "",
  SM_Level_15cm: "",
  SM_Volume_15cm: "",
  SM_Aggregate_Pct: "",
  SM_Volume_Pct: "",
};

/**
 * Collects the model feature payload. Measured values come from the latest
 * stored sensor reading (read-only, never edited or invented). The dataset
 * -specific depth-probe fields are not part of the sensor_readings table,
 * so the operator supplies them — the form never guesses them.
 */
export default function IrrigationInputForm({
  reading,
  submitLabel,
  pending,
  onSubmit,
}: {
  reading: SensorReading | null;
  submitLabel: string;
  pending: boolean;
  onSubmit: (features: ForecastFeatures) => void;
}) {
  const [manual, setManual] = useState<Record<ManualFieldKey, string>>(EMPTY);
  const [touchedError, setTouchedError] = useState<string | null>(null);

  const missing = missingMeasuredFields(reading);

  return (
    <SectionCard
      title="Model inputs"
      description="The forecasting and decision endpoints require the exact feature columns of the irrigation dataset."
      action={<LayerLabel layer="measured" />}
    >
      {!reading ? (
        <div className="rounded-lg border border-dashed border-border bg-secondary/40 p-4 text-sm text-muted-foreground">
          No sensor reading has been ingested for this polyhouse yet, so the measured part of the
          model input is unavailable. Ingest a reading via <code>POST /sensors/readings</code> first.
        </div>
      ) : (
        <div className="grid gap-x-8 gap-y-1 sm:grid-cols-2">
          <KeyValue label="Recorded at" value={fmtTime(reading.recorded_at)} />
          <KeyValue
            label="Volumetric moisture"
            value={fmt(reading.volumetric_moisture_pct, 2, " %")}
          />
          <KeyValue label="Soil temperature" value={fmt(reading.soil_temperature_c, 2, " °C")} />
          <KeyValue label="Air temperature" value={fmt(reading.atm_temperature_c, 2, " °C")} />
          <KeyValue label="Board temperature" value={fmt(reading.sensor_board_temperature_c, 2, " °C")} />
          <KeyValue label="Pressure" value={fmt(reading.atm_pressure_inhg, 2, " inHg")} />
          <KeyValue label="Raw capacitive ADC" value={fmt(reading.raw_capacitive_adc, 0)} />
          <KeyValue label="Sensor voltage" value={fmt(reading.sensor_voltage_v, 3, " V")} />
        </div>
      )}

      {missing.length > 0 && reading ? (
        <div className="mt-4 flex gap-3 rounded-lg border border-[var(--warning)]/40 bg-[var(--warning)]/10 p-4 text-sm">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--warning-foreground)]" />
          <p className="text-[var(--warning-foreground)]">
            The latest reading is missing required values: <b>{missing.join(", ")}</b>. The model
            cannot run until those are present in an ingested reading.
          </p>
        </div>
      ) : null}

      <div className="mt-6">
        <div className="mb-3 flex items-center gap-2">
          <Cpu className="h-4 w-4 text-primary" />
          <h3 className="text-sm font-semibold text-foreground">
            Dataset fields not stored in sensor_readings
          </h3>
          <Pill tone="warning">operator supplied</Pill>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {MANUAL_FIELDS.map((f) => (
            <div key={f.key} className="space-y-1.5">
              <Label htmlFor={f.key} className="text-xs">
                {f.label}
              </Label>
              <Input
                id={f.key}
                inputMode={f.numeric ? "decimal" : "text"}
                value={manual[f.key]}
                onChange={(e) => setManual((m) => ({ ...m, [f.key]: e.target.value }))}
                placeholder={f.numeric ? "numeric value" : "e.g. FARM_01"}
              />
              <p className="text-xs text-muted-foreground">{f.hint}</p>
            </div>
          ))}
        </div>
      </div>

      {touchedError ? (
        <p className="mt-4 text-sm text-destructive">{touchedError}</p>
      ) : null}

      <div className="mt-6">
        <Button
          disabled={pending || !reading || missing.length > 0}
          onClick={() => {
            if (!reading) return;
            const features = buildForecastFeatures(reading, manual);
            if (!features) {
              setTouchedError(
                "Provide a Farm_ID and all four numeric SM_* values before running the model.",
              );
              return;
            }
            setTouchedError(null);
            onSubmit(features);
          }}
        >
          {pending ? "Running model…" : submitLabel}
        </Button>
      </div>
    </SectionCard>
  );
}
