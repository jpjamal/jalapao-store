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
};

/** Ação compacta de listagem, com nome acessível e explicação no mouse/teclado. */
export function ListAction({
  kind,
  label,
  href,
  variant = "outline",
  className,
  ...props
}: ListActionProps) {
  const Icon = icons[kind];
  const content = <Icon size={18} aria-hidden />;
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
