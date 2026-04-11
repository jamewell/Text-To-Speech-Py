import z from 'zod';

export const UserSchema = z.object({
	id: z.number(),
	email: z.email(),
	created_at: z.iso.datetime(),
	is_active: z.boolean()
});

export type User = z.infer<typeof UserSchema>;

export const AuthResponseSchema = z.object({
	message: z.string(),
	user: UserSchema,
	token: z.string().optional()
});

export type AuthResponse = z.infer<typeof AuthResponseSchema>;

export const CurrentUserResponseSchema = UserSchema;

export const LogoutResponseSchema = z.object({
	message: z.string()
});

export const RefreshTokenResponseSchema = z.object({
	access_token: z.string(),
	refresh_token: z.string().optional(),
	expires_in: z.number().optional()
});

export const ErrorResponseSchema = z.object({
	detail: z.string(),
	status_code: z.number().optional()
});

export const FileUploadResponseSchema = z.object({
	id: z.number(),
	original_filename: z.string(),
	stored_filename: z.string(),
	file_size: z.number(),
	mime_type: z.string(),
	status: z.string(),
	upload_date: z.iso.datetime()
});

export type FileUploadResponse = z.infer<typeof FileUploadResponseSchema>;

export const ChapterSchema = z.object({
	id: z.number(),
	file_id: z.number(),
	chapter_index: z.number(),
	title: z.string(),
	start_page: z.number(),
	end_page: z.number(),
	audio_bucket_name: z.string().nullable().optional(),
	audio_object_name: z.string().nullable().optional(),
	created_at: z.iso.datetime()
});

export type Chapter = z.infer<typeof ChapterSchema>;

export const FileSchema = z.object({
	id: z.number(),
	user_id: z.number(),
	original_filename: z.string(),
	stored_filename: z.string(),
	file_size: z.number(),
	mime_type: z.string(),
	bucket_name: z.string(),
	status: z.string(),
	visibility: z.string(),
	error_message: z.string().nullable().optional(),
	upload_date: z.iso.datetime(),
	processed_date: z.iso.datetime().nullable().optional(),
	chapters: z.array(ChapterSchema).default([])
});

export type FileDetail = z.infer<typeof FileSchema>;

export const FileListResponseSchema = z.object({
	files: z.array(FileSchema),
	total: z.number(),
	page: z.number(),
	page_size: z.number()
});

export type FileListResponse = z.infer<typeof FileListResponseSchema>;

export const ChapterAudioResponseSchema = z.object({
	chapter_id: z.number(),
	url: z.url(),
	expires_in_seconds: z.number()
});

export type ChapterAudioResponse = z.infer<typeof ChapterAudioResponseSchema>;

export const ReadingHistorySchema = z.object({
	id: z.number(),
	user_id: z.number(),
	file_id: z.number(),
	chapter_id: z.number().nullable().optional(),
	position_seconds: z.number(),
	updated_at: z.iso.datetime()
});

export type ReadingHistory = z.infer<typeof ReadingHistorySchema>;

export const HistoryListResponseSchema = z.object({
	history: z.array(ReadingHistorySchema),
	total: z.number(),
	page: z.number(),
	page_size: z.number()
});

export type HistoryListResponse = z.infer<typeof HistoryListResponseSchema>;
