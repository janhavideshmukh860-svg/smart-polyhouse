import { Link, useNavigate } from "@tanstack/react-router";
import { useState, type ReactNode } from "react";
import {
  BellRing,
  Brain,
  Droplets,
  Gauge,
  History,
  Leaf,
  LineChart,
  Lightbulb,
  LogOut,
  Menu,
  Microscope,
  Settings,
  Thermometer,
  X,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { usePolyhouse } from "@/lib/polyhouse";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const NAV = [
  { to: "/app", label: "Dashboard", icon: Gauge, exact: true },
  { to: "/app/disease", label: "Disease Analysis", icon: Microscope },
  { to: "/app/irrigation", label: "Irrigation", icon: Droplets },
  { to: "/app/forecast", label: "Forecast", icon: LineChart },
  { to: "/app/sensors", label: "Sensors", icon: Thermometer },
  { to: "/app/recommendations", label: "Recommendations", icon: Lightbulb },
  { to: "/app/alerts", label: "Alerts", icon: BellRing },
  { to: "/app/history", label: "History", icon: History },
  { to: "/app/models", label: "Models", icon: Brain },
  { to: "/app/settings", label: "Profile & Settings", icon: Settings },
] as const;

function PolyhouseSelector() {
  const { polyhouses, activeId, setActiveId, isLoading } = usePolyhouse();
  if (isLoading || polyhouses.length === 0) return null;
  return (
    <Select {...(activeId ? { value: activeId } : {})} onValueChange={setActiveId}>
      <SelectTrigger className="w-[190px]" aria-label="Active polyhouse">
        <SelectValue placeholder="Select polyhouse" />
      </SelectTrigger>
      <SelectContent>
        {polyhouses.map((p) => (
          <SelectItem key={p.id} value={p.id}>
            {p.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const nav = (
    <nav className="flex flex-col gap-1 p-3">
      {NAV.map(({ to, label, icon: Icon, ...rest }) => (
        <Link
          key={to}
          to={to}
          activeOptions={{ exact: "exact" in rest ? true : false }}
          onClick={() => setOpen(false)}
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-sidebar-foreground transition-colors hover:bg-sidebar-accent"
          activeProps={{
            className:
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm bg-sidebar-primary text-sidebar-primary-foreground font-medium",
          }}
        >
          <Icon className="h-4 w-4" />
          {label}
        </Link>
      ))}
    </nav>
  );

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar lg:flex">
        <Link to="/" className="flex items-center gap-2.5 border-b border-sidebar-border px-5 py-4">
          <span className="rounded-lg bg-primary p-1.5 text-primary-foreground">
            <Leaf className="h-4 w-4" />
          </span>
          <span className="text-sm font-semibold tracking-tight text-sidebar-foreground">
            SMART POLYHOUSE
          </span>
        </Link>
        <div className="flex-1 overflow-y-auto">{nav}</div>
        <div className="border-t border-sidebar-border p-3">
          <p className="truncate px-3 pb-2 text-xs text-muted-foreground">
            {user?.full_name || user?.email}
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-3"
            onClick={() => {
              logout();
              void navigate({ to: "/" });
            }}
          >
            <LogOut className="h-4 w-4" /> Log out
          </Button>
        </div>
      </aside>

      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-foreground/30"
            onClick={() => setOpen(false)}
            aria-hidden
          />
          <div className="absolute inset-y-0 left-0 w-72 overflow-y-auto bg-sidebar">
            <div className="flex items-center justify-between border-b border-sidebar-border px-5 py-4">
              <span className="text-sm font-semibold text-sidebar-foreground">SMART POLYHOUSE</span>
              <Button variant="ghost" size="icon" onClick={() => setOpen(false)} aria-label="Close menu">
                <X className="h-4 w-4" />
              </Button>
            </div>
            {nav}
            <div className="border-t border-sidebar-border p-3">
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start gap-3"
                onClick={() => {
                  logout();
                  void navigate({ to: "/" });
                }}
              >
                <LogOut className="h-4 w-4" /> Log out
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-border bg-background/90 px-4 py-3 backdrop-blur sm:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="ml-auto flex items-center gap-3">
            <PolyhouseSelector />
          </div>
        </header>
        <main className="px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
      {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
    </div>
  );
}
