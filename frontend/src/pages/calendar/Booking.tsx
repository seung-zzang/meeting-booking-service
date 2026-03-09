import { Link, useParams } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Button } from "~/components/button";
import { useAuth } from "~/hooks/useAuth";
import { useCancelGuestBooking, useBooking, useUpdateGuestBooking, useUpdateHostBooking, useUploadBookingFile } from "~/hooks/useBookings";
import { useTimeslots } from "~/hooks/useTimeslots";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Booking() {
    const { id } = useParams({ from: '/app/booking/$id' });
    const { data: booking, isLoading, error, refetch } = useBooking(id);
    const { mutate: uploadFile, isSuccess: isUploadSuccess } = useUploadBookingFile(id);
    const auth = useAuth();

    const updateGuest = useUpdateGuestBooking(id);
    const cancelGuest = useCancelGuestBooking(id);
    const updateHost = useUpdateHostBooking(id);

    const [topic, setTopic] = useState('');
    const [description, setDescription] = useState('');
    const [when, setWhen] = useState('');
    const [timeSlotId, setTimeSlotId] = useState<number | ''>('');

    useEffect(() => {
        if (isUploadSuccess) {
            refetch();
        }
    }, [isUploadSuccess, refetch]);

    useEffect(() => {
        if (!booking) return;
        setTopic(booking.topic ?? '');
        setDescription(booking.description ?? '');
        const d = new Date(booking.when);
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        setWhen(`${yyyy}-${mm}-${dd}`);
        setTimeSlotId(booking.timeSlot?.id ?? '');
    }, [booking]);


    if (!booking || isLoading) return <div>예약 정보를 불러오고 있습니다...</div>;
    if (error) return <div>예약 정보를 불러오는 중 오류가 발생했습니다.</div>;

    const whenDate = new Date(booking.when);

    const selectedWhenDate = useMemo(() => {
        if (!when) return null;
        const [y, m, d] = when.split('-').map(Number);
        if (!y || !m || !d) return null;
        return new Date(y, m - 1, d);
    }, [when]);

    const { data: timeslots = [] } = useTimeslots(booking.host.username, selectedWhenDate);
    const weekday = selectedWhenDate?.getDay();
    const availableTimeslots = useMemo(() => {
        if (weekday === undefined || weekday === null) return timeslots;
        // backend weekday: 0=Mon..6=Sun, JS: 0=Sun..6=Sat
        const backendWeekday = (weekday + 6) % 7;
        return timeslots.filter((t) => t.weekdays.includes(backendWeekday));
    }, [timeslots, weekday]);

    const handleSaveGuest = () => {
        updateGuest.mutate(
            {
                topic,
                description,
                when: when || undefined,
                timeSlotId: timeSlotId === '' ? undefined : timeSlotId,
            },
            { onSuccess: () => refetch() }
        );
    };

    const handleSaveHost = () => {
        updateHost.mutate(
            {
                when: when || undefined,
                timeSlotId: timeSlotId === '' ? undefined : timeSlotId,
            },
            { onSuccess: () => refetch() }
        );
    };

    const handleCancel = () => {
        const ok = window.confirm('예약을 취소할까요?');
        if (!ok) return;
        cancelGuest.mutate(undefined, { onSuccess: () => refetch() });
    };

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.target as HTMLFormElement);
        uploadFile(formData);
    }

    return <div className="flex flex-col space-y-4">
        <Link to='/app/my-bookings' className='inline-block w-fit bg-gray-500 hover:bg-gray-700 hover:text-white text-white px-4 py-2 rounded-md'>내 예약 목록으로</Link>

        <h1 className="text-2xl font-bold">{booking.host.displayName}님과 약속잡기</h1>

        <div className="flex flex-row space-x-2 items-center">
            <div>{booking.topic}</div>
            <div className="text-sm text-gray-500 flex flex-row items-center space-x-2">
                <div>{whenDate.getFullYear()}년 {whenDate.getMonth() + 1}월 {whenDate.getDate()}일</div>
                <div>{booking.timeSlot.startTime} - {booking.timeSlot.endTime}</div>
            </div>
        </div>

        <div className="flex flex-row space-x-2 items-center">
            {booking.description}
        </div>

        <hr className="w-full" />

        <div className="space-y-3">
            <h2 className="text-lg font-bold">예약 변경 / 취소</h2>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="flex flex-col gap-2">
                    <label className="text-sm text-gray-700" htmlFor="when">날짜</label>
                    <input
                        id="when"
                        type="date"
                        value={when}
                        onChange={(e) => setWhen(e.target.value)}
                        className="border border-gray-300 rounded-md p-2"
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label className="text-sm text-gray-700" htmlFor="timeSlotId">시간</label>
                    <select
                        id="timeSlotId"
                        value={timeSlotId}
                        onChange={(e) => setTimeSlotId(e.target.value ? Number(e.target.value) : '')}
                        className="border border-gray-300 rounded-md p-2"
                    >
                        <option value="">선택</option>
                        {availableTimeslots.map((t) => (
                            <option key={t.id} value={t.id}>
                                {t.startTime} - {t.endTime}
                            </option>
                        ))}
                    </select>
                    <div className="text-xs text-gray-500">선택한 날짜의 요일에 맞는 시간만 표시됩니다.</div>
                </div>

                <div className="flex flex-col gap-2">
                    <label className="text-sm text-gray-700" htmlFor="topic">주제</label>
                    <input
                        id="topic"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        className="border border-gray-300 rounded-md p-2"
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label className="text-sm text-gray-700" htmlFor="description">설명</label>
                    <textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="border border-gray-300 rounded-md p-2"
                    />
                </div>
            </div>

            <div className="flex flex-wrap gap-2">
                <Button
                    variant="primary"
                    className="px-4 py-2"
                    onClick={handleSaveGuest}
                    disabled={updateGuest.isPending}
                >
                    {updateGuest.isPending ? '저장 중...' : '수정 저장(게스트)'}
                </Button>

                {!!auth.data?.isHost && (
                    <Button
                        variant="secondary"
                        className="px-4 py-2"
                        onClick={handleSaveHost}
                        disabled={updateHost.isPending}
                    >
                        {updateHost.isPending ? '변경 중...' : '시간/날짜 변경(호스트)'}
                    </Button>
                )}

                <Button
                    variant="secondary"
                    className="px-4 py-2 border border-red-300 text-red-700"
                    onClick={handleCancel}
                    disabled={cancelGuest.isPending}
                >
                    {cancelGuest.isPending ? '취소 중...' : '예약 취소'}
                </Button>
            </div>

            {(updateGuest.isError || updateHost.isError || cancelGuest.isError) && (
                <div className="text-sm text-red-600">
                    {(updateGuest.error || updateHost.error || cancelGuest.error)?.message}
                </div>
            )}
        </div>

        <hr className="w-full" />

        <form className="flex flex-col space-y-2 items-start" onSubmit={handleSubmit}>
            <input type="file" name="files" multiple />
            <Button type="submit" variant="primary" className="w-full py-2">첨부</Button>
        </form>

        {booking.files.length > 0 && (
            <ul className="list-disc pl-4 space-y-2">
                {booking.files.map((file) => {
                    const filename = file.file.split('/').pop();
                    return <li key={file.id} className="">
                        <a href={`${API_URL}/${file.file}`} target="_blank" rel="noopener noreferrer">{filename}</a>
                    </li>
                })}
            </ul>
        )}
        {booking.files.length === 0 && (
            <div>첨부 파일이 없습니다.</div>
        )}
    </div>;
}
