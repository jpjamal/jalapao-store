import { cn } from "@/lib/utils";

/* Botões de um formulário: empilhados e com largura total no celular (fáceis de tocar),
   lado a lado no computador. O primeiro filho é a ação principal. */
export function FormActions({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3 [&>button]:w-full sm:[&>button]:w-auto",
        className,
      )}
      {...props}
    />
  );
}
