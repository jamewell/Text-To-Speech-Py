import z from "zod";

export const UserSchema = z.object({
    id: z.number(),
    email: z.email(),
    created_at: z.iso.datetime(),
    is_active: z.boolean(),
});

export type User = z.infer<typeof UserSchema>;

export const AuthResponseSchema = z.object({
    message: z.string(),
    user: UserSchema,
    token: z.string().optional(),
});

export type AuthResponse = z.infer<typeof AuthResponseSchema>;

export const CurrentUserResponseSchema = UserSchema;

export const LogoutResponseSchema = z.object({
    message: z.string(),
});

export const RefreshTokenResponseSchema = z.object({
    access_token: z.string(),
    refresh_token: z.string().optional(),
    expires_in: z.number().optional(),
});

export const ErrorResponseSchema = z.object({
    detail: z.string(),
    status_code: z.number().optional(),
});