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
			})
			.refine(
				(value) => {
					const hasLowercase = /[a-z]/.test(value);
					const hasUppercase = /[A-Z]/.test(value);
					const hasNumber = /\d/.test(value);
					const hasSpecial = /[^a-zA-Z\d]/.test(value);
					return hasLowercase && hasUppercase && hasNumber && hasSpecial;
				},
				{
					message:
						"Password must contain at least one lowercase letter, one uppercase letter, one number and one special character",
				},
			),
		confirmPassword: z.string({
			required_error: "Confirm password is required",
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

export const loginSchema = z.object({
	email: z
		.string({
			required_error: "Email is required",
		})
		.email({
			message: "Email is invalid",
		}),
	password: z.string({
		required_error: "Password is required",
	}),
});
