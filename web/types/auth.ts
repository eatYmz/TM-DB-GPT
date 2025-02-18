import { ApiUserModel } from '../lib/dto/models/user.dto';

// 用户登录参数
export interface LoginCredentials {
  username: string;
  password: string;
}

// 登录响应
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: ApiUserModel;
}

// 认证状态
export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: ApiUserModel | null;
  error: string | null;
}

// Session状态
export interface SessionState {
  user?: {
    user_id: string;
    user_name: string;
    token: string;
    tokenExpiry: number;
  };
}

export interface RegisterParams {
  username: string;
  password: string;
  email: string;
  nickname: string;
  // 其他注册需要的字段
}
