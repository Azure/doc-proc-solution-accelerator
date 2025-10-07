import { useState, useMemo, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, RefreshCw, ArrowLeft, Activity } from "lucide-react";
import { sourcesApi, SourceInstance, vaultsApi, Vault, ErrorWithData } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import ConfigureSourceInstanceDialog from "@/components/source/ConfigureSourceInstanceDialog";
import SourceInstanceCard from "@/components/source/SourceInstanceCard";
import { Link } from "react-router-dom";


const SourceInstances = () => {
  const [sourceInstances, setSourceInstances] = useState<SourceInstance[]>([]);
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<SourceInstance | undefined>();
  const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [testingConnections, setTestingConnections] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  // Load source instances from API
  const loadSourceInstances = async () => {
    setLoading(true);
    try {
      const instances = await sourcesApi.getInstances();
      setSourceInstances(instances);
      await loadVaults();
      
    } catch (error) {
      console.error('Error loading source instances:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast({
        title: "Failed to load source instances",
        description: errorMessage + '. Ensure the API backend is running.',
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadVaults = async () => {
    try {
      const vaults = await vaultsApi.getVaults();
      if (vaults.length > 0) {
        setVaults(vaults);
      } else {
        setVaults([]);
      }
    } catch (error) {
      console.error("Error loading vaults:", error);
      setVaults([]);

      const errMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error';
      toast({
        title: "Error",
        description: "Failed to load vault information: " + errMessage,
        variant: "destructive",
      });
    }
  };

  useEffect(() => {
    loadSourceInstances();
    
  }, []);

  const filteredAndGroupedInstances = useMemo(() => {
    const filtered = sourceInstances.filter(instance => 
      instance.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      instance.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (instance.catalog_definition?.category && instance.catalog_definition.category.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const grouped = filtered.reduce((acc, instance) => {
      const category = instance.catalog_definition?.category || 'other';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(instance);
      return acc;
    }, {} as Record<string, SourceInstance[]>);

    return grouped;
  }, [sourceInstances, searchQuery]);

  const getTypeDisplayName = (type: string) => {
    switch (type) {
      case 'database': return 'Databases';
      case 'cloud-storage': return 'Cloud Storage';
      case 'file-system': return 'File Systems';
      case 'web-crawler': return 'Web Crawlers';
      case 'api': return 'API Sources';
      case 'sharepoint': return 'SharePoint';
      case 'blob': return 'Blob Storage';
      default: return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };

  const getStatusColor = (enabled: boolean) => {
    return enabled 
      ? 'bg-green-100 text-green-800' 
      : 'bg-gray-100 text-gray-800';
  };

  const handleConfigureInstance = (instance: SourceInstance) => {
    setSelectedInstance(instance);
    setIsConfigDialogOpen(true);
  };

  const handleToggleEnabled = async (instanceId: string, enabled: boolean) => {
    try {
      const instance = sourceInstances.find(s => s.id === instanceId);
      if (!instance) return;

      const updatedInstance = await sourcesApi.updateInstance(instanceId, { 
        name: instance.name,
        enabled 
      });
      
      setSourceInstances(prev => 
        prev.map(instance => 
          instance.id === instanceId 
            ? { ...instance, enabled }
            : instance
        )
      );
      toast({
        title: "Success",
        description: `Source instance ${enabled ? 'enabled' : 'disabled'} successfully`,
      });
    } catch (error) {
      console.error('Error toggling source instance:', error);
      const errorMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error occurred';

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleTestConnection = async (instanceId: string, instanceName: string) => {
    try {
      setTestingConnections(prev => new Set(prev).add(instanceId));
      
      const result = await sourcesApi.testConnection(instanceId);
      
      // Update the instance's status in the list
      setSourceInstances(prev => 
        prev.map(instance => 
          instance.id === instanceId 
            ? { 
                ...instance, 
                status: {
                  status: result.status as any,
                  message: result.message,
                  tested_at: result.tested_at,
                  details: result.details
                }
              }
            : instance
        )
      );

      toast({
        title: result.status === 'connected' ? "Connection Successful" : "Connection Failed",
        description: result.message,
        variant: result.status === 'connected' ? "default" : "destructive",
      });
    } catch (error) {
      console.error('Error testing connection:', error);
      const errorMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error occurred';
      
      toast({
        title: "Connection Test Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setTestingConnections(prev => {
        const next = new Set(prev);
        next.delete(instanceId);
        return next;
      });
    }
  };

  const handleDeleteInstance = async (instanceId: string, instanceName: string) => {
    try {
      await sourcesApi.deleteInstance(instanceId);
      setSourceInstances(prev => prev.filter(instance => instance.id !== instanceId));
      
      toast({
        title: "Source instance deleted successfully",
        description: `${instanceName} has been deleted.`,
        variant: "default",
      });
    } catch (error) {
      console.error('Error deleting source instance:', error);
      const errorMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error occurred';
      
      toast({
        title: "Failed to delete source instance",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleInstanceUpdated = () => {
    loadSourceInstances();
    setIsConfigDialogOpen(false);
    setSelectedInstance(undefined);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Source Instances</h1>
          <p className="text-muted-foreground">Manage configured source instances for your pipelines</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/sources">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Source Catalog
            </Link>
          </Button>
          <Button variant="outline" onClick={loadSourceInstances} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search source instances..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="text-center">
              <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p className="text-center text-muted-foreground">Loading source instances...</p>
            </div>
        </div>
      )}

      {!loading && sourceInstances.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No source instances found. Create instances from the Source Catalog.</p>
        </div>
      )}

      {!loading && (
        <div className="space-y-8">
          {Object.entries(filteredAndGroupedInstances).map(([category, categoryInstances]) => (
            <div key={category} className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground">
                {getTypeDisplayName(category)} ({categoryInstances.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categoryInstances.map((instance) => (
                  <SourceInstanceCard
                    key={instance.id}
                    instance={instance}
                    vault={vaults && vaults.length > 0 ? vaults.find(v => v.source_instance_name === instance.name) || null : null}
                    onConfigure={() => handleConfigureInstance(instance)}
                    onToggleEnabled={(enabled) => handleToggleEnabled(instance.id, enabled)}
                    onTestConnection={() => handleTestConnection(instance.id, instance.name)}
                    onDelete={() => handleDeleteInstance(instance.id, instance.name)}
                    isTestingConnection={testingConnections.has(instance.id)}
                  />
                ))}
              </div>
            </div>
          ))}
          
          {Object.keys(filteredAndGroupedInstances).length === 0 && !loading && sourceInstances.length > 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No source instances found matching your search.</p>
            </div>
          )}
        </div>
      )}

      {selectedInstance && (
        <ConfigureSourceInstanceDialog
          isOpen={isConfigDialogOpen}
          onClose={() => {
            setIsConfigDialogOpen(false);
            setSelectedInstance(undefined);
          }}
          sourceInstance={selectedInstance}
          onInstanceUpdated={handleInstanceUpdated}
        />
      )}
    </div>
  );
};



export default SourceInstances;