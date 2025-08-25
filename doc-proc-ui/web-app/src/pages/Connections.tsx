
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { RefreshCw, CheckCircle, XCircle, AlertTriangle, Database, Search, Zap } from "lucide-react";

interface ConnectionStatus {
  id: string;
  name: string;
  type: 'database' | 'search' | 'ai';
  status: 'connected' | 'error' | 'warning';
  lastChecked: string;
  error?: string;
  details?: string;
  icon: typeof Database;
}

const Connections = () => {
  const [connections, setConnections] = useState<ConnectionStatus[]>([
    {
      id: "cosmos-db",
      name: "Azure Cosmos DB",
      type: "database",
      status: "connected",
      lastChecked: "2024-06-20T07:30:00Z",
      details: "Primary endpoint responding normally",
      icon: Database
    },
    {
      id: "ai-search",
      name: "Azure AI Search",
      type: "search",
      status: "error",
      lastChecked: "2024-06-20T07:29:45Z",
      error: "Authentication failed: Invalid API key",
      details: "Service endpoint is reachable but authentication is failing",
      icon: Search
    },
    {
      id: "ai-services",
      name: "Azure AI Services",
      type: "ai",
      status: "warning",
      lastChecked: "2024-06-20T07:28:30Z",
      error: "Rate limit exceeded",
      details: "Service is available but rate limits are being hit",
      icon: Zap
    }
  ]);

  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // Simulate API call to check connections
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Update last checked times
    setConnections(prev => prev.map(conn => ({
      ...conn,
      lastChecked: new Date().toISOString()
    })));
    
    setIsRefreshing(false);
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
        <Button onClick={handleRefresh} disabled={isRefreshing}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh All
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {connections.map((connection) => {
          const IconComponent = connection.icon;
          return (
            <Card key={connection.id}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <IconComponent className="h-5 w-5 text-muted-foreground" />
                    <CardTitle className="text-lg">{connection.name}</CardTitle>
                  </div>
                  {getStatusIcon(connection.status)}
                </div>
                <CardDescription>
                  Last checked: {formatLastChecked(connection.lastChecked)}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Status:</span>
                  {getStatusBadge(connection.status)}
                </div>
                
                {connection.details && (
                  <div className="text-sm text-muted-foreground">
                    {connection.details}
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
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connection Health Summary</CardTitle>
          <CardDescription>Overview of all service connections</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="space-y-2">
              <div className="text-2xl font-bold text-green-600">
                {connections.filter(c => c.status === 'connected').length}
              </div>
              <div className="text-sm text-muted-foreground">Connected</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-yellow-600">
                {connections.filter(c => c.status === 'warning').length}
              </div>
              <div className="text-sm text-muted-foreground">Warnings</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-red-600">
                {connections.filter(c => c.status === 'error').length}
              </div>
              <div className="text-sm text-muted-foreground">Errors</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Connections;