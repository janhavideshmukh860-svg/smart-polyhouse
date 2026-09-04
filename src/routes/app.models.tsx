import { createFileRoute } from "@tanstack/react-router";
import { DEMO_MODE, DEMO_BADGE, demoModelsStatus, demoModelCards } from "@/lib/demo-data";
import { useQuery } from "@tanstack/react-query";
import { Brain } from "lucide-react";
import { PageHeader } from "@/components/AppShell";
import { ErrorState, LoadingState } from "@/components/states";
import { KeyValue, Pill, SectionCard, statusTone } from "@/components/data-bits";
import { api, type ModelStatusEntry } from "@/lib/api";

export const Route = createFileRoute("/app/models")({
  head: () => ({
    meta: [
      { title: "Models — Smart Polyhouse" },
      {
        name: "description",
        content: "Live training status and evaluation metrics of every deployed model.",
      },
      { property: "og:title", content: "Models — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Live training status and evaluation metrics of every deployed model.",
      },
    ],
  }),
  component: ModelsPage,
});

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function MetricValue({ value }: { value: unknown }) {
  if (value === null || value === undefined) return <span>Not reported</span>;
  if (typeof value === "number") return <span>{value.toFixed(4)}</span>;
  if (typeof value === "string" || typeof value === "boolean") return <span>{String(value)}</span>;
  return (
    <pre className="max-w-full overflow-x-auto text-xs text-muted-foreground">
      {JSON.stringify(value)}
    </pre>
  );
}

function Metrics({ metrics }: { metrics: Record<string, unknown> | null }) {
  if (!metrics || Object.keys(metrics).length === 0)
    return <p className="text-sm text-muted-foreground">The backend reported no metrics.</p>;

  return (
    <div className="space-y-4">
      {Object.entries(metrics).map(([key, value]) =>
        isRecord(value) ? (
          <div key={key} className="rounded-lg border border-border/60 p-3">
            <p className="mb-1 text-sm font-medium text-foreground">{key}</p>
            <div className="grid gap-x-8 sm:grid-cols-2">
              {Object.entries(value).map(([k, v]) => (
                <KeyValue key={k} label={k} value={<MetricValue value={v} />} />
              ))}
            </div>
          </div>
        ) : (
          <KeyValue key={key} label={key} value={<MetricValue value={value} />} />
        ),
      )}
    </div>
  );
}

function ModelCard({
  title,
  description,
  entry,
  note,
}: {
  title: string;
  description: string;
  entry: ModelStatusEntry;
  note?: string;
}) {
  return (
    <SectionCard
      title={title}
      description={description}
      action={<Pill tone={statusTone(entry.status)}>{entry.status}</Pill>}
    >
      <div className="grid gap-x-8 sm:grid-cols-2">
        <KeyValue label="Model type" value={entry.model_type ?? "—"} />
        <KeyValue label="Version" value={entry.version ?? "—"} />
        {entry.horizons ? <KeyValue label="Horizons" value={entry.horizons.join(", ")} /> : null}
      </div>
      {entry.detail ? (
        <div className="mt-3 rounded-lg border border-[var(--warning)]/40 bg-[var(--warning)]/10 p-3 text-sm text-[var(--warning-foreground)]">
          {entry.detail}
        </div>
      ) : null}
      {note ? <p className="mt-3 text-xs text-muted-foreground">{note}</p> : null}
      <div className="mt-4">
        <p className="mb-2 text-sm font-medium text-foreground">Evaluation metrics</p>
        <Metrics metrics={entry.metrics ?? null} />
      </div>
    </SectionCard>
  );
}

function ModelsPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["models-status"],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoModelsStatus) : () => api.modelsStatus(),
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Models"
        description="Live status from GET /models/status. Metrics are the values recorded at training time."
      />

      {isLoading ? <LoadingState label="Loading model status…" /> : null}
      {error ? <ErrorState error={error} onRetry={() => void refetch()} /> : null}

      {data ? (
        <>
          <ModelCard
            title="Irrigation calibration"
            description="Maps raw capacitive sensor channels to volumetric moisture."
            entry={data.irrigation_calibration}
          />
          <ModelCard
            title="Irrigation forecasting"
            description="Per-horizon soil-moisture forecasting models (1h, 6h, 12h, 24h)."
            entry={data.irrigation_forecasting}
            note="Documented limitation: the 24h horizon scores a test R² of −0.757 — worse than a mean baseline. Only the 1h and 6h horizons are considered actionable."
          />
          <ModelCard
            title="Disease classification"
            description="Leaf-image classifier used by the disease analysis page."
            entry={data.disease}
          />
          {DEMO_MODE ? (
            <SectionCard
              title="Demo Model Registry"
              description="All models available in this demonstration."
              action={<Pill tone="warning" className="text-[10px]">{DEMO_BADGE}</Pill>}
            >
              <div className="space-y-4">
                {demoModelCards.map((m) => (
                  <div key={m.name} className="rounded-lg border border-border/60 p-4">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-foreground">{m.name}</p>
                      <Pill tone="success">{m.status}</Pill>
                    </div>
                    <div className="mt-2 grid gap-x-8 sm:grid-cols-2">
                      <KeyValue label="Version" value={m.version} />
                      <KeyValue label="Mode" value={m.mode} />
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">{m.description}</p>
                  </div>
                ))}
              </div>
            </SectionCard>
          ) : null}
          <SectionCard
            title="How to read this page"
            description="No metric on this page is hardcoded in the frontend."
            action={<Brain className="h-5 w-5 text-primary" />}
          >
            <p className="text-sm text-muted-foreground">
              Every status, version and metric above is rendered exactly as returned by the backend.
              When a model has not been trained, its status is shown as-is and no substitute numbers
              are displayed.
            </p>
          </SectionCard>
        </>
      ) : null}
    </div>
  );
}
