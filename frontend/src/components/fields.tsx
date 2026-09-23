import { Input } from "./ui/input";
export function Field({
  name,
  label,
  type = "text",
  value,
  ...props
}: {
  name: string;
  label: string;
  type?: string;
  value?: string | number;
} & Omit<React.ComponentProps<"input">, "value">) {
  return (
    <div>
      <label htmlFor={name}>{label}</label>
      <Input
        id={name}
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
}: {
  name: string;
  label: string;
  value?: string | number;
}) {
  return (
    <Field
      name={name}
      label={label}
      type="number"
      min="0"
      step="0.01"
      value={value}
      required
    />
  );
}
