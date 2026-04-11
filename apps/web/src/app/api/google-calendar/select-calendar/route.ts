import { NextRequest, NextResponse } from "next/server";

import { getServerAuthState } from "@/lib/auth";
import { appConfig } from "@/lib/config";

export async function POST(request: NextRequest) {
  const formData = await request.formData();
  const orgId = String(formData.get("orgId") ?? "");
  const calendarId = String(formData.get("calendarId") ?? "");
  const redirectUrl = new URL(`/app/${orgId}/settings/google-calendar`, request.url);

  if (!orgId || !calendarId) {
    redirectUrl.searchParams.set("google_calendar", "error");
    redirectUrl.searchParams.set("detail", "missing_calendar");
    return NextResponse.redirect(redirectUrl);
  }

  const authState = await getServerAuthState();
  if (!authState.userId || !authState.token) {
    return NextResponse.redirect(new URL("/sign-in", request.url));
  }

  const response = await fetch(
    `${appConfig.apiBaseUrl}/api/orgs/${orgId}/integrations/google-calendar/calendar`,
    {
      method: "PUT",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${authState.token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ calendar_id: calendarId }),
      cache: "no-store",
    },
  );

  redirectUrl.searchParams.set("google_calendar", response.ok ? "calendar_selected" : "error");
  if (!response.ok) {
    redirectUrl.searchParams.set("detail", "calendar_selection_failed");
  }
  return NextResponse.redirect(redirectUrl);
}
