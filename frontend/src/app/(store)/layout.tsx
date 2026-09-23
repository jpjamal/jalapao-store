import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Shell } from "@/components/shell";
export default async function StoreLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const jar = await cookies();
  if (!jar.has("jalapao_access") && !jar.has("jalapao_refresh"))
    redirect("/login");
  return <Shell username="Jalapão Store">{children}</Shell>;
}
