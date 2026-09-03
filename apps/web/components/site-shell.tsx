import Link from "next/link";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard" },
  { href: "/story-map", label: "Story Map" },
  { href: "/ctd", label: "CTD Engine" },
  { href: "/dossiers", label: "Dossier Export" },
] as const;

type SiteShellProps = {
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
  wide?: boolean;
};

export function SiteShell({
  children,
  title,
  description,
  className,
  wide = false,
}: SiteShellProps) {
  return (
    <div className="min-h-screen bg-background">
      <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-center text-xs font-medium text-amber-900">
        TRAINING / INTERNAL REVIEW ONLY — NOT A REGULATORY SUBMISSION
      </div>

      <header className="border-b bg-card/80 backdrop-blur">
        <div
          className={cn(
            "mx-auto flex flex-col gap-4 px-6 py-4 sm:flex-row sm:items-center sm:justify-between",
            wide ? "max-w-6xl" : "max-w-5xl",
          )}
        >
          <div>
            <Link href="/" className="text-lg font-semibold tracking-tight text-foreground">
              Regulatory-AugSys
            </Link>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Evidence capture · Story maps · CTD mapping · dossier export
            </p>
          </div>
          <nav className="flex flex-wrap gap-1">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main
        className={cn(
          "mx-auto space-y-8 px-6 py-8",
          wide ? "max-w-6xl" : "max-w-5xl",
          className,
        )}
      >
        {title ? (
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
            {description ? (
              <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
                {description}
              </p>
            ) : null}
          </div>
        ) : null}
        {children}
      </main>
    </div>
  );
}
