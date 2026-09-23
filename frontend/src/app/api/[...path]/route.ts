import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const backend = process.env.BACKEND_URL || "http://127.0.0.1:8000";
const secure = process.env.COOKIE_SECURE !== "false";
const cookieOptions = {
  httpOnly: true,
  secure,
  sameSite: "lax" as const,
  path: "/jalapao-store",
};
type Tokens = { access: string; refresh: string };
const refreshing = new Map<string, Promise<Tokens | null>>();

async function refresh(token: string): Promise<Tokens | null> {
  let pending = refreshing.get(token);
  if (!pending) {
    pending = fetch(`${backend}/api/v1/auth/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: token }),
      cache: "no-store",
    })
      .then(async (r) => (r.ok ? ((await r.json()) as Tokens) : null))
      .catch(() => null);
    refreshing.set(token, pending);
    setTimeout(() => refreshing.delete(token), 5000).unref();
  }
  return pending;
}
async function handle(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const parts = (await params).path;
  if (parts.some((p) => !/^[-a-zA-Z0-9]+$/.test(p)))
    return NextResponse.json(
      { errors: { detail: "Rota inválida." } },
      { status: 400 },
    );
  const path = parts.join("/");
  const mutable = !["GET", "HEAD"].includes(request.method);
  if (mutable) {
    const origin = request.headers.get("origin");
    const expected = process.env.APP_ORIGIN || request.nextUrl.origin;
    if (origin !== expected)
      return NextResponse.json(
        { errors: { detail: "Origem da solicitação não permitida." } },
        { status: 403 },
      );
  }
  if (
    !/^(auth\/(login|logout|me)|dashboard|products(?:\/[a-f0-9-]+)?|movements|cash|receipts(?:\/[a-f0-9-]+(?:\/pay)?)?|sales(?:\/[a-f0-9-]+(?:\/(?:receive|cancel))?)?)$/.test(
      path,
    )
  )
    return NextResponse.json(
      { errors: { detail: "Rota não encontrada." } },
      { status: 404 },
    );
  const jar = await cookies();
  let access = jar.get("jalapao_access")?.value;
  const oldRefresh = jar.get("jalapao_refresh")?.value;
  let rotated: Tokens | null = null;
  try {
    if (path === "auth/logout") {
      if (request.method !== "POST")
        return new NextResponse(null, { status: 405 });
      if (oldRefresh)
        await fetch(`${backend}/api/v1/auth/logout/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh: oldRefresh }),
        });
      const out = NextResponse.json({ ok: true });
      out.cookies.set("jalapao_access", "", { ...cookieOptions, maxAge: 0 });
      out.cookies.set("jalapao_refresh", "", { ...cookieOptions, maxAge: 0 });
      return out;
    }
    if (path === "auth/login" && request.method !== "POST")
      return new NextResponse(null, { status: 405 });
    if (path !== "auth/login" && !access && oldRefresh) {
      rotated = await refresh(oldRefresh);
      access = rotated?.access;
    }
    const body = mutable ? await request.text() : undefined;
    if (body && body.length > 1000000)
      return NextResponse.json(
        { errors: { detail: "Solicitação muito grande." } },
        { status: 413 },
      );
    const target = path === "auth/login" ? "auth/token" : path;
    const send = () =>
      fetch(`${backend}/api/v1/${target}/${request.nextUrl.search}`, {
        method: request.method,
        headers: {
          "Content-Type": "application/json",
          ...(access ? { Authorization: `Bearer ${access}` } : {}),
        },
        body,
        cache: "no-store",
        signal: AbortSignal.timeout(20000),
      });
    let result = await send();
    if (
      result.status === 401 &&
      path !== "auth/login" &&
      oldRefresh &&
      !rotated
    ) {
      rotated = await refresh(oldRefresh);
      access = rotated?.access;
      if (access) result = await send();
    }
    const data = await result
      .json()
      .catch(() => ({ errors: { detail: "Falha na resposta da API." } }));
    if (path === "auth/login" && result.ok) rotated = data as Tokens;
    const out = NextResponse.json(
      path === "auth/login" && result.ok ? { ok: true } : data,
      { status: result.status },
    );
    out.headers.set("Cache-Control", "no-store");
    if (rotated) {
      out.cookies.set("jalapao_access", rotated.access, {
        ...cookieOptions,
        maxAge: 900,
      });
      out.cookies.set("jalapao_refresh", rotated.refresh, {
        ...cookieOptions,
        maxAge: 86400,
      });
    }
    if (result.status === 401) {
      out.cookies.set("jalapao_access", "", { ...cookieOptions, maxAge: 0 });
      out.cookies.set("jalapao_refresh", "", { ...cookieOptions, maxAge: 0 });
    }
    return out;
  } catch {
    return NextResponse.json(
      {
        errors: {
          detail: "Não foi possível falar com o servidor. Tente novamente.",
        },
      },
      { status: 502 },
    );
  }
}
export { handle as GET, handle as POST, handle as PATCH, handle as PUT };
