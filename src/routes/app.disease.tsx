import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ImageUp, Microscope, CheckCircle, AlertTriangle, Shield, Stethoscope, ShieldCheck } from "lucide-react";
import { DEMO_MODE, DEMO_BADGE, demoDiseaseInfo, demoPredictionResponse, demoDiseaseHistory, demoDiseaseStatus } from "@/lib/demo-data";
import { PageHeader } from "@/components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "@/components/states";
import { KeyValue, LayerLabel, Pill, SectionCard, statusTone } from "@/components/data-bits";
import { Button } from "@/components/ui/button";
import { api, type DiseasePredictionResponse } from "@/lib/api";
import { fmt, fmtTime } from "@/lib/features";
import { usePolyhouse } from "@/lib/polyhouse";

export const Route = createFileRoute("/app/disease")({
  head: () => ({
    meta: [
      { title: "Disease analysis — Smart Polyhouse" },
      {
        name: "description",
        content: "Upload a leaf image and get a real plant-disease classification result.",
      },
      { property: "og:title", content: "Disease analysis — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Upload a leaf image and get a real plant-disease classification result.",
      },
    ],
  }),
  component: DiseasePage,
});

function DiseasePage() {
  const { activeId, active } = usePolyhouse();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const status = useQuery({
    queryKey: ["disease-status"],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoDiseaseStatus) : () => api.diseaseStatus(),
  });
  const history = useQuery({
    queryKey: ["disease-history", activeId],
    queryFn: DEMO_MODE ? () => Promise.resolve(demoDiseaseHistory) : () => api.diseaseHistory(activeId!),
    enabled: DEMO_MODE || !!activeId,
    retry: false,
  });

  const predict = useMutation<DiseasePredictionResponse, unknown, File>({
    mutationFn: DEMO_MODE
      ? () => new Promise<DiseasePredictionResponse>((resolve) => setTimeout(() => resolve(demoPredictionResponse), 1500))
      : (f) => api.diseasePredict(f, activeId ?? undefined, 3),
    onSuccess: () => { if (!DEMO_MODE) void history.refetch(); },
  });

  const available = status.data?.status === "MODEL_AVAILABLE";
  const result = predict.data;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageHeader
        title="Disease analysis"
        description={`Leaf image classification${active ? ` for ${active.name}` : ""}, backed by the trained CNN.`}
      />

      {status.isLoading ? <LoadingState label="Checking model availability…" /> : null}
      {status.error ? <ErrorState error={status.error} onRetry={() => void status.refetch()} /> : null}

      {status.data ? (
        <SectionCard
          title="Model availability"
          description="Reported live by GET /disease/status."
          action={<Pill tone={statusTone(status.data.status)}>{status.data.status}</Pill>}
        >
          <div className="grid gap-x-8 sm:grid-cols-2">
            <KeyValue label="Model type" value={status.data.model_type ?? "—"} />
            <KeyValue label="Version" value={status.data.version ?? "—"} />
          </div>
          {status.data.message ? (
            <p className="mt-3 text-sm text-muted-foreground">{status.data.message}</p>
          ) : null}
          {!available ? (
            <div className="mt-4 rounded-lg border border-[var(--warning)]/40 bg-[var(--warning)]/10 p-4 text-sm text-[var(--warning-foreground)]">
              The disease model is not available, so prediction is disabled. No placeholder result is
              shown — the backend must serve a trained model before this page can classify images.
            </div>
          ) : null}
        </SectionCard>
      ) : null}

      <SectionCard
        title="Leaf image"
        description="The image is sent to POST /disease/predict; nothing is stored locally."
        action={<LayerLabel layer="measured" />}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null);
            predict.reset();
          }}
        />
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="flex h-44 w-full max-w-xs items-center justify-center overflow-hidden rounded-xl border border-dashed border-border bg-secondary/40 transition-colors hover:bg-secondary"
          >
            {preview ? (
              <img src={preview} alt="Selected leaf" className="h-full w-full object-cover" />
            ) : (
              <span className="flex flex-col items-center gap-2 text-sm text-muted-foreground">
                <ImageUp className="h-6 w-6" />
                Choose an image
              </span>
            )}
          </button>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              {file ? `${file.name} · ${(file.size / 1024).toFixed(0)} KB` : "No file selected."}
            </p>
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={!file || (!DEMO_MODE && !available) || predict.isPending}
                onClick={() => file && predict.mutate(file)}
              >
                {predict.isPending ? "Analysing…" : "Predict disease"}
              </Button>
              {file ? (
                <Button variant="outline" onClick={() => { setFile(null); predict.reset(); }}>
                  Clear
                </Button>
              ) : null}
            </div>
          </div>
        </div>
      </SectionCard>

      {predict.error ? <ErrorState error={predict.error} onRetry={() => predict.reset()} /> : null}

      {result ? (
        <SectionCard
          title="Classification result"
          description="Direct model output, including the top-k alternatives."
          action={
            <div className="flex items-center gap-2">
              {DEMO_MODE ? <Pill tone="warning" className="text-[10px]">{DEMO_BADGE}</Pill> : null}
              <LayerLabel layer="prediction" />
            </div>
          }
        >
          <div className="grid gap-x-8 sm:grid-cols-2">
            <KeyValue label="Predicted class" value={result.prediction.class} />
            <KeyValue label="Confidence" value={fmt(result.prediction.confidence * 100, 2, " %")} />
            <KeyValue label="Crop" value={result.prediction.canonical_crop ?? "—"} />
            <KeyValue label="Disease" value={result.prediction.canonical_disease ?? "—"} />
            <KeyValue
              label="Model"
              value={`${result.model.name} · v${result.model.version} · ${result.model.status}`}
            />
          </div>
          <div className="mt-4 space-y-2">
            <p className="text-sm text-muted-foreground">Top alternatives</p>
            {result.top_k.map((k) => (
              <KeyValue key={k.class} label={k.class} value={fmt(k.confidence * 100, 2, " %")} />
            ))}
          </div>
        </SectionCard>
      ) : null}

      {/* Demo: Extended disease information */}
      {DEMO_MODE && result ? (
        <>
          <SectionCard
            title="Possible Cause"
            description="Why this disease may have occurred."
            action={<Pill tone="warning" className="text-[10px]">Prototype Demo • Synthetic Result</Pill>}
          >
            <p className="text-sm text-foreground leading-relaxed">{demoDiseaseInfo.cause}</p>
            <div className="mt-3 grid gap-x-8 sm:grid-cols-2">
              <KeyValue label="Severity" value={demoDiseaseInfo.severity} />
              <KeyValue label="Analysis Status" value={demoDiseaseInfo.analysisStatus} />
            </div>
          </SectionCard>

          <SectionCard
            title="Treatment Recommendation"
            description="Guidance for managing the detected condition."
            action={<Pill tone="info" className="text-[10px]">Advisory Only</Pill>}
          >
            <p className="text-sm text-foreground leading-relaxed">{demoDiseaseInfo.treatment}</p>
            <div className="mt-3">
              <KeyValue label="Treatment Type" value={demoDiseaseInfo.treatmentType} />
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              This is a prototype demonstration. Treatment decisions should follow local agricultural guidance.
            </p>
          </SectionCard>

          <SectionCard
            title="Preventive Measures"
            description="Steps to reduce future disease risk."
          >
            <ul className="space-y-2">
              {demoDiseaseInfo.prevention.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-foreground">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  {item}
                </li>
              ))}
            </ul>
          </SectionCard>
        </>
      ) : null}

      <SectionCard
        title="Prediction history"
        description="Previous predictions stored for this polyhouse."
        action={<LayerLabel layer="recommendation" />}
      >
        {!activeId ? (
          <EmptyState title="No polyhouse selected" description="History is scoped to a polyhouse." />
        ) : history.isLoading ? (
          <LoadingState label="Loading history…" />
        ) : history.error ? (
          <ErrorState error={history.error} onRetry={() => void history.refetch()} />
        ) : (history.data?.predictions.length ?? 0) === 0 ? (
          <EmptyState
            icon={<Microscope className="h-5 w-5" />}
            title="No predictions recorded"
            description="Analysed images will be listed here once the backend stores them."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="py-2 font-medium">When</th>
                  <th className="py-2 font-medium">Class</th>
                  <th className="py-2 font-medium">Crop</th>
                  <th className="py-2 text-right font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {history.data!.predictions.map((p) => (
                  <tr key={p.id} className="border-b border-border/60 last:border-0">
                    <td className="py-2 text-muted-foreground">{fmtTime(p.created_at)}</td>
                    <td className="py-2 text-foreground">{p.predicted_class}</td>
                    <td className="py-2 text-muted-foreground">{p.canonical_crop ?? "—"}</td>
                    <td className="py-2 text-right text-foreground">
                      {fmt(p.confidence * 100, 2, " %")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
