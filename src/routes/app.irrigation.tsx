import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Droplets, Leaf, ShieldAlert } from "lucide-react";
import { PageHeader } from "@/components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import {
  KeyValue,
  LayerLabel,
  Pill,
  SectionCard,
  StatCard,
  statusTone,
  urgencyTone,
} from "@/components/data-bits";
import IrrigationInputForm from "@/components/IrrigationInputForm";
import { api, ApiError, type ForecastFeatures, type IrrigationDecisionResponse } from "@/lib/api";
import { fmt, fmtTime } from "@/lib/features";
import { usePolyhouse } from "@/lib/polyhouse";
import { DEMO_MODE, DEMO_BADGE, demoIrrigationDecision, demoIrrigationExtras, demoLatestSensor } from "@/lib/demo-data";

export const Route = createFileRoute("/app/irrigation")({
  head: () => ({
    meta: [
      { title: "Irrigation — Smart Polyhouse" },
      {
        name: "description",
        content: "Understand measured moisture, ML forecasts and irrigation decisions.",
      },
      { property: "og:title", content: "Irrigation — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Understand measured moisture, ML forecasts and irrigation decisions.",
      },
    ],
  }),
  component: IrrigationPage,
});

const HORIZON_KEYS = ["1h", "6h", "12h", "24h"] as const;

function forecastValue(forecast: Record<string, number> | null | undefined, h: string) {
  if (!forecast) return null;
  return forecast[h] ?? forecast[`forecast_${h}`] ?? null;
}

function IrrigationPage() {
  const { activeId, active, isLoading: phLoading, error: phError, refetch } = usePolyhouse();

  const latest = useQuery({
    queryKey: ["latest-reading", activeId],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoLatestSensor) : () => api.latestReading(activeId!),
    enabled: DEMO_MODE || !!activeId,
    retry: false,
  });

  const decision = useMutation<IrrigationDecisionResponse, unknown, ForecastFeatures>({
    mutationFn: (features) =>
      api.decision(activeId ? { ...features, polyhouse_id: activeId } : { ...features }),
  });

  if (phLoading) return <LoadingState label="Loading your farms…" />;
  if (phError) return <ErrorState error={phError} onRetry={refetch} />;

  if (!activeId)
    return (
      <div className="mx-auto max-w-6xl">
        <PageHeader title="Smart irrigation" />
        <EmptyState
          icon={<Leaf className="h-5 w-5" />}
          title="No polyhouse available yet"
          description="Irrigation decisions are scoped to a polyhouse. Create one before running the model."
        />
      </div>
    );

  const noReading = latest.error instanceof ApiError && latest.error.status === 404;
  const result = DEMO_MODE ? demoIrrigationDecision : decision.data;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Smart irrigation"
        description={`Measured state, model prediction and rule-based action kept separate${
          active ? ` for ${active.name}` : ""
        }.`}
      />
      {DEMO_MODE ? <Pill tone="warning" className="text-[10px] mb-4">{DEMO_BADGE}</Pill> : null}

      {latest.isLoading ? <LoadingState label="Loading latest reading…" /> : null}
      {latest.error && !noReading ? (
        <ErrorState error={latest.error} onRetry={() => void latest.refetch()} />
      ) : null}

      {/* 1 — MEASURED DATA (+ operator supplied dataset fields) */}
      {!latest.isLoading && (latest.data || noReading) ? (
        <IrrigationInputForm
          reading={latest.data ?? null}
          submitLabel="Run irrigation decision"
          pending={decision.isPending}
          onSubmit={(features) => decision.mutate(features)}
        />
      ) : null}

      {decision.error ? (
        <ErrorState error={decision.error} onRetry={() => decision.reset()} />
      ) : null}

      {decision.isPending ? <LoadingState label="Running the decision engine…" /> : null}

      {!result && !decision.isPending && !decision.error ? (
        <EmptyState
          icon={<Droplets className="h-5 w-5" />}
          title="No irrigation decision yet"
          description="Submit the model inputs above to get a real decision from POST /irrigation/decision. Nothing is shown until the backend returns it."
        />
      ) : null}

      {result ? (
        <>
          {/* 2 — MODEL PREDICTION */}
          <SectionCard
            title="Forecasted soil moisture"
            description="Values returned by the trained forecasting models for each horizon."
            action={<LayerLabel layer="prediction" />}
          >
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {HORIZON_KEYS.map((h) => {
                const v = forecastValue(result.forecast, h);
                return (
                  <StatCard
                    key={h}
                    label={`+${h} forecast`}
                    value={fmt(v, 2)}
                    {...(v === null
                      ? { footnote: "Not returned by the backend" }
                      : { unit: "%" })}
                  />
                );
              })}
            </div>
            <div className="mt-4 grid gap-x-8 sm:grid-cols-2">
              <KeyValue
                label="Current moisture (measured)"
                value={fmt(result.current_moisture, 2, " %")}
              />
              <KeyValue
                label="Model confidence"
                value={
                  result.model_confidence === null
                    ? "Not reported by the backend"
                    : fmt(result.model_confidence * 100, 1, " %")
                }
              />
              <KeyValue label="Generated at" value={fmtTime(result.generated_at)} />
              <KeyValue label="Recommendation ID" value={result.recommendation_id ?? "—"} />
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              Documented limitation: the 24-hour forecasting horizon scores a negative test R² of
              −0.757, i.e. it performs worse than predicting the mean. Treat the +24h value as
              indicative only.
            </p>
          </SectionCard>

          {/* 3 — RULE-BASED DECISION */}
          <SectionCard
            title="Decision engine outcome"
            description="Deterministic thresholds applied by the backend to the measured and predicted values."
            action={<LayerLabel layer="rule" />}
          >
            <div className="flex flex-wrap items-center gap-2">
              <Pill tone={statusTone(result.status)}>status: {result.status}</Pill>
              <Pill tone={urgencyTone(result.urgency)}>urgency: {result.urgency}</Pill>
            </div>
            <div className="mt-4 space-y-2">
              <p className="text-sm text-muted-foreground">Reason</p>
              <p className="text-sm text-foreground">{result.reason}</p>
            </div>
            {result.risk_factors.length > 0 ? (
              <div className="mt-4">
                <p className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                  <ShieldAlert className="h-4 w-4" /> Risk factors
                </p>
                <ul className="list-inside list-disc space-y-1 text-sm text-foreground">
                  {result.risk_factors.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="mt-4 text-sm text-muted-foreground">
                The backend reported no risk factors for this decision.
              </p>
            )}
          </SectionCard>

          {/* 4 — RECOMMENDATION */}
          <SectionCard
            title="Recommended action"
            description="The persisted recommendation text produced for this decision."
            action={<LayerLabel layer="recommendation" />}
          >
            <p className="text-base text-foreground">{result.recommendation}</p>
          </SectionCard>
          
          {DEMO_MODE && result ? (
            <SectionCard
              title="Extended Demo Info"
              description="Additional fields supplied by the demo mode dataset."
              action={<LayerLabel layer="measured" />}
            >
              <div className="grid gap-x-8 sm:grid-cols-2">
                <KeyValue label="Irrigation Status" value="Optimal" />
                <KeyValue label="Soil Moisture" value="68%" />
                <KeyValue label="Water Requirement" value="Moderate" />
                <KeyValue label="Next Irrigation" value="Approximately 3 hours" />
                <KeyValue label="Current Decision" value="No immediate irrigation required" />
                <KeyValue label="Irrigation System" value="Online" />
                <KeyValue label="Data Source" value="Synthetic Demo Data" />
              </div>
            </SectionCard>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
