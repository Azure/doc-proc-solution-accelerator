import { useState, useMemo, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, RefreshCw, Edit, Trash2, Settings, Power, PowerOff, Plus, ArrowLeft } from "lucide-react";
import { stepsApi, StepInstance, StepCatalogDefinition } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import ConfigureStepInstanceDialog from "@/components/step/ConfigureStepInstanceDialog";
import { Link } from "react-router-dom";

const StepInstances = () => {
  const [stepInstances, setStepInstances] = useState<StepInstance[]>([]);
  const [selectedInstance, setSelectedInstance] = useState<StepInstance | undefined>();
  const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Load step instances from API
  const loadStepInstances = async () => {
    setLoading(true);
    try {
      const instances = await stepsApi.getInstances();
      setStepInstances(instances);
    } catch (error) {
      console.error('Error loading step instances:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast({
        title: "Failed to load step instances",
        description: errorMessage + '. Ensure the API backend is running.',
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStepInstances();
  }, []);

  const filteredAndGroupedInstances = useMemo(() => {
    const filtered = stepInstances.filter(instance => 
      instance.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      instance.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (instance.category && instance.category.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const grouped = filtered.reduce((acc, instance) => {
      const category = instance.category || 'other';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(instance);
      return acc;
    }, {} as Record<string, StepInstance[]>);

    return grouped;
  }, [stepInstances, searchQuery]);

  const getTypeDisplayName = (type: string) => {
    switch (type) {
      case 'connector': return 'Data Connectors';
      case 'extractor': return 'Text Extractors';
      case 'transformer': return 'Transformers';
      case 'ai_processor': return 'AI Processors';
      case 'output': return 'Output Connectors';
      default: return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };

  const getStatusColor = (enabled: boolean) => {
    return enabled 
      ? 'bg-green-100 text-green-800' 
      : 'bg-gray-100 text-gray-800';
  };

  const handleConfigureInstance = (instance: StepInstance) => {
    setSelectedInstance(instance);
    setIsConfigDialogOpen(true);
  };

  const handleToggleEnabled = async (instanceId: string, enabled: boolean) => {
    try {
      const updatedInstance = await stepsApi.updateInstance(instanceId, { enabled });
      setStepInstances(prev => 
        prev.map(instance => 
          instance.id === instanceId 
            ? { ...instance, enabled }
            : instance
        )
      );
      toast({
        title: "Success",
        description: `Step instance ${enabled ? 'enabled' : 'disabled'} successfully`,
      });
    } catch (error) {
      console.error('Error toggling step instance:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleDeleteInstance = async (instanceId: string) => {
    if (!confirm('Are you sure you want to delete this step instance?')) {
      return;
    }

    try {
      await stepsApi.deleteInstance(instanceId);
      setStepInstances(prev => prev.filter(instance => instance.id !== instanceId));
      toast({
        title: "Success",
        description: "Step instance deleted successfully",
      });
    } catch (error) {
      console.error('Error deleting step instance:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleInstanceUpdated = () => {
    loadStepInstances();
    setIsConfigDialogOpen(false);
    setSelectedInstance(undefined);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Step Instances</h1>
          <p className="text-muted-foreground">Manage configured step instances for your pipelines</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/steps">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Step Catalog
            </Link>
          </Button>
          <Button variant="outline" onClick={loadStepInstances} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search step instances..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {loading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading step instances...</p>
        </div>
      )}

      {!loading && stepInstances.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No step instances found. Create instances from the Step Catalog.</p>
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
                  <StepInstanceCard
                    key={instance.id}
                    instance={instance}
                    onConfigure={() => handleConfigureInstance(instance)}
                    onToggleEnabled={(enabled) => handleToggleEnabled(instance.id, enabled)}
                    onDelete={() => handleDeleteInstance(instance.id)}
                  />
                ))}
              </div>
            </div>
          ))}
          
          {Object.keys(filteredAndGroupedInstances).length === 0 && !loading && stepInstances.length > 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No step instances found matching your search.</p>
            </div>
          )}
        </div>
      )}

      {selectedInstance && (
        <ConfigureStepInstanceDialog
          isOpen={isConfigDialogOpen}
          onClose={() => {
            setIsConfigDialogOpen(false);
            setSelectedInstance(undefined);
          }}
          stepInstance={selectedInstance}
          onInstanceUpdated={handleInstanceUpdated}
        />
      )}
    </div>
  );
};

interface StepInstanceCardProps {
  instance: StepInstance;
  onConfigure: () => void;
  onToggleEnabled: (enabled: boolean) => void;
  onDelete: () => void;
}

const StepInstanceCard = ({ instance, onConfigure, onToggleEnabled, onDelete }: StepInstanceCardProps) => {
  const getStatusColor = (enabled: boolean) => {
    return enabled 
      ? 'bg-green-100 text-green-800' 
      : 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (enabled: boolean) => {
    return enabled ? Power : PowerOff;
  };

  const StatusIcon = getStatusIcon(instance.enabled);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
              <StatusIcon className={`h-5 w-5 ${instance.enabled ? 'text-green-600' : 'text-gray-400'}`} />
            </div>
            <div>
              <CardTitle className="text-lg">{instance.name}</CardTitle>
              <CardDescription className="line-clamp-2">
                {instance.description || instance.catalog_definition?.description}
              </CardDescription>
            </div>
          </div>
          <div className="flex flex-col items-end space-y-2">
            {instance.category && (
              <Badge variant="secondary">{instance.category}</Badge>
            )}
            <Badge className={getStatusColor(instance.enabled)}>
              {instance.enabled ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <p className="text-muted-foreground">Catalog</p>
            <p className="font-medium">{instance.step_catalog_id}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Timeout</p>
            <p className="font-medium">{instance.timeout}s</p>
          </div>
        </div>
        
        {instance.tags && instance.tags.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-1">
              {instance.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {instance.tags.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{instance.tags.length - 3}
                </Badge>
              )}
            </div>
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
            <Button variant="outline" size="sm" onClick={onConfigure}>
              <Settings className="h-4 w-4 mr-2" />
              Configure
            </Button>
            <Button variant="outline" size="sm" onClick={onDelete} className="text-destructive">
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default StepInstances;