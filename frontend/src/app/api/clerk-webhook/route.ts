const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const REQUIRED_SVIX_HEADERS = [
  "svix-id",
  "svix-timestamp",
  "svix-signature",
] as const;

function buildWebhookUrl() {
  return new URL("auth/webhook", `${API_BASE_URL.replace(/\/+$/, "")}/`).toString();
}

function buildErrorResponse(
  status: number,
  code: string,
  message: string,
  details: unknown = null,
) {
  return Response.json(
    {
      error: {
        code,
        message,
        details,
      },
    },
    { status },
  );
}

export async function POST(request: Request) {
  const body = await request.text();
  const headers = new Headers({
    "content-type": "application/json",
  });

  for (const headerName of REQUIRED_SVIX_HEADERS) {
    const headerValue = request.headers.get(headerName);

    if (!headerValue) {
      return buildErrorResponse(
        400,
        "missing_webhook_header",
        `Missing required webhook header: ${headerName}`,
      );
    }

    headers.set(headerName, headerValue);
  }

  const response = await fetch(buildWebhookUrl(), {
    method: "POST",
    headers,
    body,
    cache: "no-store",
  });

  return new Response(await response.text(), {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
  });
}
