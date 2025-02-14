import { 
  STORAGE_TOKEN_KET,
  STORAGE_USERINFO_KEY,
  STORAGE_USERINFO_VALID_TIME_KEY 
} from './constants/storage';

// Token 操作工具类
export class TokenManager {
  // 存储 token
  static setToken(token: string): void {
    localStorage.setItem(STORAGE_TOKEN_KET, token);
  }

  // 获取 token
  static getToken(): string | null {
    return localStorage.getItem(STORAGE_TOKEN_KET);
  }

  // 移除 token
  static removeToken(): void {
    localStorage.removeItem(STORAGE_TOKEN_KET);
    localStorage.removeItem(STORAGE_USERINFO_KEY);
    localStorage.removeItem(STORAGE_USERINFO_VALID_TIME_KEY);
  }

  // 检查是否有 token
  static isTokenValid(): boolean {
    const token = this.getToken();
    const validTime = localStorage.getItem(STORAGE_USERINFO_VALID_TIME_KEY);
    if (!token || !validTime) return false;
    return Date.now() < parseInt(validTime);
  }
}
