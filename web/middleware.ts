import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// 公开路径（不需要token）
const publicPaths = [
  '/login',
  '/api/auth/login',
  '/register',
  '/api/auth/register',
  '/',  // 假设首页是公开的
];

// 需要保护的路径
const protectedPaths = [
  '/logout',  // 登出需要保护
  '/api/auth/logout',  // 登出API需要保护
];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // 如果是公开路径，直接放行
  if (publicPaths.includes(pathname)) {
    return NextResponse.next();
  }

  // 如果不是受保护的路径，直接放行
  if (!protectedPaths.some(path => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  // 获取请求头中的 token
  const token = req.headers.get('Authorization')?.replace('Bearer ', '');

  // 如果是受保护的路径且没有 token，重定向到登录页
  if (!token) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|favicon.ico).*)'],
};