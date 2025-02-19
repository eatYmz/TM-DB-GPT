import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// 需要登录才能访问的路径
const protectedPaths = ['/', '/chat', '/profile'];

export function middleware(request: NextRequest) {
  // 获取当前路径
  const path = request.nextUrl.pathname;

  // 检查是否是需要保护的路径
  if (protectedPaths.some(pp => path.startsWith(pp))) {
    // 只能通过 cookies 检查 token
    const token = request.cookies.get('token')?.value;

    // 如果没有 token，重定向到登录页
    if (!token) {
      const loginUrl = new URL('/login', request.url);
      // 保存原始目标路径，登录后可以重定向回去
      loginUrl.searchParams.set('from', path);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

// 配置中间件匹配的路径
export const config = {
  matcher: [
    /*
     * 匹配所有需要保护的路径
     * 排除 _next、api 路由、静态文件等
     */
    '/((?!api|_next/static|_next/image|favicon.ico|login|register).*)',
  ],
};