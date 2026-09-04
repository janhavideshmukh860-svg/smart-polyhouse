import { createFileRoute, Outlet, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import AppShell from "@/components/AppShell";
import { DEMO_MODE } from "@/lib/demo-data";
import { LoadingState } from "@/components/states";
import { useAuth } from "@/lib/auth";
import { PolyhouseProvider } from "@/lib/polyhouse";

export const Route = createFileRoute("/app")({
  head: () => ({
    meta: [
      { title: "Workspace — Smart Polyhouse" },
      {
        name: "description",
        content: "Monitor your polyhouse environment, irrigation and plant health.",
      },
      { property: "og:title", content: "Workspace — Smart Polyhouse" },
      {
        property: "og:description",
        content: "Monitor your polyhouse environment, irrigation and plant health.",
      },
    ],
  }),
  component: AppLayout,
});

function AppLayout() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!DEMO_MODE && !loading && !user) {
      void navigate({ to: "/auth/login", replace: true });
    }
  }, [loading, navigate, user]);

  if (loading) {
    return <LoadingState label="Checking your workspace…" />;
  }

  if (!DEMO_MODE && !user) {
    return <LoadingState label="Redirecting to sign in…" />;
  }

  return (
    <PolyhouseProvider>
      <AppShell>
        <Outlet />
      </AppShell>
    </PolyhouseProvider>
  );
}