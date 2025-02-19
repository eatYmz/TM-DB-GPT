import { useState } from 'react';
import { useRouter } from 'next/router';
import { message } from 'antd';
import { TokenManager } from '@/utils/token';
import { authLogin } from '@/client/api/auth/auth';
import { LoginCredentials } from '@/types/auth';
import { 
  STORAGE_USERINFO_KEY,
  STORAGE_USERINFO_VALID_TIME_KEY 
} from '@/utils/constants/storage';

export const LoginForm = () => {
  const router = useRouter();
  const [formData, setFormData] = useState<LoginCredentials>({
    username: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authLogin(formData);
      const loginData = response.data;
      
      if (loginData.access_token) {
        // 1. 先存储用户信息
        localStorage.setItem(STORAGE_USERINFO_KEY, JSON.stringify(loginData.user));
        // 2. 再设置 token
        TokenManager.setToken(loginData.access_token, loginData.expires_in);
        
        message.success('登录成功');
        
        // 3. 直接跳转到目标页面
        const redirectPath = router.query.from as string || '/';
        router.push(redirectPath);
      } else {
        setError('登录失败，请检查用户名和密码');
        message.error('登录失败，请检查用户名和密码');
      }
    } catch (error: any) {
      console.error('Login failed:', error);
      const errorMessage = error.response?.data?.detail || '登录失败，请稍后重试';
      setError(errorMessage);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <input
          type="text"
          placeholder="Username"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          className="w-full p-2 border rounded"
          disabled={loading}
        />
      </div>
      <div>
        <input
          type="password"
          placeholder="Password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          className="w-full p-2 border rounded"
          disabled={loading}
        />
      </div>
      {error && <div className="text-red-500">{error}</div>}
      <button 
        type="submit"
        className={`w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600 
          ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        disabled={loading}
      >
        {loading ? '登录中...' : '登录'}
      </button>
    </form>
  );
};
