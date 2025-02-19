import { useState } from 'react';
import { useRouter } from 'next/router';
import { TokenManager } from '@/utils/token';
import { authRegister } from '@/client/api/auth/auth';
import { RegisterParams } from '@/types/auth';
import { 
  STORAGE_USERINFO_KEY,
  STORAGE_USERINFO_VALID_TIME_KEY 
} from '@/utils/constants/storage';

export const RegisterForm = () => {
  const router = useRouter();
  const [formData, setFormData] = useState<RegisterParams>({
    username: '',
    password: '',
    email: '',
    nickname: ''
  });
  const [error, setError] = useState('');
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSuccess(false);
    
    try {
      const response = await authRegister(formData);
      const registerData = response.data;
      
      if (registerData.access_token) {
        // 存储 token
        TokenManager.setToken(registerData.access_token);
        
        // 存储用户信息
        localStorage.setItem(STORAGE_USERINFO_KEY, JSON.stringify(registerData.user));
        
        // 存储过期时间
        localStorage.setItem(
          STORAGE_USERINFO_VALID_TIME_KEY, 
          (Date.now() + registerData.expires_in * 1000).toString()
        );
        
        // 设置成功状态
        setIsSuccess(true);
        
        // 延迟跳转，让用户看到成功提示
        setTimeout(() => {
          router.push('/');
        }, 1000);
      } else {
        setError('注册失败，请重试');
      }
    } catch (error: any) {
      console.error('Register failed:', error);
      setError(error.response?.data?.detail || '注册失败，请稍后重试');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {isSuccess && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative">
          注册成功！正在跳转到首页...
        </div>
      )}
      <div>
        <input
          type="text"
          placeholder="用户名"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          className="w-full p-2 border rounded"
          required
        />
      </div>
      <div>
        <input
          type="password"
          placeholder="密码"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          className="w-full p-2 border rounded"
          required
        />
      </div>
      <div>
        <input
          type="email"
          placeholder="邮箱"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="w-full p-2 border rounded"
          required
        />
      </div>
      <div>
        <input
          type="text"
          placeholder="昵称"
          value={formData.nickname}
          onChange={(e) => setFormData({ ...formData, nickname: e.target.value })}
          className="w-full p-2 border rounded"
          required
        />
      </div>
      {error && <div className="text-red-500">{error}</div>}
      <button 
        type="submit"
        className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        注册
      </button>
      <div className="text-center">
        <a 
          href="/login" 
          className="text-blue-500 hover:text-blue-700"
        >
          返回登录
        </a>
      </div>
    </form>
  );
};
