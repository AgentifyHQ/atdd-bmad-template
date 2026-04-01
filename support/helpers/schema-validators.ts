import { z } from 'zod';

/**
 * Common reusable schemas for API response validation.
 * Add project-specific schemas here as the test suite grows.
 */

export const IdSchema = z.object({
  id: z.string().or(z.number()),
});

export const TimestampsSchema = z.object({
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    total: z.number(),
    page: z.number(),
    pageSize: z.number(),
  });

export const ErrorResponseSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.array(z.object({
    field: z.string().optional(),
    message: z.string(),
  })).optional(),
});

// ── Example: User schema (replace with your domain) ──
export const UserSchema = z.object({
  id: z.string(),
  name: z.string(),
  email: z.string().email(),
  role: z.enum(['user', 'admin', 'viewer']),
}).merge(TimestampsSchema);

export type User = z.infer<typeof UserSchema>;
