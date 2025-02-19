import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { TokenManager } from '@/utils/token';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 简化检查逻辑
    if (!TokenManager.isTokenValid()) {
      router.push(`/login?from=${router.pathname}`);
    } else {
      TokenManager.refreshTokenStorage();
      setIsLoading(false);
    }
  }, [router.pathname]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return <>{children}</>;
}
