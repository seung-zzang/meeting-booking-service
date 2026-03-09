import { useMutation, UseMutationResult } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { httpClient } from '~/libs/httpClient';

interface SignupPayload {
    username: string;
    email: string;
    displayName: string;
    password: string;
    passwordAgain: string;
}

interface SignupResponse {
    username: string;
    displayName: string;
    isHost: boolean;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useSignup(): UseMutationResult<SignupResponse, Error, SignupPayload> {
    const navigate = useNavigate();

    return useMutation<SignupResponse, Error, SignupPayload>({
        mutationFn: async (payload: SignupPayload) => {
            return await httpClient<SignupResponse>(`${API_URL}/account/signup`, {
                method: 'POST',
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                body: payload as any,
            });
        },
        onSuccess: () => {
            navigate({ to: '/app/login' });
        },
    });
}

