import { LoginForm } from '@/components/auth/login-form';

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div>
          <h1 className="text-2xl font-bold text-center">登录</h1>
        </div>
        <LoginForm />
        <div className="text-center">
          <a 
            href="/register" 
            className="text-blue-500 hover:text-blue-700"
          >
            没有账号？立即注册
          </a>
        </div>
      </div>
    </div>
  );
}
