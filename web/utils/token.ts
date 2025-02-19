import { 
  STORAGE_TOKEN_KET,
  STORAGE_USERINFO_KEY,
  STORAGE_USERINFO_VALID_TIME_KEY,
  STORAGE_TOKEN_MAX_AGE,
} from './constants/storage';

// Token 操作工具类
export class TokenManager {  
  // 存储 token
  static setToken(token: string, expiresIn: number = STORAGE_TOKEN_MAX_AGE): void {
    if (!token) return;

    const expiresAt = Date.now() + (expiresIn * 1000);
    
    // 存储 token 和过期时间
    localStorage.setItem(STORAGE_TOKEN_KET, token);
    localStorage.setItem(STORAGE_USERINFO_VALID_TIME_KEY, expiresAt.toString());
    
    // 设置 cookie
    document.cookie = `token=${token}; path=/; max-age=${expiresIn}; SameSite=Lax; Secure`;
  }

  // 获取 token
  static getToken(): string | null {
    const token = localStorage.getItem(STORAGE_TOKEN_KET);
    const expiresAt = localStorage.getItem(STORAGE_USERINFO_VALID_TIME_KEY);
    
    if (!token || !expiresAt) return null;
    
    // 检查是否过期
    if (Date.now() > parseInt(expiresAt)) {
      this.removeToken();
      return null;
    }
    
    return token;
  }

  // 移除 token
  static removeToken(): void {
    localStorage.removeItem(STORAGE_TOKEN_KET);
    localStorage.removeItem(STORAGE_USERINFO_KEY);
    localStorage.removeItem(STORAGE_USERINFO_VALID_TIME_KEY);
    document.cookie = `token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
  }

  // 刷新 token 的存储时间
  static refreshTokenStorage(): void {
    const token = this.getToken();
    if (token) {
      this.setToken(token, STORAGE_TOKEN_MAX_AGE);
    }
  }

  // 从 cookie 中恢复 token
  static syncFromCookie(): boolean {
    try {
      // 从 cookie 中获取 token
      const cookies = document.cookie.split(';');
      const tokenCookie = cookies.find(cookie => cookie.trim().startsWith('token='));
      
      if (tokenCookie) {
        const token = tokenCookie.split('=')[1].trim();
        if (token) {
          // 如果 cookie 中有 token 但 localStorage 中没有，则恢复
          this.setToken(token, STORAGE_TOKEN_MAX_AGE);
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Error syncing token from cookie:', error);
      return false;
    }
  }

  // 增强版的 isTokenValid
  static isTokenValid(): boolean {
    const token = this.getToken();
    const expiresAt = localStorage.getItem(STORAGE_USERINFO_VALID_TIME_KEY);
    
    if (!token || !expiresAt) {
      // 如果 localStorage 中没有 token，尝试从 cookie 恢复
      return this.syncFromCookie();
    }
    
    const isValid = Date.now() < parseInt(expiresAt);
    if (!isValid) {
      this.removeToken();
    }
    
    return isValid;
  }
}
