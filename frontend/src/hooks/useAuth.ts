import { useQuery } from '@tanstack/react-query';
import { httpClient } from '~/libs/httpClient';
import type { User } from '~/types/user';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useAuth() {
    return useQuery<User>({
        queryKey: ['auth'],
        queryFn: async () => {
            const data = await httpClient<User>(`${API_URL}/account/@me`);
            return data;
        },
        retry: false,
    });
}
