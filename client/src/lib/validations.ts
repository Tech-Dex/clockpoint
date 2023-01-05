import { z } from "zod";

export const registerSchema = z
	.object({
		email: z
			.string({
				required_error: "Email is required",
			})
			.email({
				message: "Email is invalid",
			}),
		firstName: z
			.string({
				required_error: "First name is required",
			})
			.min(2, {
				message: "First name must be at least 2 characters long",
			})
			.max(50, {
				message: "First name must be at most 50 characters long",
			}),
		secondName: z
			.string()
			.min(2, {
				message: "Second name must be at least 2 characters long",
			})
			.max(50, {
				message: "Second name must be at most 50 characters long",
			})
			.optional(),
		lastName: z
			.string({
				required_error: "Last name is required",
			})
			.min(2, {
				message: "Last name must be at least 2 characters long",
			})
			.max(50, {
				message: "Last name must be at most 50 characters long",
			}),
		username: z
			.string({
				required_error: "Username is required",
			})
			.min(2, {
				message: "Username must be at least 2 characters long",
			})
			.max(50, {
				message: "Username must be at most 50 characters long",
			}),
		password: z
			.string({
				required_error: "Password is required",
			})
			.min(8, {
				message: "Password must be at least 8 characters long",
			})
			.max(50, {
				message: "Password must be at most 50 characters long",
			}),
		confirmPassword: z
			.string({
				required_error: "Confirm password is required",
			})
			.min(8, {
				message: "Confirm password must be at least 8 characters long",
			})
			.max(50, {
				message: "Confirm password must be at most 50 characters long",
			}),
	})
	.superRefine(({ password, confirmPassword }, ctx) => {
		if (password !== confirmPassword) {
			ctx.addIssue({
				code: z.ZodIssueCode.custom,
				message: "Password and confirm password must match",
				path: ["confirmPassword"],
			});
			ctx.addIssue({
				code: z.ZodIssueCode.custom,
				message: "Password and confirm password must match",
				path: ["password"],
			});
		}
		return true;
	});
