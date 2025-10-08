import { useState, useEffect, useCallback } from 'react';
import { healthApi, SystemHealth } from '@/lib/api';

export interface OnlineStatus {
  isOnline: boolean;
  isDegraded: boolean;
  isLoading: boolean;
  lastChecked: Date | null;
  responseTime: number | null;
  error: string | null;
  servicesSummary?: {
    connected: number;
    failed: number;
    total: number;
  };
  failedServices?: string[];
}

interface UseOnlineStatusOptions {
  checkInterval?: number; // milliseconds
  enabled?: boolean;
}

export const useOnlineStatus = (options: UseOnlineStatusOptions = {}) => {
  const { checkInterval = 5*60*1000, enabled = true } = options; // Default: check every 5 minutes
  
  const [status, setStatus] = useState<OnlineStatus>({
    isOnline: false,
    isDegraded: false,
    isLoading: true,
    lastChecked: null,
    responseTime: null,
    error: null,
  });

  const checkApiHealth = useCallback(async () => {
    if (!enabled) return;

    setStatus(prev => ({ ...prev, isLoading: true, error: null }));
    
    const startTime = Date.now();
    
    try {
      const systemHealth: SystemHealth = await healthApi.healthCheck();
      const responseTime = Date.now() - startTime;
      
      // Check if any services are failing
      const failedServices: string[] = [];
      Object.entries(systemHealth.services).forEach(([serviceName, service]) => {
        if (service.status === 'error') {
          failedServices.push(serviceName);
        }
      });
      
      const isDegraded = failedServices.length > 0 && systemHealth.status !== 'error';
      const isOnline = systemHealth.status !== 'error';
      
      setStatus({
        isOnline,
        isDegraded,
        isLoading: false,
        lastChecked: new Date(),
        responseTime,
        error: null,
        servicesSummary: { connected: Object.keys(systemHealth.services).length - failedServices.length, total: Object.keys(systemHealth.services).length, failed: failedServices.length },
        failedServices: failedServices.length > 0 ? failedServices : undefined,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Connection failed';
      
      setStatus({
        isOnline: false,
        isDegraded: false,
        isLoading: false,
        lastChecked: new Date(),
        responseTime: null,
        error: errorMessage,
        servicesSummary: undefined,
        failedServices: undefined,
      });
    }
  }, [enabled]);

  // Initial check
  useEffect(() => {
    if (enabled) {
      checkApiHealth();
    }
  }, [checkApiHealth, enabled]);

  // Set up periodic health checks
  useEffect(() => {
    if (!enabled) return;

    const interval = setInterval(checkApiHealth, checkInterval);
    
    return () => clearInterval(interval);
  }, [checkApiHealth, checkInterval, enabled]);

  // Manual refresh function
  const refresh = useCallback(() => {
    checkApiHealth();
  }, [checkApiHealth]);

  return {
    ...status,
    refresh,
  };
};