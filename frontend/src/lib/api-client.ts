"use client";

import { useAuth } from "@clerk/nextjs";

type ApiErrorPayload = {
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
};

export class ApiClientError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: unknown = null,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

export type ApiClient = <T>(path: string, init?: RequestInit) => Promise<T>;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function buildApiUrl(path: string) {
  return new URL(path.replace(/^\/+/, ""), `${API_BASE_URL.replace(/\/+$/, "")}/`).toString();
}

async function parseJsonSafely(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type");

  if (!contentType?.includes("application/json")) {
    return null;
  }

  return response.json();
}

export function createApiClient(getToken: () => Promise<string | null>): ApiClient {
  return async function apiClient<T>(path: string, init: RequestInit = {}): Promise<T> {
    const token = await getToken();
    const headers = new Headers(init.headers);

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    if (!headers.has("Content-Type") && init.body && !(init.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(buildApiUrl(path), {
      ...init,
      headers,
      cache: init.cache ?? "no-store",
    });

    const payload = await parseJsonSafely(response);

    if (!response.ok) {
      const errorPayload = payload as ApiErrorPayload | null;

      if (errorPayload?.error) {
        throw new ApiClientError(
          response.status,
          errorPayload.error.code,
          errorPayload.error.message,
          errorPayload.error.details,
        );
      }

      throw new ApiClientError(
        response.status,
        "request_failed",
        `Request failed with status ${response.status}`,
      );
    }

    return payload as T;
  };
}

export function useApiClient(): ApiClient {
  const { getToken } = useAuth();

  return createApiClient(() => getToken());
}
