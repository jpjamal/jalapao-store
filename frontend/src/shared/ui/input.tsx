import * as React from "react";
import { cn } from "@/shared/lib/utils";
import { NumberInput, type NumberMask } from "@/shared/ui/number-input";
export function Input({
  className,
  type,
  mask,
  ...props
}: React.ComponentProps<"input"> & { mask?: NumberMask }) {
  // campos numéricos têm máscara brasileira (spec 036); o valor entregue segue sendo o número puro
  if (type === "number") return <NumberInput className={className} mask={mask} {...(props as React.ComponentProps<typeof NumberInput>)} />;
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "flex h-11 sm:h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base shadow-xs focus-visible:outline-2 focus-visible:outline-ring disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
