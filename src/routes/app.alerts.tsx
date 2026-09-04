import { createFileRoute } from "@tanstack/react-router";
import { DEMO_MODE, DEMO_BADGE, demoAlerts } from "@/lib/demo-data";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing } from "lucide-react";
import { PageHeader } from "@/components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { KeyValue, Pill, SectionCard, severityTone, statusTone } from "@/components/data-bits";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { fmtTime } from "@/lib/features";
import { usePolyhouse } from "@/lib/polyhouse";

export const Route = createFileRoute("/app/alerts")({
  head: () => ({
    meta: [
      { title: "Alerts — Smart Polyhouse" },
      {
        name: "description",
        content: "Monitor, acknowledge and resolve polyhouse conditions that need attention.",
      },
      { property: "og:title", content: "Alerts — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Monitor, acknowledge and resolve polyhouse conditions that need attention.",
      },
    ],
  }),
  component: AlertsPage,
});

function AlertsPage() {
  const { activeId, active } = usePolyhouse();
  const qc = useQueryClient();
  const [activeOnly, setActiveOnly] = useState(true);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["alerts", activeId, activeOnly],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoAlerts) : () => api.listAlerts(activeId ?? undefined, activeOnly, 50),
    enabled: DEMO_MODE || !!activeId,
  });

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["alerts"] });
    void qc.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const acknowledge = useMutation({
    mutationFn: (id: string) => api.acknowledgeAlert(id),
    onSuccess: invalidate,
  });
  const resolve = useMutation({
    mutationFn: (id: string) => api.resolveAlert(id),
    onSuccess: invalidate,
  });

  const mutationError = acknowledge.error ?? resolve.error;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Alerts"
        description={`Conditions raised by the backend${active ? ` for ${active.name}` : ""}.`}
      />
      {DEMO_MODE ? <Pill tone="warning" className="text-[10px]">{DEMO_BADGE}</Pill> : null}

      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant={activeOnly ? "default" : "outline"} onClick={() => setActiveOnly(true)}>
          Active only
        </Button>
        <Button size="sm" variant={!activeOnly ? "default" : "outline"} onClick={() => setActiveOnly(false)}>
          All alerts
        </Button>
      </div>

      {mutationError ? (
        <ErrorState
          error={mutationError}
          onRetry={() => {
            acknowledge.reset();
            resolve.reset();
          }}
        />
      ) : null}

      {!activeId ? (
        <EmptyState title="No polyhouse selected" description="Alerts are scoped to a polyhouse." />
      ) : isLoading ? (
        <LoadingState label="Loading alerts…" />
      ) : error ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : (data?.alerts.length ?? 0) === 0 ? (
        <EmptyState
          icon={<BellRing className="h-5 w-5" />}
          title={activeOnly ? "No active alerts" : "No alerts recorded"}
          description="Alerts raised by the backend appear here with severity, source and resolution actions."
        />
      ) : (
        <div className="space-y-4">
          {data!.alerts.map((a) => {
            const busy =
              (acknowledge.isPending && acknowledge.variables === a.id) ||
              (resolve.isPending && resolve.variables === a.id);
            return (
              <SectionCard
                key={a.id}
                title={a.message}
                description={a.alert_type}
                action={
                  <div className="flex flex-wrap gap-2">
                    <Pill tone={severityTone(a.severity)}>{a.severity}</Pill>
                    <Pill tone={statusTone(a.status)}>{a.status}</Pill>
                  </div>
                }
              >
                <div className="grid gap-x-8 sm:grid-cols-2">
                  <KeyValue label="Raised" value={fmtTime(a.created_at)} />
                  <KeyValue label="Resolved" value={a.resolved_at ? fmtTime(a.resolved_at) : "—"} />
                </div>
                {a.source_reference ? (
                  <pre className="mt-3 overflow-x-auto rounded-lg bg-secondary/50 p-3 text-xs text-muted-foreground">
                    {JSON.stringify(a.source_reference, null, 2)}
                  </pre>
                ) : null}
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy || a.status !== "active"}
                    onClick={() => acknowledge.mutate(a.id)}
                  >
                    Acknowledge
                  </Button>
                  <Button
                    size="sm"
                    disabled={busy || a.status === "resolved"}
                    onClick={() => resolve.mutate(a.id)}
                  >
                    Resolve
                  </Button>
                </div>
              </SectionCard>
            );
          })}
        </div>
      )}
    </div>
  );
}
