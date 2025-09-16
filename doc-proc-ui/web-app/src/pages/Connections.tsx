
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { RefreshCw, CheckCircle, XCircle, AlertTriangle, Server, Globe } from "lucide-react";
import { ServiceIcon } from "@/components/service/ServiceIcon";
import { healthApi, SystemHealth, ServiceHealth } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface ConnectionStatus {
  id: string;
  name: string;
  type: 'api' | 'database' | 'storage' | 'queue' | 'config';
  status: 'connected' | 'error' | 'unknown';
  lastChecked: string;
  message?: string;
  error?: string;
  details?: Record<string, any>;
  endpoint?: string;
  responseTime?: number;
}

const Connections = () => {
  const [connections, setConnections] = useState<ConnectionStatus[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  // Load connections on component mount
  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    setLoading(true);
    await checkConnections();
    setLoading(false);
  };

  const checkConnections = async () => {
    const newConnections: ConnectionStatus[] = [];
        
    try {

      const startTime = Date.now();

      // Use the health check API
      const systemHealth: SystemHealth = await healthApi.healthCheck();
      
      const responseTime = Date.now() - startTime;

      // Add a connection status for the Backend Api as well
      newConnections.push({
          id: "web-app-backend-api",
          name: "Web App Backend API",
          type: "api",
          status: "connected",
          lastChecked: new Date().toISOString(),
          message: `API responding - connected`,
          endpoint: (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8000",
          responseTime
        });

      // Convert backend health data to frontend format
      Object.entries(systemHealth.services).forEach(([serviceId, service]) => {
        const connectionStatus: ConnectionStatus = {
          id: serviceId,
          name: service.name === 'cosmos_db' ? 'Azure Cosmos DB' :
                service.name === 'storage_queue' ? 'Azure Storage Queue' :
                service.name === 'app_config' ? 'Azure App Configuration' :
                service.name,
          type: service.name === 'cosmos_db' ? 'database' :
                service.name === 'storage_queue' ? 'storage' :
                service.name === 'app_config' ? 'config' :
                'api' as const,
          status: service.status === 'connected' ? 'connected' :
                  service.status === 'error' ? 'error' :
                  'unknown',
          lastChecked: service.last_checked,
          message: service.message,
          details: service.details,
          endpoint: service.endpoint,
          responseTime: service.response_time_ms
        };

        if (service.status !== 'connected' && service.error) {
          connectionStatus.error = service.error;
        }

        newConnections.push(connectionStatus);
      });

    } catch (error) {
      console.error("Health check failed:", error);
      
      newConnections.push({
          id: "backend-api",
          name: "Backend API",
          type: "api",
          status: "error",
          lastChecked: new Date().toISOString(),
          error: error instanceof Error ? error.message : "Connection failed",
          message: "Unable to reach backend API service",
          endpoint: (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8000"
        });
      }

      setConnections(newConnections);

  };

    
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await checkConnections();
      toast({
        title: "Connections Refreshed",
        description: "All connection statuses have been updated.",
      });
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: "Some connections could not be checked.",
        variant: "destructive",
      });
    }
    setIsRefreshing(false);
  };

  const getServiceIconType = (type: string): string => {
    switch (type) {
      case 'api':
        return 'api';
      case 'database':
        return 'cosmosdb';
      case 'storage':
        return 'azureblob';
      case 'queue':
        return 'queue';
      case 'config':
        return 'settings';
      default:
        return 'server';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <XCircle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return <Badge variant="default" className="bg-green-100 text-green-800">Connected</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      case 'warning':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const formatLastChecked = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Connections</h1>
          <p className="text-muted-foreground">Monitor the status of backend service connections</p>
        </div>
        <Button onClick={handleRefresh} disabled={isRefreshing || loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh All
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Checking connections...</span>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {connections.map((connection) => (
            <Card key={connection.id}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <ServiceIcon 
                      iconName={getServiceIconType(connection.type)}
                      category={connection.type}
                      type={connection.type}
                      className="h-5 w-5 text-muted-foreground" 
                    />
                    <CardTitle className="text-lg">{connection.name}</CardTitle>
                  </div>
                  {getStatusIcon(connection.status)}
                </div>
                <CardDescription>
                  Last checked: {formatLastChecked(connection.lastChecked)}
                  {connection.endpoint && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {connection.endpoint}
                    </div>
                  )}
                  {connection.responseTime && (
                    <div className="text-xs text-muted-foreground">
                      Response time: {connection.responseTime}ms
                    </div>
                  )}
                  {connection.details?.credential_type && (
                    <div className="text-xs text-muted-foreground">
                      Credential type: {connection.details.credential_type}
                    </div>
                  )}
                  {connection.details?.credential_details?.client_id && (
                    <div className="text-xs text-muted-foreground">
                      Client ID: {JSON.stringify(connection.details.credential_details.client_id)}
                    </div>
                  )}
                  {connection.details?.credential_details?.object_id && (
                    <div className="text-xs text-muted-foreground">
                      Object ID: {JSON.stringify(connection.details.credential_details.object_id)}
                    </div>
                  )}
                  {connection.details?.credential_details?.upn && (
                    <div className="text-xs text-muted-foreground">
                      UPN: {JSON.stringify(connection.details.credential_details.upn)}
                    </div>
                  )}
                  
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Status:</span>
                  {getStatusBadge(connection.status)}
                </div>
                
                {connection.message && (
                  <div className="text-sm text-muted-foreground">
                    {connection.message}
                  </div>
                )}
                
                {connection.error && (
                  <Alert variant={connection.status === 'error' ? 'destructive' : 'default'}>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>
                      {connection.status === 'error' ? 'Connection Error' : 'Warning'}
                    </AlertTitle>
                    <AlertDescription>{connection.error}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Connection Health Summary</CardTitle>
          <CardDescription>Overview of all service connections</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="space-y-2">
              <div className="text-2xl font-bold text-green-600">
                {connections.filter(c => c.status === 'connected').length}
              </div>
              <div className="text-sm text-muted-foreground">Connected</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-red-600">
                {connections.filter(c => c.status === 'error').length}
              </div>
              <div className="text-sm text-muted-foreground">Errors</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-blue-600">
                {connections.filter(c => c.status === 'unknown').length}
              </div>
              <div className="text-sm text-muted-foreground">Unknown</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Connections;