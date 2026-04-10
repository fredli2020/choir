import type { ReactNode } from "react";
import Link from "next/link";
import {
  CalendarRange,
  FolderKanban,
  LayoutDashboard,
  NotebookTabs,
  ShieldCheck,
  UserCircle2,
  Users,
} from "lucide-react";
import { UserButton } from "@clerk/nextjs";

import { NavLink } from "@/components/app/nav-link";
import { Button } from "@/components/ui/button";
import { formatRole } from "@/lib/format";
import type { CurrentUser, CurrentUserContext, OrganizationSummary } from "@/types/api";

type AppShellProps = {
  children: ReactNode;
  currentUser: CurrentUser;
  context: CurrentUserContext;
  organizations: OrganizationSummary[];
};

export function AppShell({ children, currentUser, context, organizations }: AppShellProps) {
  const organization = context.organization;
  const membership = context.membership;
  const permissions = context.permissions;

  if (!organization || !membership) {
    return <>{children}</>;
  }

  const navItems = [
    {
      href: `/app/${organization.id}`,
      label: "Overview",
      icon: <LayoutDashboard className="h-4 w-4" />,
      visible: true,
    },
    {
      href: `/app/${organization.id}/members`,
      label: "Members",
      icon: <Users className="h-4 w-4" />,
      visible: permissions.can_view_members,
    },
    {
      href: `/app/${organization.id}/directory`,
      label: "Directory",
      icon: <NotebookTabs className="h-4 w-4" />,
      visible: permissions.can_view_directory,
    },
    {
      href: `/app/${organization.id}/events`,
      label: "Events",
      icon: <CalendarRange className="h-4 w-4" />,
      visible: permissions.can_view_events || permissions.can_view_relevant_events,
    },
    {
      href: `/app/${organization.id}/profile`,
      label: "My profile",
      icon: <UserCircle2 className="h-4 w-4" />,
      visible: permissions.can_self_edit_profile,
    },
  ].filter((item) => item.visible);

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 pb-12 pt-6 sm:px-8 lg:px-10">
      <header className="glass-panel ambient-border sticky top-5 z-20 flex flex-col gap-4 rounded-[2rem] px-5 py-5 shadow-[0_20px_48px_rgba(35,34,29,0.09)] lg:flex-row lg:items-center lg:justify-between lg:px-6">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-[0_14px_28px_rgba(16,66,91,0.22)]">
              <FolderKanban className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                {organization.name}
              </p>
              <p className="text-sm text-foreground/72">{formatRole(membership.role)} workspace</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {organizations.map((entry) => (
              <Button key={entry.organization.id} asChild variant={entry.organization.id === organization.id ? "default" : "ghost"}>
                <Link href={`/app/${entry.organization.id}`}>{entry.organization.name}</Link>
              </Button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3 self-end lg:self-auto">
          <div className="hidden rounded-2xl border border-white/60 bg-white/72 px-4 py-3 text-right backdrop-blur sm:block">
            <p className="text-sm font-semibold text-foreground">{currentUser.name || currentUser.email}</p>
            <p className="text-xs uppercase tracking-[0.22em] text-muted-foreground">{formatRole(membership.role)}</p>
          </div>
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/60 bg-white/72 backdrop-blur">
            <UserButton appearance={{ elements: { avatarBox: "h-8 w-8" } }} />
          </div>
        </div>
      </header>

      <div className="mt-8 grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="space-y-5 lg:sticky lg:top-32 lg:h-fit">
          <div className="glass-panel ambient-border rounded-[2rem] p-5 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">
              Navigation
            </p>
            <div className="mt-4 grid gap-3">
              {navItems.map((item) => (
                <NavLink key={item.href} href={item.href} label={item.label} icon={item.icon} />
              ))}
            </div>
          </div>

          <div className="glass-panel ambient-border rounded-[2rem] p-5 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
            <div className="flex items-start gap-3">
              <div className="mt-1 flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                  Permissions
                </p>
                <p className="mt-2 text-sm leading-7 text-foreground/78">
                  The UI only exposes surfaces your Django permission layer already allows for this organization.
                </p>
              </div>
            </div>
          </div>
        </aside>

        <div className="min-w-0">{children}</div>
      </div>
    </div>
  );
}
