import { Circle, Wifi, WifiOff, RefreshCw, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { OnlineStatus } from '@/hooks/useOnlineStatus';

interface OnlineStatusIndicatorProps {
  status: OnlineStatus;
  onRefresh?: () => void;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

export function OnlineStatusIndicator({ 
  status, 
  onRefresh,
  size = 'sm',
  showText = false,
  className 
}: OnlineStatusIndicatorProps) {
  const { isOnline, isDegraded, isLoading, lastChecked, responseTime, error, servicesSummary, failedServices } = status;

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return 'h-2 w-2';
      case 'md':
        return 'h-3 w-3';
      case 'lg':
        return 'h-4 w-4';
      default:
        return 'h-2 w-2';
    }
  };

  const getStatusColor = () => {
    if (isLoading) return 'text-yellow-500';
    if (!isOnline) return 'text-red-500';
    if (isDegraded) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getStatusIcon = () => {
    if (isLoading) return RefreshCw;
    if (!isOnline) return WifiOff;
    if (isDegraded) return AlertTriangle;
    return Wifi;
  };

  const getTooltipContent = () => {
    const formatTime = (date: Date) => date.toLocaleTimeString();
    
    if (isLoading) {
      return 'Checking API connection...';
    }
    
    if (isOnline && !isDegraded) {
      return (
        <div className="text-center">
          <div className="font-medium text-green-400">API Online</div>
          {lastChecked && (
            <div className="text-xs text-muted-foreground">
              Last checked: {formatTime(lastChecked)}
            </div>
          )}
          {responseTime && (
            <div className="text-xs text-muted-foreground">
              Response time: {responseTime}ms
            </div>
          )}
          {servicesSummary && (
            <div className="text-xs text-green-300 mt-1">
              All {servicesSummary.total} services healthy
            </div>
          )}
        </div>
      );
    }
    
    if (isOnline && isDegraded) {
      return (
        <div className="text-center">
          <div className="font-medium text-yellow-400">API Degraded</div>
          {lastChecked && (
            <div className="text-xs text-muted-foreground">
              Last checked: {formatTime(lastChecked)}
            </div>
          )}
          {responseTime && (
            <div className="text-xs text-muted-foreground">
              Response time: {responseTime}ms
            </div>
          )}
          {servicesSummary && (
            <div className="text-xs text-yellow-300 mt-1">
              {servicesSummary.failed} of {servicesSummary.total} services failed
            </div>
          )}
          {failedServices && failedServices.length > 0 && (
            <div className="text-xs text-red-300 mt-1">
              Failed: {failedServices.join(', ')}
            </div>
          )}
          <div className="text-xs text-blue-300 mt-2 border-t border-gray-600 pt-2">
            💡 Check the App Health page for more details
          </div>
        </div>
      );
    }
    
    return (
      <div className="text-center">
        <div className="font-medium text-red-400">API Offline</div>
        {lastChecked && (
          <div className="text-xs text-muted-foreground">
            Last checked: {formatTime(lastChecked)}
          </div>
        )}
        {error && (
          <div className="text-xs text-red-300 mt-1">
            {error}
          </div>
        )}
        <div className="text-xs text-blue-300 mt-2 border-t border-gray-600 pt-2">
          💡 Check the App Health page for more details
        </div>
      </div>
    );
  };

  const StatusIcon = getStatusIcon();

  const indicator = (
    <div className={cn("flex items-center gap-1", className)}>
      {/* Animated pulse dot for loading state */}
      {isLoading ? (
        <Circle 
          className={cn(
            getSizeClasses(),
            "animate-pulse fill-current",
            getStatusColor()
          )} 
        />
      ) : (
        <Circle 
          className={cn(
            getSizeClasses(),
            "fill-current",
            getStatusColor()
          )} 
        />
      )}
      
      {showText && (
        <>
          <StatusIcon className="h-3 w-3" />
          <span className="text-xs">
            {isLoading ? 'Checking...' : 
             !isOnline ? 'Offline' : 
             isDegraded ? 'Degraded' : 
             'Online'}
          </span>
        </>
      )}
    </div>
  );

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          {onRefresh ? (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto p-1 hover:bg-transparent"
              onClick={onRefresh}
              disabled={isLoading}
            >
              {indicator}
            </Button>
          ) : (
            <div className="cursor-help">
              {indicator}
            </div>
          )}
        </TooltipTrigger>
        <TooltipContent side="bottom" align="center">
          {getTooltipContent()}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}