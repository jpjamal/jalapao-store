import * as React from "react";
import { cn } from "@/lib/utils";
export function Card({ className, ...props }: React.ComponentProps<"section">) {
  return (
    <section
      className={cn(
        "rounded-xl border bg-card text-card-foreground p-6 shadow-xs",
        className,
      )}
      {...props}
    />
  );
}
