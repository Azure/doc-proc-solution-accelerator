import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Trash2, Settings, Power, PowerOff, Activity, TestTube, CheckCircle, AlertTriangle } from "lucide-react";
import { SourceInstance, Vault, sourcesApi, ErrorWithData } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useEffect, useState } from "react";
import { useToast } from "@/hooks/use-toast";

interface SourceInstanceCardProps {
  instance: SourceInstance;
  vault: Vault;
  onConfigure: () => void;
  onToggleEnabled: (enabled: boolean) => void;
  onTestConnection: () => void;
  onDelete: () => void;
  isTestingConnection: boolean;
}

const SourceInstanceCard = ({ 
  instance,
  vault,
  onConfigure, 
  onToggleEnabled, 
  onTestConnection, 
  onDelete, 
  isTestingConnection 
}: SourceInstanceCardProps) => {
  const { toast } = useToast();

  const [deleteConfirmation, setDeleteConfirmation] = useState(false);
  const [confirmationName, setConfirmationName] = useState("");
  
  
  const getStatusColor = (enabled: boolean) => {
    return enabled 
      ? 'bg-green-100 text-green-800' 
      : 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (enabled: boolean) => {
    return enabled ? Power : PowerOff;
  };

  const getConnectionStatusIcon = (status?: string) => {
    switch (status) {
      case 'connected': return CheckCircle;
      case 'error': return AlertTriangle;
      default: return TestTube;
    }
  };

  const getConnectionStatusColor = (status?: string) => {
    switch (status) {
      case 'connected': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-yellow-600';
    }
  };

  const StatusIcon = getStatusIcon(instance.enabled);
  const ConnectionIcon = getConnectionStatusIcon(instance.status?.status);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
              {(vault && vault.name) ? (
              <StatusIcon className={`h-5 w-5 ${instance.enabled ? 'text-green-600' : 'text-gray-400'}`} />
              ) : (
                <StatusIcon className={`h-5 w-5 ${instance.enabled ? 'text-yellow-600' : 'text-gray-400'}`} />
              )}
            </div>
            <div>
              <CardTitle className="text-lg">
                <Tooltip>
                  <TooltipTrigger>{instance.name.substring(0, 37)}</TooltipTrigger>
                  <TooltipContent>
                   <span>{instance.name}</span>
                  </TooltipContent>
                 </Tooltip>
                </CardTitle>
              <CardDescription className="line-clamp-2">
                {instance.description || instance.catalog_definition?.description}
              </CardDescription>
            </div>
          </div>
          <div className="flex flex-col items-end space-y-2">
            {instance.catalog_definition?.type && (
              <Badge variant="secondary">{instance.catalog_definition.type}</Badge>
            )}
            <Badge className={getStatusColor(instance.enabled)}>
              {instance.enabled ? 'Enabled' : 'Disabled'}
            </Badge>
            {vault && vault.name ? (
              <Tooltip>
                <TooltipTrigger><Badge variant="default">{vault.name}</Badge></TooltipTrigger>
                <TooltipContent>
                  <span>This source instance is associated with {vault.name}. <br />All documents crawled by this instance will be stored in this vault.</span>
                </TooltipContent>
              </Tooltip>
            ) : (
              <Tooltip>
                <TooltipTrigger><AlertTriangle className="h-7 w-7 text-yellow-600" /> </TooltipTrigger>
                <TooltipContent>
                  <span>This source instance is not associated with any vault.<br />No documents will be crawled by this source instance.</span>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <p className="text-muted-foreground">Catalog</p>
            <p className="font-medium">{instance.source_catalog_id}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Connection Status</p>
            <div className="flex items-center space-x-1">
              <ConnectionIcon className={`h-3 w-3 ${getConnectionStatusColor(instance.status?.status)}`} />
              <p className={`font-medium capitalize ${getConnectionStatusColor(instance.status?.status)}`}>
                {instance.status?.status || 'Unknown'}
              </p>
            </div>
          </div>
        </div>
        
        {instance.catalog_definition?.tags && instance.catalog_definition.tags.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-1">
              {instance.catalog_definition.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {instance.catalog_definition.tags.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{instance.catalog_definition.tags.length - 3}
                </Badge>
              )}
            </div>
          </div>
        )}

        {(instance.last_crawl_at || instance.last_crawl_status) && (
          <div className="grid grid-cols-2 gap-4 text-sm mb-4">
            {instance.last_crawl_at && (
              <div>
                <p className="text-muted-foreground">Last Crawl At</p>
                <p className="font-medium">
                  {new Date(instance.last_crawl_at).toLocaleString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            )}
            {instance.last_crawl_status && (
              <div>
                <p className="text-muted-foreground">Last Crawl Status</p>
                <p className="font-medium capitalize">{instance.last_crawl_status}</p>
              </div>
            )}
          </div>
        )}


        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Switch
              checked={instance.enabled}
              onCheckedChange={onToggleEnabled}
            />
            <span className="text-sm text-muted-foreground">
              {instance.enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          
          <div className="flex space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onTestConnection}
              disabled={isTestingConnection}
            >
              {isTestingConnection ? (
                <Activity className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <TestTube className="h-4 w-4 mr-2" />
              )}
              Test
            </Button>
            <Button variant="outline" size="sm" onClick={onConfigure}>
              <Settings className="h-4 w-4 mr-2" />
              Configure
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" size="sm" className="text-destructive hover:text-destructive">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Source Instance</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to delete "{instance.name}"? This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                
                <div className="space-y-4 py-4">
                  <div className="flex items-center justify-between rounded-lg border p-3">
                    <div className="space-y-0.5">
                      <label className="text-sm font-medium">I understand the consequences</label>
                      <p className="text-xs text-muted-foreground">
                        Confirm that you understand this action cannot be undone
                      </p>
                    </div>
                    <Switch
                      checked={deleteConfirmation}
                      onCheckedChange={setDeleteConfirmation}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-sm font-medium">
                      Type "{instance.name}" to confirm
                    </label>
                    <Input
                      placeholder="Enter instance name to confirm deletion"
                      value={confirmationName}
                      onChange={(e) => setConfirmationName(e.target.value)}
                      className="w-full"
                    />
                  </div>
                </div>
                
                <AlertDialogFooter>
                  <AlertDialogCancel onClick={() => {
                    setDeleteConfirmation(false);
                    setConfirmationName("");
                  }}>
                    Cancel
                  </AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => {
                      onDelete();
                      setDeleteConfirmation(false);
                      setConfirmationName("");
                    }}
                    disabled={!deleteConfirmation || confirmationName !== instance.name}
                    className="bg-red-600 hover:bg-red-700 focus:ring-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SourceInstanceCard;
export type { SourceInstanceCardProps };