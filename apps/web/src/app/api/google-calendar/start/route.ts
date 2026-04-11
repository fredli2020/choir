import { NextRequest, NextResponse } from "next/server";

import { getServerAuthState } from "@/lib/auth";
import { appConfig } from "@/lib/config";

export async function GET(request: NextRequest) {
  const orgId = request.nextUrl.searchParams.get("orgId");
  if (!orgId) {
    return NextResponse.redirect(new URL("/app?google_calendar=error&detail=missing_org", request.url));
  }

  const authState = await getServerAuthState();
  if (!authState.userId || !authState.token) {
    return NextResponse.redirect(new URL("/sign-in", request.url));
  }

  const response = await fetch(
    `${appConfig.apiBaseUrl}/api/orgs/${orgId}/integrations/google-calendar/oauth/start`,
    {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${authState.token}`,
      },
      cache: "no-store",
    },
  );

  const fallbackUrl = new URL(`/app/${orgId}/settings/google-calendar`, request.url);
  if (!response.ok) {
    fallbackUrl.searchParams.set("google_calendar", "error");
    fallbackUrl.searchParams.set("detail", "oauth_start_failed");
    return NextResponse.redirect(fallbackUrl);
  }

  const payload = (await response.json()) as { authorization_url: string };
  return NextResponse.redirect(payload.authorization_url);
}
