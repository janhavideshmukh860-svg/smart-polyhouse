import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Droplets, Thermometer } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PageHeader } from "@/components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { KeyValue, LayerLabel, Pill, SectionCard, StatCard } from "@/components/data-bits";
import { Button } from "@/components/ui/button";
import { api, ApiError, type SensorReading } from "@/lib/api";
import { fmt, fmtTime } from "@/lib/features";
import { usePolyhouse } from "@/lib/polyhouse";
import { DEMO_MODE, DEMO_BADGE, demoLatestSensor, demoSensorHistory, demoSensorExtras } from "@/lib/demo-data";

export const Route = createFileRoute("/app/sensors")({
  head: () => ({
    meta: [
      { title: "Sensors — Smart Polyhouse" },
      { name: "description", content: "Review current and historical polyhouse sensor readings." },
      { property: "og:title", content: "Sensors — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Review current and historical polyhouse sensor readings.",
      },
    ],
  }),
  component: SensorsPage,
});

const LIMITS = [50, 100, 250, 500] as const;

function SensorsPage() {
  const { activeId, active } = usePolyhouse();
  const [limit, setLimit] = useState<number>(100);

  const latest = useQuery({
    queryKey: ["latest-reading", activeId],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoLatestSensor) : () => api.latestReading(activeId!),
    enabled: DEMO_MODE || !!activeId,
    retry: false,
  });

  const history = useQuery({
    queryKey: ["sensor-history", activeId, limit],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoSensorHistory) : () => api.sensorHistory(activeId!, limit),
    enabled: DEMO_MODE || !!activeId,
  });

  const chartData = useMemo(() => {
    const readings: SensorReading[] = history.data?.readings ?? [];
    return [...readings]
      .sort((a, b) => +new Date(a.recorded_at) - +new Date(b.recorded_at))
      .map((r) => ({
        t: fmtTime(r.recorded_at),
        moisture: r.volumetric_moisture_pct,
        soil: r.soil_temperature_c,
        air: r.atm_temperature_c,
      }));
  }, [history.data]);

  if (!activeId)
    return (
      <div className="mx-auto max-w-6xl">
        <PageHeader title="Sensors" />
        <EmptyState
          title="No polyhouse selected"
          description="Sensor data is scoped to a polyhouse. Create one to begin ingesting readings."
        />
      </div>
    );

  const latestMissing = latest.error instanceof ApiError && latest.error.status === 404;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Sensors"
        description={`Environmental readings${active ? ` for ${active.name}` : ""}, straight from the backend.`}
      />
      {DEMO_MODE ? <Pill tone="warning" className="text-[10px] mb-4">{DEMO_BADGE}</Pill> : null}

      <div className="flex items-center gap-3">
        <LayerLabel layer="measured" />
      </div>

      {latest.isLoading ? <LoadingState label="Loading latest reading…" /> : null}
      {latest.error && !latestMissing ? (
        <ErrorState error={latest.error} onRetry={() => void latest.refetch()} />
      ) : null}
      {latestMissing ? (
        <EmptyState
          icon={<Droplets className="h-5 w-5" />}
          title="No sensor readings yet"
          description="This polyhouse has not received any readings. Values appear here as soon as real data is ingested."
        />
      ) : null}

      {latest.data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Volumetric moisture"
              value={fmt(latest.data.volumetric_moisture_pct, 2)}
              unit="%"
              icon={<Droplets className="h-4 w-4" />}
              footnote={`Recorded ${fmtTime(latest.data.recorded_at)}`}
            />
            <StatCard
              label="Soil temperature"
              value={fmt(latest.data.soil_temperature_c, 2)}
              unit="°C"
              icon={<Thermometer className="h-4 w-4" />}
            />
            <StatCard
              label="Air temperature"
              value={fmt(latest.data.atm_temperature_c, 2)}
              unit="°C"
            />
            <StatCard
              label="Pressure"
              value={fmt(latest.data.atm_pressure_inhg, 2)}
              unit="inHg"
            />
          </div>
          
          {DEMO_MODE ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 mt-4">
              <StatCard label="Humidity" value="72" unit="%" />
              <StatCard label="Light Intensity" value="Good" />
              <StatCard label="CO2" value="Normal" />
              <StatCard label="Sensor Network" value="Online" />
              <StatCard label="Last Updated" value="Just now" />
            </div>
          ) : null}

          <SectionCard title="Raw sensor channels" description="Latest ingested reading, unmodified.">
            <div className="grid gap-x-8 sm:grid-cols-2">
              <KeyValue label="Raw capacitive ADC" value={fmt(latest.data.raw_capacitive_adc, 0)} />
              <KeyValue label="Sensor voltage" value={fmt(latest.data.sensor_voltage_v, 3, " V")} />
              <KeyValue
                label="Board temperature"
                value={fmt(latest.data.sensor_board_temperature_c, 2, " °C")}
              />
              <KeyValue label="Recorded at" value={fmtTime(latest.data.recorded_at)} />
            </div>
          </SectionCard>
        </>
      ) : null}

      <SectionCard
        title="Historical readings"
        description="Time-ordered readings returned by /sensors/readings/{polyhouse_id}."
        action={
          <div className="flex gap-1">
            {LIMITS.map((l) => (
              <Button
                key={l}
                size="sm"
                variant={limit === l ? "default" : "outline"}
                onClick={() => setLimit(l)}
              >
                {l}
              </Button>
            ))}
          </div>
        }
      >
        {history.isLoading ? <LoadingState label="Loading history…" /> : null}
        {history.error ? (
          <ErrorState error={history.error} onRetry={() => void history.refetch()} />
        ) : null}
        {history.data && chartData.length === 0 ? (
          <EmptyState
            title="No historical readings"
            description="Charts will render as soon as readings exist for this polyhouse."
          />
        ) : null}
        {chartData.length > 0 ? (
          <div className="space-y-8">
            <div>
              <p className="mb-2 text-sm font-medium text-foreground">Soil moisture (%)</p>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ left: -18, right: 8, top: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="t" tick={{ fontSize: 11 }} minTickGap={28} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: "var(--card)",
                        border: "1px solid var(--border)",
                        borderRadius: 12,
                        fontSize: 12,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="moisture"
                      stroke="var(--chart-1)"
                      strokeWidth={2}
                      dot={false}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div>
              <p className="mb-2 text-sm font-medium text-foreground">Temperatures (°C)</p>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ left: -18, right: 8, top: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="t" tick={{ fontSize: 11 }} minTickGap={28} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: "var(--card)",
                        border: "1px solid var(--border)",
                        borderRadius: 12,
                        fontSize: 12,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="soil"
                      stroke="var(--chart-5)"
                      strokeWidth={2}
                      dot={false}
                      connectNulls
                    />
                    <Line
                      type="monotone"
                      dataKey="air"
                      stroke="var(--chart-4)"
                      strokeWidth={2}
                      dot={false}
                      connectNulls
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Soil temperature (dark green) and air temperature (amber).
              </p>
            </div>
          </div>
        ) : null}
      </SectionCard>
    </div>
  );
}
