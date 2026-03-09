import { useQuery } from '@tanstack/react-query';
import { httpClient } from '~/libs/httpClient';
import { ITimeSlot } from '~/types/timeslot';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useTimeslots(hostname: string, date: Date | null) {
    return useQuery<ITimeSlot[]>({
        queryKey: ['timeslots', hostname, date?.toISOString()],
        queryFn: async () => {
            if (!date) throw new Error("Date is required");
            const url = `${API_URL}/time-slots/${hostname}`;
            const data: ITimeSlot[] = await httpClient<ITimeSlot[]>(url);
            return data;
           
        },
        enabled: !!date,
    });
} 
