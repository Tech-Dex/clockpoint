import type { Actions } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";
import { registerSchema } from "$lib/validations";
import { redirect } from "@sveltejs/kit";

export const load: PageServerLoad = async ({ locals }) => {
	if (locals.user) {
		throw redirect(307, "/");
	}
};

export const actions: Actions = {
	async default({ cookies, request }) {
		const formData = Object.fromEntries(await request.formData());

		const zodParse = await registerSchema.safeParseAsync(formData);
		if (!zodParse.success) {
			const { fieldErrors: errors } = zodParse.error.flatten();
			const validFields = Object.keys(formData).filter(
				(field) => !Object.keys(errors).includes(field),
			);
			const validFormData = validFields.reduce(
				(acc, field) => ({ ...acc, [field]: formData[field] }),
				{},
			);
			return {
				data: validFormData,
				errors,
			};
		}

		throw redirect(307, "/");
	},
};
