// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
// and what to do when importing types
declare namespace App {
	// interface Error {}
	interface Locals {
		user: {
			email: string;
			firstName: string;
			secondName: string;
			lastName: string;
			username: string;
			isActive: boolean;
			phoneNumber: string;
		};
	}
	// interface PageData {}
	// interface Platform {}
}
