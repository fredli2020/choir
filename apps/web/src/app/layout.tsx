import type { Metadata } from "next";
import { Cormorant_Garamond, Manrope } from "next/font/google";

import { AppProviders } from "@/components/app/providers";
import { isClerkConfigured } from "@/lib/server-env";

import "./globals.css";

const manrope = Manrope({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

const cormorantGaramond = Cormorant_Garamond({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-display",
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Choir App",
  description:
    "Modern choir operations software for organizations, members, events, and attendance.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={[manrope.variable, cormorantGaramond.variable].join(" ")}>
        <AppProviders clerkEnabled={isClerkConfigured()}>{children}</AppProviders>
      </body>
    </html>
  );
}
