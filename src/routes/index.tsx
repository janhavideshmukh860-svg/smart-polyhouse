import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { lazy, useEffect, type ReactNode } from "react";
import {
  Activity,
  ArrowRight,
  BellRing,
  Brain,
  Cpu,
  Droplets,
  Gauge,
  Leaf,
  LineChart,
  Lightbulb,
  Microscope,
  Recycle,
  ShieldCheck,
  Sprout,
  Thermometer,
} from "lucide-react";
import ClientOnly from "@/components/ClientOnly";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

import { DEMO_MODE } from "@/lib/demo-data";

const PlantScene = lazy(() => import("@/components/PlantScene"));

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Smart Polyhouse — AI Plant Health & Smart Irrigation" },
      {
        name: "description",
        content:
          "Smart Polyhouse monitors your environment, forecasts soil moisture with trained ML models and turns readings into explainable irrigation decisions.",
      },
      { property: "og:title", content: "Smart Polyhouse — AI Plant Health & Smart Irrigation" },
      {
        property: "og:description",
        content:
          "Intelligent plant health, environmental monitoring and smart irrigation for more sustainable cultivation. Built by Team Binary Shogun.",
      },
    ],
  }),
  component: Landing,
});

function Section({
  id,
  eyebrow,
  title,
  description,
  children,
  tone = "default",
}: {
  id?: string;
  eyebrow?: string;
  title: string;
  description?: string;
  children?: ReactNode;
  tone?: "default" | "muted";
}) {
  return (
    <section
      id={id}
      className={
        tone === "muted"
          ? "border-y border-border bg-secondary/40 py-20 sm:py-24"
          : "py-20 sm:py-24"
      }
    >
      <div className="mx-auto max-w-6xl px-5">
        <div className="max-w-2xl">
          {eyebrow ? (
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
              {eyebrow}
            </p>
          ) : null}
          <h2 className="mt-3 text-3xl font-semibold text-foreground sm:text-4xl">{title}</h2>
          {description ? (
            <p className="mt-4 text-base leading-relaxed text-muted-foreground">{description}</p>
          ) : null}
        </div>
        {children ? <div className="mt-12">{children}</div> : null}
      </div>
    </section>
  );
}

function FeatureCard({
  icon,
  title,
  body,
}: {
  icon: ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="surface-panel h-full p-6 transition-shadow hover:shadow-[var(--shadow-lift)]">
      <div className="inline-flex rounded-lg bg-secondary p-2.5 text-primary">{icon}</div>
      <h3 className="mt-4 text-lg font-semibold text-foreground">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{body}</p>
    </div>
  );
}

const WORKFLOW = [
  { icon: <Sprout className="h-5 w-5" />, label: "Plant & environment" },
  { icon: <Cpu className="h-5 w-5" />, label: "Sensors + image capture" },
  { icon: <Brain className="h-5 w-5" />, label: "AI / ML processing" },
  { icon: <LineChart className="h-5 w-5" />, label: "Analysis & forecast" },
  { icon: <Gauge className="h-5 w-5" />, label: "Smart decision" },
  { icon: <BellRing className="h-5 w-5" />, label: "Recommendation / alert" },
];

function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3.5">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="rounded-lg bg-primary p-1.5 text-primary-foreground">
              <Leaf className="h-4 w-4" />
            </span>
            <span className="text-sm font-semibold tracking-tight text-foreground">
              SMART POLYHOUSE
            </span>
          </Link>
          <nav className="hidden items-center gap-7 text-sm text-muted-foreground md:flex">
            <a href="#how-it-works" className="transition-colors hover:text-foreground">
              How it works
            </a>
            <a href="#features" className="transition-colors hover:text-foreground">
              Features
            </a>
            <a href="#team" className="transition-colors hover:text-foreground">
              Team
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm">
              <Link to="/auth/login">Sign in</Link>
            </Button>
            <Button asChild size="sm">
              <Link to="/auth/register">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section className="hero-canopy">
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-5 py-20 sm:py-28 lg:grid-cols-[1.15fr_0.85fr]">
          <div className="animate-rise">
            <Badge variant="secondary" className="mb-5 gap-1.5">
              <Leaf className="h-3.5 w-3.5" /> Team Binary Shogun
            </Badge>
            <h1 className="text-4xl font-semibold leading-[1.08] text-foreground sm:text-6xl">
              Smart <span className="text-gradient-leaf">Polyhouse</span>
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted-foreground">
              Intelligent plant health, environmental monitoring and smart irrigation for more
              sustainable cultivation — powered by real sensor data and trained machine-learning
              models.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link to="/auth/register">
                  Get Started <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <a href="#features">Explore Features</a>
              </Button>
            </div>
            <dl className="mt-10 grid max-w-lg grid-cols-3 gap-4 text-sm">
              {[
                ["Calibration R²", "0.803"],
                ["1h forecast R²", "0.898"],
                ["Horizons", "1h · 6h · 12h · 24h"],
              ].map(([k, v]) => (
                <div key={k} className="rounded-lg border border-border bg-card/70 px-3 py-2.5">
                  <dt className="text-xs text-muted-foreground">{k}</dt>
                  <dd className="mt-0.5 font-semibold text-foreground">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="relative h-[300px] w-full sm:h-[380px]">
            <ClientOnly
              fallback={
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  <Sprout className="h-10 w-10 animate-pulse" />
                </div>
              }
            >
              <PlantScene />
            </ClientOnly>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <Section
        id="how-it-works"
        eyebrow="How it works"
        title="From a living plant to an actionable decision"
        description="Every screen in Smart Polyhouse follows the same pipeline — measured state first, model prediction second, rule-based decision last. Nothing is invented in between."
        tone="muted"
      >
        <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {WORKFLOW.map((step, i) => (
            <li key={step.label} className="surface-panel flex items-center gap-4 p-5">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-primary">
                {step.icon}
              </span>
              <div>
                <p className="text-xs font-medium text-muted-foreground">Step {i + 1}</p>
                <p className="font-medium text-foreground">{step.label}</p>
              </div>
            </li>
          ))}
        </ol>
      </Section>

      {/* FEATURES */}
      <Section
        id="features"
        eyebrow="Core features"
        title="One platform for the whole polyhouse"
        description="Each capability is wired to the Smart Polyhouse backend — real endpoints, real model artifacts, honest status when something is not ready yet."
      >
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <FeatureCard
            icon={<Microscope className="h-5 w-5" />}
            title="AI disease detection"
            body="Upload a plant image and get a classification the moment the trained disease model is available. The interface is ready; the model status is reported honestly."
          />
          <FeatureCard
            icon={<Droplets className="h-5 w-5" />}
            title="Smart irrigation"
            body="Combines calibrated moisture, environmental state and the irrigation decision engine into an explainable irrigate / hold recommendation with urgency."
          />
          <FeatureCard
            icon={<LineChart className="h-5 w-5" />}
            title="Moisture forecasting"
            body="Trained gradient-boosted models forecast soil moisture at 1h, 6h, 12h and 24h horizons from the current sensor state."
          />
          <FeatureCard
            icon={<Thermometer className="h-5 w-5" />}
            title="Environment monitoring"
            body="Soil and atmospheric temperature, pressure, sensor voltage and volumetric moisture — current readings plus historical trend charts."
          />
          <FeatureCard
            icon={<Lightbulb className="h-5 w-5" />}
            title="Intelligent recommendations"
            body="Model outputs pass through the rule engine and become recommendations with domain, urgency, reasoning and risk factors."
          />
          <FeatureCard
            icon={<BellRing className="h-5 w-5" />}
            title="Alerts"
            body="Conditions that need attention are raised as alerts you can acknowledge and resolve directly from the dashboard."
          />
        </div>
      </Section>

      {/* DISEASE / IRRIGATION / FORECAST DETAIL */}
      <Section
        eyebrow="AI disease detection"
        title="Plant-health analysis, without guesswork"
        description="Capture or upload a leaf image and the pipeline classifies crop and disease with a confidence score. The disease model is currently NOT_YET_TRAINED — the supplied dataset manifests contain no image bytes — so the app reports that state instead of fabricating a diagnosis."
        tone="muted"
      >
        <div className="surface-panel flex flex-wrap items-center gap-4 p-6">
          <ShieldCheck className="h-6 w-6 text-primary" />
          <p className="max-w-2xl text-sm text-muted-foreground">
            Honest-by-design: when the backend reports a model as unavailable, Smart Polyhouse shows
            a clear preparation state rather than a placeholder prediction.
          </p>
        </div>
      </Section>

      <Section
        eyebrow="Smart irrigation & forecasting"
        title="Measured state, model prediction and rule-based decision — kept separate"
        description="The irrigation view never blurs the three layers. You always see what was measured, what the model predicted, and what rule turned that into a recommendation."
      >
        <div className="grid gap-5 lg:grid-cols-3">
          <FeatureCard
            icon={<Activity className="h-5 w-5" />}
            title="Measured state"
            body="Calibrated volumetric moisture and environmental readings taken from the sensor layer."
          />
          <FeatureCard
            icon={<Brain className="h-5 w-5" />}
            title="Model prediction"
            body="Forecast moisture at 1h (R² 0.898), 6h (0.648), 12h (0.194) and 24h (-0.757). The 24h model does not currently generalise, and we say so."
          />
          <FeatureCard
            icon={<Gauge className="h-5 w-5" />}
            title="Rule-based decision"
            body="Thresholds interpret the forecast into a status, urgency, recommendation text and risk factors you can audit."
          />
        </div>
      </Section>

      {/* SUSTAINABILITY */}
      <Section
        eyebrow="Why Smart Polyhouse"
        title="Grow more with less water and fewer surprises"
        tone="muted"
      >
        <div className="grid gap-5 sm:grid-cols-3">
          <FeatureCard
            icon={<Recycle className="h-5 w-5" />}
            title="Water efficiency"
            body="Irrigate on forecast evidence instead of a fixed schedule, reducing avoidable water use."
          />
          <FeatureCard
            icon={<Leaf className="h-5 w-5" />}
            title="Healthier crops"
            body="Early environmental and plant-health signals mean interventions happen before damage spreads."
          />
          <FeatureCard
            icon={<ShieldCheck className="h-5 w-5" />}
            title="Trustworthy AI"
            body="Every number in the product comes from the backend. No mock data, no invented metrics."
          />
        </div>
      </Section>

      {/* TEAM */}
      <Section
        id="team"
        eyebrow="Meet the team"
        title="Team Binary Shogun"
        description="Built end to end — FastAPI backend, PostgreSQL, trained irrigation models and this interface."
      >
        <div className="grid max-w-2xl gap-5 sm:grid-cols-2">
          {["Janhavi Deshmukh", "Aaditya Gaikwad"].map((name) => (
            <div key={name} className="surface-panel p-6">
              <p className="text-lg font-semibold text-foreground">{name}</p>
              <p className="mt-1 text-sm text-muted-foreground">Team Binary Shogun</p>
            </div>
          ))}
        </div>
      </Section>

      {/* FINAL CTA */}
      <section className="border-t border-border bg-secondary/50 py-20">
        <div className="mx-auto max-w-3xl px-5 text-center">
          <h2 className="text-3xl font-semibold text-foreground sm:text-4xl">
            Bring intelligence into your polyhouse
          </h2>
          <p className="mt-4 text-muted-foreground">
            Create an account, register your farm and polyhouse, and start turning readings into
            decisions.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button asChild size="lg">
              <Link to="/auth/register">Get Started</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link to="/auth/login">Sign in</Link>
            </Button>
          </div>
        </div>
      </section>

      <footer className="border-t border-border py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 text-sm text-muted-foreground sm:flex-row">
          <p className="flex items-center gap-2">
            <Leaf className="h-4 w-4 text-primary" /> Smart Polyhouse
          </p>
          <p>Built by Team Binary Shogun — Janhavi Deshmukh & Aaditya Gaikwad</p>
        </div>
      </footer>
    </div>
  );
}
