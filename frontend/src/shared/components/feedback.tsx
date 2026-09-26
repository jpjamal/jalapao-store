export function ErrorMessage({ message }: { message: string }) {
  return message ? (
    <div
      role="alert"
      className="border border-destructive text-destructive rounded-md p-3 mb-4 whitespace-pre-wrap"
    >
      {message}
    </div>
  ) : null;
}
export function Empty({ children }: { children: React.ReactNode }) {
  return <p className="py-10 text-center text-muted-foreground">{children}</p>;
}
