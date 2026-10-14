"use client";

import type { ComponentProps } from "react";
import Link from "next/link";
import {
  Banknote,
  Boxes,
  FilePenLine,
  Image,
  PackageMinus,
  Pencil,
  RefreshCw,
  ShoppingCart,
  SlidersHorizontal,
  Tag,
  Trash2,
  Upload,
  XCircle,
} from "lucide-react";
import { Button, buttonVariants } from "@/shared/ui/button";
import { cn } from "@/shared/lib/utils";

const icons = {
  edit: Pencil,
  delete: Trash2,
  cancel: XCircle,
  label: Tag,
  receive: Banknote,
  pay: Banknote,
  buy: ShoppingCart,
  consume: PackageMinus,
  adjust: SlidersHorizontal,
  photos: Image,
  import: RefreshCw,
  stock: Boxes,
  upload: Upload,
  draft: FilePenLine,
} as const;

type ListActionProps = Omit<ComponentProps<typeof Button>, "children" | "size"> & {
  kind: keyof typeof icons;
  label: string;
  href?: string;
  /** Na janela de visualização: botão com ícone e texto, sem dica. */
  showText?: boolean;
};

/** Ação compacta de listagem, com nome acessível e explicação no mouse/teclado. */
export function ListAction({
  kind,
  label,
  href,
  showText = false,
  variant = "outline",
  className,
  ...props
}: ListActionProps) {
  const Icon = icons[kind];
  const content = <Icon size={18} aria-hidden />;
  if (showText) {
    const withText = (
      <>
        {content}
        {label}
      </>
    );
    return href ? (
      <Link href={href} className={cn(buttonVariants({ variant }), "gap-2", className)}>
        {withText}
      </Link>
    ) : (
      <Button {...props} type={props.type ?? "button"} variant={variant} className={cn("gap-2", className)}>
        {withText}
      </Button>
    );
  }
  return (
    <span className="group/action relative inline-flex" title={label}>
      {href ? (
        <Link
          href={href}
          aria-label={label}
          className={cn(buttonVariants({ variant, size: "icon" }), className)}
        >
          {content}
        </Link>
      ) : (
        <Button
          {...props}
          type={props.type ?? "button"}
          variant={variant}
          size="icon"
          className={className}
          aria-label={label}
        >
          {content}
        </Button>
      )}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full right-0 z-50 mb-2 hidden rounded bg-foreground px-2 py-1 text-xs font-normal whitespace-nowrap text-background shadow-md group-hover/action:block group-focus-within/action:block"
      >
        {label}
      </span>
    </span>
  );
}
