import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Small presentation primitives shared across the workspace pages.
 * Colours come exclusively from the design-system tokens.
 */

export function StatCard({
  label,
  value,
  unit,
  icon,
  footnote,
}: {
  label: string;
  value: string;
  unit?: string;
  icon?: ReactNode;
  footnote?: string;
}) {
  return (
    <div className="surface-panel p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
        {icon ? <span className="text-primary">{icon}</span> : null}
      </div>
      <p className="mt-3 text-2xl font-semibold text-foreground">
        {value}
        {unit ? <span className="ml-1 text-sm font-normal text-muted-foreground">{unit}</span> : null}
      </p>
      {footnote ? <p className="mt-1 text-xs text-muted-foreground">{footnote}</p> : null}
    </div>
  );
}

const TONE: Record<string, string> = {
  neutral: "bg-secondary text-secondary-foreground",
  info: "bg-accent text-accent-foreground",
  success: "bg-[var(--success)]/12 text-[var(--success)]",
  warning: "bg-[var(--warning)]/15 text-[var(--warning-foreground)]",
  danger: "bg-destructive/10 text-destructive",
};

export function Pill({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: keyof typeof TONE;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        TONE[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function severityTone(severity: string): keyof typeof TONE {
  const s = severity.toLowerCase();
  if (s === "critical" || s === "high") return "danger";
  if (s === "medium") return "warning";
  if (s === "low") return "info";
  return "neutral";
}

export function urgencyTone(urgency: string): keyof typeof TONE {
  const u = urgency.toLowerCase();
  if (u === "critical" || u === "high") return "danger";
  if (u === "medium") return "warning";
  if (u === "low") return "info";
  return "neutral";
}

export function statusTone(status: string): keyof typeof TONE {
  const s = status.toLowerCase();
  if (s === "ready" || s === "model_available" || s === "resolved") return "success";
  if (s === "not_yet_trained" || s === "model_not_trained" || s === "unavailable") return "warning";
  if (s === "active") return "danger";
  return "neutral";
}

/**
 * Layer label — the project deliberately keeps MEASURED DATA, MODEL
 * PREDICTION, RULE-BASED DECISION and RECOMMENDATION visually distinct.
 */
export function LayerLabel({
  layer,
}: {
  layer: "measured" | "prediction" | "rule" | "recommendation";
}) {
  const map = {
    measured: { text: "MEASURED DATA", tone: "info" as const },
    prediction: { text: "MODEL PREDICTION", tone: "success" as const },
    rule: { text: "RULE-BASED DECISION", tone: "warning" as const },
    recommendation: { text: "RECOMMENDATION", tone: "neutral" as const },
  };
  const { text, tone } = map[layer];
  return (
    <Pill tone={tone} className="tracking-wide">
      {text}
    </Pill>
  );
}

export function KeyValue({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-border/60 py-2 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

export function SectionCard({
  title,
  description,
  action,
  children,
  className,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("surface-panel p-4 sm:p-6", className)}>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">{title}</h2>
          {description ? (
            <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{description}</p>
          ) : null}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
