import Link from "next/link";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Overview" },
  { href: "/ctd", label: "Document Intake" },
  { href: "/regulatory-intelligence", label: "Intelligence" },
  { href: "/obligations", label: "Obligations" },
  { href: "/clarifications", label: "Clarifications" },
  { href: "/dossiers", label: "Dossiers" },
] as const;

type SiteShellProps = {
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
  wide?: boolean;
};

export function SiteShell({ children, title, description, className, wide = false }: SiteShellProps) {
  return (
    <div className="maras-app min-h-screen">
      <div className="maras-safety-banner">
        <span className="maras-banner-dot" />
        TRAINING / INTERNAL REVIEW ONLY · NOT A REGULATORY SUBMISSION
      </div>
      <header className="maras-header">
        <div className={cn("maras-header-inner mx-auto px-5 py-4", wide ? "max-w-[1440px]" : "max-w-7xl")}>
          <div className="maras-brand">
            <Link href="/" className="maras-brand-mark" aria-label="MARAS home">M</Link>
            <div>
              <Link href="/" className="maras-brand-name">MARAS <span>INTELLIGENCE</span></Link>
              <p className="maras-brand-caption">Regulatory assurance workspace</p>
            </div>
          </div>
          <nav className="maras-nav" aria-label="Main navigation">
            {NAV_ITEMS.map((item) => (
              <Link key={item.href} href={item.href} className="maras-nav-link">
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="maras-header-status"><span /> LOCAL-FIRST WORKSPACE</div>
        </div>
      </header>
      <main className={cn("maras-main mx-auto px-5 py-8", wide ? "max-w-[1440px]" : "max-w-7xl", className)}>
        {title ? (
          <div className="maras-page-heading">
            <div className="maras-page-eyebrow">MARAS / WORKSPACE</div>
            <h1>{title}</h1>
            {description ? <p>{description}</p> : null}
          </div>
        ) : null}
        {children}
        <footer className="maras-global-footer">
          <span>MARAS · REGULATORY INTELLIGENCE</span>
          <span>Evidence-led workflows · Human review remains mandatory</span>
        </footer>
      </main>
    </div>
  );
}
