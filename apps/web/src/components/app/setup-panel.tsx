import Link from "next/link";
import { ArrowUpRight, Settings2 } from "lucide-react";

import { Button } from "@/components/ui/button";

type SetupPanelProps = {
  title: string;
  description: string;
  body: string;
  ctaHref?: string;
  ctaLabel?: string;
};

export function SetupPanel({
  title,
  description,
  body,
  ctaHref = "/",
  ctaLabel = "Back to landing page",
}: SetupPanelProps) {
  return (
    <div className="mx-auto flex min-h-[70vh] w-full max-w-3xl items-center px-6 py-16 sm:px-8">
      <section className="glass-panel ambient-border w-full rounded-[2.5rem] p-8 shadow-[0_30px_70px_rgba(44,37,29,0.1)] sm:p-10">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <Settings2 className="h-7 w-7" />
          </div>
          <div className="space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.28em] text-muted-foreground">
              Setup required
            </p>
            <h1 className="text-4xl text-primary sm:text-5xl">{title}</h1>
            <p className="max-w-2xl text-lg leading-8 text-muted-foreground">{description}</p>
          </div>
        </div>
        <p className="mt-8 rounded-[1.5rem] border border-primary/10 bg-white/72 p-5 text-sm leading-7 text-foreground/80 backdrop-blur">
          {body}
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild>
            <Link href={ctaHref}>
              {ctaLabel}
              <ArrowUpRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
          <Button asChild variant="secondary">
            <a href="https://clerk.com/docs" target="_blank" rel="noreferrer">
              Clerk setup docs
              <ArrowUpRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
        </div>
      </section>
    </div>
  );
}
