import { axios } from "@api/axios";

const ENDPOINT = "/auth";

export const login = async ({ email, password, options }) => {
	const { data } = await axios.post(
		`${ENDPOINT}/login`,
		{ email, password },
		{
			signal: options?.signal,
			headers: {
				"Content-Type": "application/json",
			},
		},
	);
	return data;
};

export const register = async ({
	email,
	password,
	firstName,
	secondName,
	lastName,
	username,
	options,
}) => {
	const { data } = await axios.post(
		`${ENDPOINT}/register`,
		{ email, password, firstName, secondName, lastName, username },
		{
			signal: options?.signal,
			headers: {
				"Content-Type": "application/json",
			},
		},
	);

	return data;
};

export const refresh = async ({ options }) => {
	const { data } = await axios.get(`${ENDPOINT}/refresh`, {
		signal: options?.signal,
		headers: {
			"Content-Type": "application/json",
		},
	});

	return data;
};
