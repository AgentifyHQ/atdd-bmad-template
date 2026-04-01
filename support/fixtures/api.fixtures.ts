import { test as base } from '@playwright/test';
import { z, ZodSchema } from 'zod';

type ApiResponse<T = unknown> = {
  status: number;
  body: T;
  headers: Record<string, string>;
};

type ApiRequestOptions = {
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  path: string;
  baseUrl?: string;
  body?: unknown;
  params?: Record<string, string | number>;
  headers?: Record<string, string>;
  validateSchema?: ZodSchema;
};

/**
 * API testing fixtures — no browser required.
 * Provides typed HTTP client with schema validation.
 */
export const test = base.extend<{
  apiRequest: <T = unknown>(options: ApiRequestOptions) => Promise<ApiResponse<T>>;
}>({
  apiRequest: async ({ request }, use) => {
    const apiRequest = async <T = unknown>(options: ApiRequestOptions): Promise<ApiResponse<T>> => {
      const { method, path, baseUrl, body, params, headers, validateSchema } = options;

      // Build URL with query params
      let url = baseUrl ? `${baseUrl}${path}` : path;
      if (params) {
        const searchParams = new URLSearchParams();
        for (const [key, value] of Object.entries(params)) {
          searchParams.append(key, String(value));
        }
        url += `?${searchParams.toString()}`;
      }

      const response = await request.fetch(url, {
        method,
        data: body,
        headers,
      });

      const responseBody = response.headers()['content-type']?.includes('application/json')
        ? await response.json()
        : await response.text();

      // Schema validation
      if (validateSchema) {
        validateSchema.parse(responseBody);
      }

      return {
        status: response.status(),
        body: responseBody as T,
        headers: response.headers(),
      };
    };

    await use(apiRequest);
  },
});

export { expect } from '@playwright/test';
