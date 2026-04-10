"use client";

import type { ReactNode } from "react";
import { ClerkProvider } from "@clerk/nextjs";

import { appConfig } from "@/lib/config";

type AppProvidersProps = {
  children: ReactNode;
  clerkEnabled: boolean;
};

export function AppProviders({ children, clerkEnabled }: AppProvidersProps) {
  if (!clerkEnabled) {
    return <>{children}</>;
  }

  return (
    <ClerkProvider signInUrl={appConfig.signInUrl} signUpUrl={appConfig.signUpUrl}>
      {children}
    </ClerkProvider>
  );
}
