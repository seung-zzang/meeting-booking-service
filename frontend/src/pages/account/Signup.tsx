import React, { useState } from 'react';
import { Link } from '@tanstack/react-router';
import { Button } from '~/components/button';
import { useSignup } from '~/hooks/useSignup';

export default function Signup() {
    const signup = useSignup();

    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [password, setPassword] = useState('');
    const [passwordAgain, setPasswordAgain] = useState('');

    const handleSubmit = (event: React.FormEvent) => {
        event.preventDefault();
        signup.mutate({ username, email, displayName, password, passwordAgain });
    };

    return (
        <div className="space-y-4 px-8">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">회원가입</h2>
                <Link to="/app/login" className="text-sm text-gray-600 hover:text-primary">
                    로그인으로
                </Link>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                    <label htmlFor="username">아이디:</label>
                    <input
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                        minLength={4}
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label htmlFor="email">이메일:</label>
                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label htmlFor="displayName">표시 이름:</label>
                    <input
                        id="displayName"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        required
                        minLength={2}
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label htmlFor="password">비밀번호:</label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        minLength={8}
                    />
                </div>

                <div className="flex flex-col gap-2">
                    <label htmlFor="passwordAgain">비밀번호 확인:</label>
                    <input
                        id="passwordAgain"
                        type="password"
                        value={passwordAgain}
                        onChange={(e) => setPasswordAgain(e.target.value)}
                        required
                        minLength={8}
                    />
                </div>

                <Button variant="primary" type="submit" disabled={signup.isPending} className="w-full py-3 px-5">
                    {signup.isPending ? '가입 중...' : '회원가입'}
                </Button>
            </form>

            {signup.isError && <div className="text-sm text-red-600">{signup.error.message}</div>}
            {signup.isSuccess && <div className="text-sm text-green-700">가입 완료! 로그인 화면으로 이동합니다.</div>}
        </div>
    );
}

