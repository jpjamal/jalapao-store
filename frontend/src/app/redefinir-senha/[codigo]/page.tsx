import ResetPassword from "@/features/auth/reset-password-page";

export default async function Page({ params }: { params: Promise<{ codigo: string }> }) {
  const { codigo } = await params;
  return <ResetPassword code={codigo} />;
}
