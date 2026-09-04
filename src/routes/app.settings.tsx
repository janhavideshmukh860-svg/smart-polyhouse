import { createFileRoute } from "@tanstack/react-router";
import { DEMO_MODE, DEMO_BADGE, demoProcessingSettings, demoUser } from "@/lib/demo-data";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { LogOut, Plus } from "lucide-react";
import { PageHeader } from "@/components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { KeyValue, Pill, SectionCard } from "@/components/data-bits";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, API_BASE_URL } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { fmtTime } from "@/lib/features";
import { usePolyhouse } from "@/lib/polyhouse";

export const Route = createFileRoute("/app/settings")({
  head: () => ({
    meta: [
      { title: "Profile & settings — Smart Polyhouse" },
      {
        name: "description",
        content: "Your account, farms, polyhouses and backend connection details.",
      },
      { property: "og:title", content: "Profile & settings — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Your account, farms, polyhouses and backend connection details.",
      },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { user, logout } = useAuth();
  const displayUser = user ?? (DEMO_MODE ? demoUser : null);
  const { farms, polyhouses, activeId, setActiveId, isLoading, error, refetch } = usePolyhouse();
  const qc = useQueryClient();

  const [farmName, setFarmName] = useState("");
  const [farmLocation, setFarmLocation] = useState("");
  const [phFarmId, setPhFarmId] = useState("");
  const [phName, setPhName] = useState("");
  const [phArea, setPhArea] = useState("");

  const reload = () => {
    void qc.invalidateQueries({ queryKey: ["farms"] });
    refetch();
  };

  const createFarm = useMutation({
    mutationFn: () =>
      api.createFarm({
        name: farmName.trim(),
        ...(farmLocation.trim() ? { location_label: farmLocation.trim() } : {}),
      }),
    onSuccess: () => {
      setFarmName("");
      setFarmLocation("");
      reload();
    },
  });

  const createPolyhouse = useMutation({
    mutationFn: () =>
      api.createPolyhouse(phFarmId, {
        name: phName.trim(),
        ...(phArea.trim() && Number.isFinite(Number(phArea)) ? { area_sq_m: Number(phArea) } : {}),
      }),
    onSuccess: () => {
      setPhName("");
      setPhArea("");
      reload();
    },
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="Profile & settings"
        description="Account details and the farm structure your workspace is built on."
      />

      <SectionCard
        title="Account"
        description="Read from GET /auth/me — the backend does not expose profile editing."
        action={displayUser ? <Pill tone="info">{displayUser.role}</Pill> : null}
      >
        {displayUser ? (
          <>
            <div className="grid gap-x-8 sm:grid-cols-2">
              <KeyValue label="Email" value={displayUser.email} />
              <KeyValue label="Full name" value={displayUser.full_name ?? "—"} />
              <KeyValue label="Status" value={displayUser.is_active ? "Active" : "Inactive"} />
              <KeyValue label="Member since" value={fmtTime(displayUser.created_at)} />
            </div>
            <div className="mt-4">
              <Button variant="outline" size="sm" onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" /> Sign out
              </Button>
            </div>
          </>
        ) : (
          <LoadingState label="Loading your account…" />
        )}
      </SectionCard>

      <SectionCard
        title="Active polyhouse"
        description="Every page in the workspace is scoped to this polyhouse."
      >
        {isLoading ? (
          <LoadingState label="Loading farms…" />
        ) : error ? (
          <ErrorState error={error} onRetry={refetch} />
        ) : polyhouses.length === 0 ? (
          <EmptyState
            title="No polyhouses yet"
            description="Create a farm and a polyhouse below to start monitoring real data."
          />
        ) : (
          <div className="flex flex-wrap gap-2">
            {polyhouses.map((p) => (
              <Button
                key={p.id}
                size="sm"
                variant={p.id === activeId ? "default" : "outline"}
                onClick={() => setActiveId(p.id)}
              >
                {p.name}
              </Button>
            ))}
          </div>
        )}
      </SectionCard>

      <SectionCard title="Farms" description="Owned farms returned by GET /farms.">
        {farms.length > 0 ? (
          <div className="mb-4 space-y-2">
            {farms.map((f) => (
              <KeyValue
                key={f.id}
                label={f.name}
                value={`${f.location_label ?? "no location"} · ${f.polyhouses?.length ?? 0} polyhouse(s)`}
              />
            ))}
          </div>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="farm-name">Farm name</Label>
            <Input id="farm-name" value={farmName} onChange={(e) => setFarmName(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="farm-loc">Location label (optional)</Label>
            <Input id="farm-loc" value={farmLocation} onChange={(e) => setFarmLocation(e.target.value)} />
          </div>
        </div>
        {createFarm.error ? (
          <div className="mt-3">
            <ErrorState error={createFarm.error} onRetry={() => createFarm.reset()} />
          </div>
        ) : null}
        <div className="mt-4">
          <Button
            size="sm"
            disabled={!farmName.trim() || createFarm.isPending}
            onClick={() => createFarm.mutate()}
          >
            <Plus className="mr-2 h-4 w-4" />
            {createFarm.isPending ? "Creating…" : "Create farm"}
          </Button>
        </div>
      </SectionCard>

      <SectionCard title="Polyhouses" description="Add a polyhouse to one of your farms.">
        {farms.length === 0 ? (
          <p className="text-sm text-muted-foreground">Create a farm first.</p>
        ) : (
          <>
            <div className="mb-3 flex flex-wrap gap-2">
              {farms.map((f) => (
                <Button
                  key={f.id}
                  size="sm"
                  variant={f.id === phFarmId ? "default" : "outline"}
                  onClick={() => setPhFarmId(f.id)}
                >
                  {f.name}
                </Button>
              ))}
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="ph-name">Polyhouse name</Label>
                <Input id="ph-name" value={phName} onChange={(e) => setPhName(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ph-area">Area in m² (optional)</Label>
                <Input
                  id="ph-area"
                  inputMode="decimal"
                  value={phArea}
                  onChange={(e) => setPhArea(e.target.value)}
                />
              </div>
            </div>
            {createPolyhouse.error ? (
              <div className="mt-3">
                <ErrorState error={createPolyhouse.error} onRetry={() => createPolyhouse.reset()} />
              </div>
            ) : null}
            <div className="mt-4">
              <Button
                size="sm"
                disabled={!phFarmId || !phName.trim() || createPolyhouse.isPending}
                onClick={() => createPolyhouse.mutate()}
              >
                <Plus className="mr-2 h-4 w-4" />
                {createPolyhouse.isPending ? "Creating…" : "Create polyhouse"}
              </Button>
            </div>
          </>
        )}
      </SectionCard>

      <SectionCard title="Backend connection" description="Where this frontend sends every request.">
        <KeyValue label="API base URL" value={<code className="text-xs">{API_BASE_URL}</code>} />
        <p className="mt-3 text-xs text-muted-foreground">
          Configured through the <code>VITE_API_BASE_URL</code> environment variable at build time.
        </p>
      </SectionCard>

      {DEMO_MODE ? (
        <SectionCard
          title="Processing Settings"
          description="Current demo mode configuration."
          action={<Pill tone="warning" className="text-[10px]">{DEMO_BADGE}</Pill>}
        >
          <div className="grid gap-x-8 sm:grid-cols-2">
            <KeyValue label="Processing Mode" value={demoProcessingSettings.processingMode} />
            <KeyValue label="Image Analysis" value={demoProcessingSettings.imageAnalysis} />
            <KeyValue label="Disease Detection" value={demoProcessingSettings.diseaseDetection} />
            <KeyValue label="Irrigation Analysis" value={demoProcessingSettings.irrigationAnalysis} />
            <KeyValue label="Forecast Analysis" value={demoProcessingSettings.forecastAnalysis} />
            <KeyValue label="Sensor Analysis" value={demoProcessingSettings.sensorAnalysis} />
            <KeyValue label="Recommendation Engine" value={demoProcessingSettings.recommendationEngine} />
            <KeyValue label="Data Source" value={demoProcessingSettings.dataSource} />
            <KeyValue label="Backend" value={demoProcessingSettings.backend} />
            <KeyValue label="ML Model" value={demoProcessingSettings.mlModel} />
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}
