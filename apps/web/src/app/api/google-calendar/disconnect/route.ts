import { NextRequest, NextResponse } from "next/server";

import { getServerAuthState } from "@/lib/auth";
import { appConfig } from "@/lib/config";

export async function POST(request: NextRequest) {
  const formData = await request.formData();
  const orgId = String(formData.get("orgId") ?? "");
  const redirectUrl = new URL(`/app/${orgId}/settings/google-calendar`, request.url);

  if (!orgId) {
    return NextResponse.redirect(new URL("/app?google_calendar=error&detail=missing_org", request.url));
  }

  const authState = await getServerAuthState();
  if (!authState.userId || !authState.token) {
    return NextResponse.redirect(new URL("/sign-in", request.url));
  }

  const response = await fetch(
    `${appConfig.apiBaseUrl}/api/orgs/${orgId}/integrations/google-calendar/disconnect`,
    {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${authState.token}`,
      },
      cache: "no-store",
    },
  );

  redirectUrl.searchParams.set("google_calendar", response.ok ? "disconnected" : "error");
  if (!response.ok) {
    redirectUrl.searchParams.set("detail", "disconnect_failed");
  }
  return NextResponse.redirect(redirectUrl);
}
