import { Link, useSearch } from '@tanstack/react-router';
import { useMemo, useState } from 'react';
import Pagination from '~/components/Pagination';
import { useAuth } from '~/hooks/useAuth';
import { useHostBookings } from '~/hooks/useBookings';

export default function HostBookings() {
    const auth = useAuth();
    const { page, pageSize } = useSearch({ from: '/app/host-bookings' });
    const [currentPage, setCurrentPage] = useState<number>(page);

    const { data: bookings, isLoading, error } = useHostBookings({ page: currentPage, pageSize });

    const totalCount = useMemo(() => {
        // 백엔드가 total_count를 주지 않아서, "다음" 버튼 활성화를 위해 느슨하게 계산
        if (!bookings) return 0;
        if (bookings.length < pageSize) return (currentPage - 1) * pageSize + bookings.length;
        return (currentPage + 1) * pageSize;
    }, [bookings, currentPage, pageSize]);

    if (auth.isLoading) return <div>사용자 정보를 확인 중...</div>;

    if (auth.isError) {
        return (
            <div className="space-y-3">
                <div className="text-red-600">로그인이 필요합니다.</div>
                <Link to="/app/login" className="inline-block bg-primary text-white px-4 py-2 rounded-md">
                    로그인
                </Link>
            </div>
        );
    }

    if (!auth.data?.isHost) {
        return (
            <div className="space-y-3">
                <div className="text-red-600">호스트 계정만 볼 수 있습니다.</div>
                <Link to="/app" className="inline-block bg-gray-500 text-white px-4 py-2 rounded-md">
                    홈으로
                </Link>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <Link to="/app" className="bg-gray-500 hover:bg-gray-700 text-white px-4 py-2 rounded-md">
                    첫 화면으로
                </Link>
                <h2 className="text-2xl font-bold">신청된 예약(호스트)</h2>
            </div>

            {isLoading && <div>예약 목록을 불러오고 있습니다...</div>}

            {!!error && (
                <div className="text-red-500 space-y-2">
                    <div className="text-lg font-bold">오류 발생</div>
                    <div className="text-sm">{error.message}</div>
                </div>
            )}

            <ul className="divide-y">
                {bookings?.map((booking) => {
                    const when = new Date(booking.when);
                    return (
                        <li key={booking.id} className="py-3">
                            <Link to="/app/booking/$id" params={{ id: booking.id }} className="hover:text-primary">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-gray-500">
                                        {when.getFullYear()}.{when.getMonth() + 1}.{when.getDate()}
                                    </span>
                                    <span className="text-sm text-gray-500">
                                        {booking.timeSlot.startTime} - {booking.timeSlot.endTime}
                                    </span>
                                </div>
                                <div className="flex flex-wrap items-center gap-x-2">
                                    <span className="font-semibold">{booking.topic}</span>
                                    <span className="text-sm text-gray-600">({booking.host.displayName})</span>
                                    {booking.attendanceStatus && (
                                        <span className="text-xs text-gray-500">상태: {booking.attendanceStatus}</span>
                                    )}
                                </div>
                            </Link>
                        </li>
                    );
                })}
            </ul>

            <Pagination
                page={currentPage}
                pageSize={pageSize}
                totalCount={totalCount}
                onPageChange={setCurrentPage}
            />
        </div>
    );
}

