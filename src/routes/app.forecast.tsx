import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Leaf, LineChart as LineChartIcon } from "lucide-react";
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
import IrrigationInputForm from "@/components/IrrigationInputForm";
import { api, ApiError, type ForecastFeatures, type ForecastPredictResponse } from "@/lib/api";
import { fmt, fmtTime } from "@/lib/features";
import { usePolyhouse } from "@/lib/polyhouse";
import { DEMO_MODE, DEMO_BADGE, demoForecastResult, demoForecastExtras, demoLatestSensor } from "@/lib/demo-data";

export const Route = createFileRoute("/app/forecast")({
  head: () => ({
    meta: [
      { title: "Moisture forecast — Smart Polyhouse" },
      {
        name: "description",
        content: "Run the trained 1h/6h/12h/24h soil-moisture forecasting models on real inputs.",
      },
      { property: "og:title", content: "Moisture forecast — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Run the trained 1h/6h/12h/24h soil-moisture forecasting models on real inputs.",
      },
    ],
  }),
  component: ForecastPage,
});

function ForecastPage() {
  const { activeId, active, isLoading: phLoading, error: phError, refetch } = usePolyhouse();

  const latest = useQuery({
    queryKey: ["latest-reading", activeId],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoLatestSensor) : () => api.latestReading(activeId!),
    enabled: DEMO_MODE || !!activeId,
    retry: false,
  });

  const models = useQuery({ queryKey: ["models-status"], queryFn: () => api.modelsStatus() });

  const forecast = useMutation<ForecastPredictResponse, unknown, ForecastFeatures>({
    mutationFn: (features) => api.forecast(features),
  });

  if (phLoading) return <LoadingState label="Loading your farms…" />;
  if (phError) return <ErrorState error={phError} onRetry={refetch} />;

  if (!activeId)
    return (
      <div className="mx-auto max-w-6xl">
        <PageHeader title="Moisture forecast" />
        <EmptyState
          icon={<Leaf className="h-5 w-5" />}
          title="No polyhouse available yet"
          description="Forecasting uses the latest reading of a polyhouse. Create one first."
        />
      </div>
    );

  const noReading = latest.error instanceof ApiError && latest.error.status === 404;
  const result = DEMO_MODE ? demoForecastResult : forecast.data;
  const fcStatus = models.data?.irrigation_forecasting;

  const chartData = result
    ? [
        { t: "now", value: result.current_moisture_pct },
        { t: "+1h", value: result.forecast_1h },
        { t: "+6h", value: result.forecast_6h },
        { t: "+12h", value: result.forecast_12h },
        { t: "+24h", value: result.forecast_24h },
      ]
    : [];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Moisture forecast"
        description={`Soil-moisture trajectory predicted by the trained models${
          active ? ` for ${active.name}` : ""
        }.`}
      />
      {DEMO_MODE ? <Pill tone="warning" className="text-[10px] mb-4">{DEMO_BADGE}</Pill> : null}

      {fcStatus && fcStatus.status !== "READY" ? (
        <div className="surface-panel border-[var(--warning)]/40 bg-[var(--warning)]/10 p-4 text-sm text-[var(--warning-foreground)]">
          Forecasting model status: <b>{fcStatus.status}</b>. {fcStatus.detail ?? ""}
        </div>
      ) : null}

      <div className="surface-panel flex gap-3 border-[var(--warning)]/40 bg-[var(--warning)]/10 p-4">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--warning-foreground)]" />
        <div className="text-sm text-[var(--warning-foreground)]">
          <b>Known accuracy limitation.</b> The 24-hour horizon has a measured test R² of{" "}
          <b>−0.757</b>, which is worse than a mean baseline. The short horizons (1h, 6h) are the
          only ones that should drive irrigation action; +24h is displayed for transparency, not for
          decision making.
        </div>
      </div>

      {latest.isLoading ? <LoadingState label="Loading latest reading…" /> : null}
      {latest.error && !noReading ? (
        <ErrorState error={latest.error} onRetry={() => void latest.refetch()} />
      ) : null}

      {!latest.isLoading && (latest.data || noReading) ? (
        <IrrigationInputForm
          reading={latest.data ?? null}
          submitLabel="Run forecast"
          pending={forecast.isPending}
          onSubmit={(features) => forecast.mutate(features)}
        />
      ) : null}

      {forecast.error ? <ErrorState error={forecast.error} onRetry={() => forecast.reset()} /> : null}
      {forecast.isPending ? <LoadingState label="Running the forecasting models…" /> : null}

      {!result && !forecast.isPending && !forecast.error ? (
        <EmptyState
          icon={<LineChartIcon className="h-5 w-5" />}
          title="No forecast yet"
          description="Submit the model inputs above to call POST /irrigation/predict. Only real backend output is shown."
        />
      ) : null}

      {result ? (
        <>
          <SectionCard
            title="Predicted soil moisture by horizon"
            description="Direct output of the per-horizon forecasting models."
            action={<LayerLabel layer="prediction" />}
          >
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="+1 hour" value={fmt(result.forecast_1h, 2)} unit="%" />
              <StatCard label="+6 hours" value={fmt(result.forecast_6h, 2)} unit="%" />
              <StatCard label="+12 hours" value={fmt(result.forecast_12h, 2)} unit="%" />
              <StatCard
                label="+24 hours"
                value={fmt(result.forecast_24h, 2)}
                unit="%"
                footnote="Low reliability — test R² = −0.757"
              />
            </div>

            <div className="mt-6 h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 12, bottom: 0, left: -14 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="t" stroke="var(--muted-foreground)" fontSize={12} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={12} unit="%" />
                  <Tooltip
                    contentStyle={{
                      background: "var(--card)",
                      border: "1px solid var(--border)",
                      borderRadius: 12,
                      color: "var(--foreground)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    name="Soil moisture %"
                    stroke="var(--primary)"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>

          <SectionCard
            title="Run details"
            description="Reference values and model versions reported alongside the prediction."
            action={<LayerLabel layer="measured" />}
          >
            <div className="grid gap-x-8 sm:grid-cols-2">
              <KeyValue label="Reference time" value={fmtTime(result.reference_time)} />
              <KeyValue
                label="Current moisture (measured)"
                value={fmt(result.current_moisture_pct, 2, " %")}
              />
            </div>
            <div className="mt-4 space-y-2">
              {Object.entries(result.models).map(([key, m]) => (
                <KeyValue
                  key={key}
                  label={key}
                  value={`${m.name} · v${m.version} · ${m.task} · ${m.status}`}
                />
              ))}
            </div>
          </SectionCard>
          
          {DEMO_MODE ? (
            <SectionCard
              title="Extended Demo Info"
              description="Additional fields supplied by the demo mode dataset."
            >
              <div className="grid gap-x-8 sm:grid-cols-2">
                <KeyValue label="Forecast Status" value="Favorable" />
                <KeyValue label="Temperature" value="28°C" />
                <KeyValue label="Humidity" value="72%" />
                <KeyValue label="Rain Probability" value="30%" />
                <KeyValue label="Weather" value="Partly Cloudy" />
                <KeyValue label="Environmental Risk" value="Moderate" />
                <KeyValue label="Data Source" value="Synthetic Demo Data" />
              </div>
            </SectionCard>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
