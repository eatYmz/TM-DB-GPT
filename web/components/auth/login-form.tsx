import { useState } from 'react';
import { useRouter } from 'next/router';
import { TokenManager } from '@/utils/token';
import { authLogin } from '@/client/api/auth/auth';
import { LoginCredentials, LoginResponse } from '@/types/auth';
import { 
  STORAGE_TOKEN_KET,
  STORAGE_USERINFO_KEY,
  STORAGE_USERINFO_VALID_TIME_KEY 
} from '@/utils/constants/storage';

export const LoginForm = () => {
  const router = useRouter();
  const [formData, setFormData] = useState<LoginCredentials>({
    username: '',
    password: '',
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await authLogin(formData);
      const loginData = response.data;
      
      if (loginData.access_token) {
        // 存储 token
        TokenManager.setToken(loginData.access_token);
        
        // 存储用户信息
        localStorage.setItem(STORAGE_USERINFO_KEY, JSON.stringify(loginData.user));
        
        // 存储过期时间
        localStorage.setItem(
          STORAGE_USERINFO_VALID_TIME_KEY, 
          (Date.now() + loginData.expires_in * 1000).toString()
        );
        
        router.push('/');
      } else {
        setError('登录失败，请检查用户名和密码');
      }
    } catch (error) {
      console.error('Login failed:', error);
      setError('登录失败，请稍后重试');
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
        />
      </div>
      <div>
        <input
          type="password"
          placeholder="Password"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          className="w-full p-2 border rounded"
        />
      </div>
      {error && <div className="text-red-500">{error}</div>}
      <button 
        type="submit"
        className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Login
      </button>
    </form>
  );
};
