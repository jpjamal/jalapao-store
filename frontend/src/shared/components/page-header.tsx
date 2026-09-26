import Link from "next/link";
import { ChevronLeft } from "lucide-react";

/* Cabeçalho padrão das páginas: título, descrição e ações. No celular as ações descem para
   baixo do título e ocupam a largura toda; no computador ficam à direita. */
export function PageHeader({
  title,
  description,
  eyebrow,
  actions,
  back,
}: {
  title: string;
  description?: React.ReactNode;
  eyebrow?: string;
  actions?: React.ReactNode;
  back?: { href: string; label: string };
}) {
  return (
    <header className="mb-6 md:mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {back && (
          <Link href={back.href} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-3 py-1">
            <ChevronLeft size={16} aria-hidden /> {back.label}
          </Link>
        )}
        {eyebrow && (
          <p className="text-xs tracking-[.2em] uppercase text-muted-foreground mb-2">
            {eyebrow}
          </p>
        )}
        <h1 className="mb-2">{title}</h1>
        {description && (
          <p className="text-muted-foreground max-w-2xl">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex flex-col gap-2 sm:flex-row sm:shrink-0 [&>*]:w-full sm:[&>*]:w-auto">
          {actions}
        </div>
      )}
    </header>
  );
}
