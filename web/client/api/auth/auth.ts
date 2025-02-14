import { LoginCredentials, LoginResponse, RegisterParams } from '../../../types/auth';
import { POST } from '../index';

/**
 * 登录
 */
export const authLogin = (credentials: LoginCredentials) => {
  return POST<LoginCredentials, LoginResponse>('/auth/login', credentials);
};

/**
 * 登出
 */
export const authLogout = () => {
  return POST<null, void>('/auth/logout');
};

/**
 * 注册
 */
export const authRegister = (params: RegisterParams) => {
  return POST<RegisterParams, void>('/auth/register', params);
};
