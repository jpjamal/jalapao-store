import { Input } from "@/shared/ui/input";
export function Field({
  name,
  id = name,
  label,
  type = "text",
  value,
  ...props
}: {
  name: string;
  label: string;
  type?: string;
  value?: string | number;
  /** Só para type="number": ver shared/ui/number-input. */
  mask?: "money" | "decimal";
} & Omit<React.ComponentProps<"input">, "value">) {
  return (
    <div>
      <label htmlFor={id}>{label}</label>
      <Input
        id={id}
        name={name}
        type={type}
        defaultValue={value}
        {...props}
      />
    </div>
  );
}
export function MoneyField({
  name,
  label,
  value = "0",
  mask = "money",
}: {
  name: string;
  label: string;
  value?: string | number;
  /** "decimal" para campos sem centavos (potência, percentual). */
  mask?: "money" | "decimal";
}) {
  return (
    <Field
      name={name}
      label={label}
      type="number"
      min="0"
      step="0.01"
      mask={mask}
      value={value}
      required
    />
  );
}
