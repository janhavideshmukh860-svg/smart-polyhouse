import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BellRing,
  Brain,
  Droplets,
  Leaf,
  Lightbulb,
  Thermometer,
  Waves,
} from "lucide-react";
import { PageHeader } from "@/components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import {
  KeyValue,
  LayerLabel,
  Pill,
  SectionCard,
  StatCard,
  severityTone,
  statusTone,
  urgencyTone,
} from "@/components/data-bits";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { fmt, fmtTime } from "@/lib/features";
import { usePolyhouse } from "@/lib/polyhouse";
import { DEMO_MODE, DEMO_BADGE, demoDashboardData } from "@/lib/demo-data";

export const Route = createFileRoute("/app/")({
  head: () => ({
    meta: [
      { title: "Dashboard — Smart Polyhouse" },
      {
        name: "description",
        content: "Live environmental, irrigation and plant-health state for your polyhouse.",
      },
      { property: "og:title", content: "Dashboard — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Live environmental, irrigation and plant-health state for your polyhouse.",
      },
    ],
  }),
  component: DashboardPage,
});

function DashboardPage() {
  const { activeId, active, isLoading: phLoading, error: phError, refetch } = usePolyhouse();

  const { data, isLoading, error, refetch: reload } = useQuery({
    queryKey: ["dashboard", activeId],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoDashboardData) : () => api.dashboard(activeId!),
    enabled: DEMO_MODE || !!activeId,
  });

  if (phLoading) return <LoadingState label="Loading your farms…" />;
  if (phError) return <ErrorState error={phError} onRetry={refetch} />;
  if (!activeId)
    return (
      <div className="mx-auto max-w-6xl">
        <PageHeader title="Dashboard" />
        <EmptyState
          icon={<Leaf className="h-5 w-5" />}
          title="No polyhouse available yet"
          description="Create a farm and a polyhouse through the API to start monitoring. Nothing is shown here until real records exist."
        />
      </div>
    );

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Dashboard"
        description={active ? `Live state for ${active.name}.` : "Live polyhouse state."}
      />
      {DEMO_MODE ? <Pill tone="warning" className="text-[10px] mb-4">{DEMO_BADGE}</Pill> : null}

      {isLoading ? <LoadingState label="Loading dashboard…" /> : null}
      {error ? <ErrorState error={error} onRetry={() => void reload()} /> : null}

      {data ? (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-3">
            <LayerLabel layer="measured" />
            <span className="text-xs text-muted-foreground">
              Generated {fmtTime(data.generated_at)}
              {data.data_freshness_minutes !== null
                ? ` · data ${data.data_freshness_minutes} min old`
                : ""}
            </span>
          </div>

          {data.sensor_state.available ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                label="Soil moisture"
                value={fmt(data.sensor_state.volumetric_moisture_pct, 1)}
                unit="%"
                icon={<Droplets className="h-4 w-4" />}
                footnote={`Recorded ${fmtTime(data.sensor_state.recorded_at)}`}
              />
              <StatCard
                label="Soil temperature"
                value={fmt(data.sensor_state.soil_temperature_c, 1)}
                unit="°C"
                icon={<Thermometer className="h-4 w-4" />}
              />
              <StatCard
                label="Air temperature"
                value={fmt(data.sensor_state.atm_temperature_c, 1)}
                unit="°C"
                icon={<Waves className="h-4 w-4" />}
              />
              <StatCard
                label="Active alerts"
                value={String(data.active_alerts.length)}
                icon={<BellRing className="h-4 w-4" />}
                footnote={`${data.recent_recommendations_count} recent recommendations`}
              />
            </div>
          ) : (
            <EmptyState
              icon={<Activity className="h-5 w-5" />}
              title="No sensor data received yet"
              description={
                data.sensor_state.detail ??
                "This polyhouse has not ingested any sensor readings, so no environmental values can be shown."
              }
            />
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            <SectionCard
              title="Irrigation intelligence"
              description="Decision-engine output stored for this polyhouse."
              action={<LayerLabel layer="rule" />}
            >
              {data.irrigation.available ? (
                <div className="space-y-1">
                  <KeyValue
                    label="Current moisture (measured)"
                    value={fmt(data.irrigation.current_moisture, 2, " %")}
                  />
                  {data.irrigation.status ? (
                    <KeyValue
                      label="Status"
                      value={<Pill tone={statusTone(data.irrigation.status)}>{data.irrigation.status}</Pill>}
                    />
                  ) : null}
                  {data.irrigation.urgency ? (
                    <KeyValue
                      label="Urgency"
                      value={<Pill tone={urgencyTone(data.irrigation.urgency)}>{data.irrigation.urgency}</Pill>}
                    />
                  ) : null}
                  {data.irrigation.forecast ? (
                    <div className="pt-3">
                      <LayerLabel layer="prediction" />
                      <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
                        {Object.entries(data.irrigation.forecast).map(([h, v]) => (
                          <div key={h} className="rounded-lg bg-secondary/60 p-2 text-center">
                            <p className="text-xs text-muted-foreground">{h}</p>
                            <p className="text-sm font-semibold text-foreground">{fmt(v, 1, "%")}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  {data.irrigation.recommendation ? (
                    <p className="pt-3 text-sm text-foreground">{data.irrigation.recommendation}</p>
                  ) : null}
                  {data.irrigation.detail ? (
                    <p className="pt-3 text-sm text-muted-foreground">{data.irrigation.detail}</p>
                  ) : null}
                  <div className="pt-4">
                    <Button asChild variant="outline" size="sm">
                      <Link to="/app/irrigation">Open irrigation engine</Link>
                    </Button>
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={<Droplets className="h-5 w-5" />}
                  title="Irrigation state unavailable"
                  description={data.irrigation.detail ?? "No calibrated moisture reading available yet."}
                  action={
                    <Button asChild variant="outline" size="sm">
                      <Link to="/app/irrigation">Run the decision engine</Link>
                    </Button>
                  }
                />
              )}
            </SectionCard>

            <SectionCard
              title="Plant health (disease model)"
              description="Reported straight from the backend model registry."
              action={<Pill tone={statusTone(data.disease.status)}>{data.disease.status}</Pill>}
            >
              {data.disease.latest_prediction ? (
                <div className="space-y-1">
                  {Object.entries(data.disease.latest_prediction).map(([k, v]) => (
                    <KeyValue key={k} label={k} value={String(v)} />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {data.disease.detail ??
                    "No disease prediction is available for this polyhouse. Nothing is inferred when the model or a real prediction is missing."}
                </p>
              )}
              <div className="pt-4">
                <Button asChild variant="outline" size="sm">
                  <Link to="/app/disease">Open disease analysis</Link>
                </Button>
              </div>
            </SectionCard>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <SectionCard
              title="Active alerts"
              action={
                <Button asChild variant="ghost" size="sm">
                  <Link to="/app/alerts">All alerts</Link>
                </Button>
              }
            >
              {data.active_alerts.length === 0 ? (
                <p className="text-sm text-muted-foreground">No active alerts for this polyhouse.</p>
              ) : (
                <ul className="space-y-3">
                  {data.active_alerts.slice(0, 5).map((a) => (
                    <li key={a.id} className="rounded-lg border border-border/70 p-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Pill tone={severityTone(a.severity)}>{a.severity}</Pill>
                        <span className="text-xs text-muted-foreground">{a.alert_type}</span>
                        <span className="ml-auto text-xs text-muted-foreground">
                          {fmtTime(a.created_at)}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-foreground">{a.message}</p>
                    </li>
                  ))}
                </ul>
              )}
            </SectionCard>

            <SectionCard
              title="Model status"
              action={
                <Button asChild variant="ghost" size="sm">
                  <Link to="/app/models">Model details</Link>
                </Button>
              }
            >
              <div className="space-y-1">
                <KeyValue
                  label="Irrigation calibration"
                  value={
                    <Pill tone={statusTone(data.model_status.irrigation_calibration.status)}>
                      {data.model_status.irrigation_calibration.status}
                    </Pill>
                  }
                />
                <KeyValue
                  label="Irrigation forecasting"
                  value={
                    <Pill tone={statusTone(data.model_status.irrigation_forecasting.status)}>
                      {data.model_status.irrigation_forecasting.status}
                    </Pill>
                  }
                />
                <KeyValue
                  label="Disease detection"
                  value={
                    <Pill tone={statusTone(data.model_status.disease.status)}>
                      {data.model_status.disease.status}
                    </Pill>
                  }
                />
              </div>
              <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                <Brain className="h-3.5 w-3.5" /> Metrics and horizon limitations are listed on the
                Models page.
              </div>
            </SectionCard>
          </div>

          <SectionCard
            title="Recommendations"
            action={
              <Button asChild variant="ghost" size="sm">
                <Link to="/app/recommendations">Open recommendations</Link>
              </Button>
            }
          >
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <Lightbulb className="h-4 w-4 text-primary" />
              {data.recent_recommendations_count > 0
                ? `${data.recent_recommendations_count} recommendation(s) recorded recently for this polyhouse.`
                : "No recommendations have been generated for this polyhouse yet."}
            </div>
          </SectionCard>
        </div>
      ) : null}
    </div>
  );
}
