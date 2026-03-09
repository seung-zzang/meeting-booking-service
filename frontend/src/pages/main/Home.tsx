import { Link } from '@tanstack/react-router';
import { useAuth } from '~/hooks/useAuth';
import { useHosts } from '~/hooks/useHost';

export default function Home() {
    const hosts = useHosts();
    const auth = useAuth();
    const now = new Date();

    return (
        <div className='w-6/12 mx-auto flex flex-col justify-center min-h-[200px] px-8 space-y-4'>
            <h1 className='text-2xl font-bold'>약속 잡기 서비스</h1>

            <div className="flex flex-wrap gap-2">
                {!auth.isError && auth.data?.isHost && (
                    <Link
                        to="/app/host-bookings"
                        search={{ page: 1, pageSize: 10 }}
                        className="inline-block bg-gray-800 text-white px-4 py-2 rounded-md hover:bg-gray-700"
                    >
                        호스트 예약 내역
                    </Link>
                )}
                {auth.isError && (
                    <>
                        <Link
                            to="/app/login"
                            className="inline-block bg-primary text-white px-4 py-2 rounded-md hover:bg-secondary"
                        >
                            로그인
                        </Link>
                        <Link
                            to="/app/signup"
                            className="inline-block border border-gray-300 px-4 py-2 rounded-md hover:border-gray-400"
                        >
                            회원가입
                        </Link>
                    </>
                )}
            </div>

            {hosts.isLoading && <div>읽어오는 중...</div>}
            {hosts.error && <div className='space-y-2'>
                <p className='text-red-500'>{hosts.error.message}</p>
                {hosts.error.cause === 401 && <p className=''>
                    <Link to='/app/login' className='block text-center bg-primary text-white px-4 py-2 rounded-md hover:bg-secondary hover:text-white'>로그인</Link>
                </p>}
            </div>}

            <ul>
                {hosts.data?.map((host) => (
                    <li key={host.username}>
                        <Link
                            to='/app/calendar/$slug'
                            params={{ slug: host.username }}
                            search={{ year: now.getFullYear(), month: now.getMonth() + 1 }}
                            className='block text-center bg-primary text-white px-4 py-2 rounded-md hover:bg-secondary hover:text-white'
                        >
                            {host.displayName} ({host.username})
                        </Link>
                    </li>
                ))}
            </ul>
        </div>
    );
};

