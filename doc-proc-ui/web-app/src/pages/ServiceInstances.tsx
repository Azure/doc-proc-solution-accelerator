import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Link } from "react-router-dom";
import { 
  Server, 
  TestTube, 
  AlertTriangle,
  CheckCircle,
  Search,
  Loader2,
  Settings2,
  Trash2,
  Plus,
  Clock,
  X,
  ArrowLeft
} from "lucide-react";
import { AddServiceInstanceDialog } from "@/components/service/AddServiceInstanceDialog";
import { ConfigureServiceInstanceDialog } from "@/components/service/ConfigureServiceInstanceDialog";
import { servicesApi, ServiceInstance, ServiceCatalogDefinition } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { ServiceIcon } from "@/components/service/ServiceIcon";
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
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreVertical } from "lucide-react";

const ServiceInstances = () => {
  const [instances, setInstances] = useState<ServiceInstance[]>([]);
  const [catalog, setCatalog] = useState<ServiceCatalogDefinition[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testingConnections, setTestingConnections] = useState<Set<string>>(new Set());
  const { toast } = useToast();

  // Load service instances and catalog from API
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [instancesData, catalogData] = await Promise.all([
        servicesApi.getInstances(),
        servicesApi.getCatalog()
      ]);
      setInstances(instancesData);
      setCatalog(catalogData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load service instances';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage + '. Ensure the API backend is running and connected to CosmosDB.',
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (instanceId: string) => {
    if (testingConnections.has(instanceId)) return;
    
    try {
      setTestingConnections(prev => new Set([...prev, instanceId]));
      
      // Update the instance status to testing immediately for UI feedback
      setInstances(prev => prev.map(instance => 
        instance.id === instanceId 
          ? { ...instance, connection_status: { ...instance.connection_status, status: 'testing' as const } }
          : instance
      ));

      const result = await servicesApi.testConnection(instanceId);
      
      toast({
        title: result.success ? "Connection successful" : "Connection failed",
        description: result.message,
        variant: result.success ? "default" : "destructive",
      });

      // Reload instances to get updated connection status
      await loadData();
    } catch (error) {
      toast({
        title: "Connection test failed",
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: "destructive",
      });
    } finally {
      setTestingConnections(prev => {
        const newSet = new Set(prev);
        newSet.delete(instanceId);
        return newSet;
      });
    }
  };

  const addServiceInstance = async (serviceData: any) => {
    try {
      const newInstance = await servicesApi.createInstance({
        name: serviceData.name,
        description: serviceData.description,
        service_catalog_id: serviceData.service_catalog_id,
        settings: serviceData.settings || {}
      });
      
      setInstances(prev => [...prev, newInstance]);
      
      toast({
        title: "Service instance created",
        description: `${newInstance.name} has been created successfully`,
      });
    } catch (error) {
      toast({
        title: "Failed to create service instance",
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: "destructive",
      });
    }
  };

  const updateServiceInstance = async (instanceId: string, config: any) => {
    try {
      const updatedInstance = await servicesApi.updateInstance(instanceId, config);
      
      setInstances(prev => prev.map(instance => 
        instance.id === instanceId ? updatedInstance : instance
      ));
      
      toast({
        title: "Service instance updated",
        description: `${updatedInstance.name} has been updated successfully`,
      });
    } catch (error) {
      toast({
        title: "Failed to update service instance",
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: "destructive",
      });
    }
  };

  const deleteServiceInstance = async (instanceId: string) => {
    try {
      await servicesApi.deleteInstance(instanceId);
      
      setInstances(prev => prev.filter(instance => instance.id !== instanceId));
      
      toast({
        title: "Service instance deleted",
        description: "The service instance has been deleted successfully",
      });
    } catch (error) {
      toast({
        title: "Failed to delete service instance",
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: "destructive",
      });
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="h-3 w-3 text-green-600" />;
      case 'error': return <AlertTriangle className="h-3 w-3 text-red-600" />;
      case 'testing': return <TestTube className="h-3 w-3 text-blue-600 animate-pulse" />;
      default: return <AlertTriangle className="h-3 w-3 text-gray-600" />;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'connected': return 'bg-green-100 text-green-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'testing': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'Database': return 'bg-purple-100 text-purple-800';
      case 'AI Platform': return 'bg-blue-100 text-blue-800';
      case 'Storage': return 'bg-orange-100 text-orange-800';
      case 'Search Engine': return 'bg-green-100 text-green-800';
      case 'Integration': return 'bg-pink-100 text-pink-800';
      case 'Analytics': return 'bg-yellow-100 text-yellow-800';
      case 'Monitoring': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryColor = (category?: string) => {
    if (!category) return 'bg-gray-100 text-gray-800';
    switch (category.toLowerCase()) {
      case 'data': return 'bg-purple-100 text-purple-800';
      case 'ai': return 'bg-blue-100 text-blue-800';
      case 'ai services': return 'bg-blue-100 text-blue-800';
      case 'ai/ml': return 'bg-blue-100 text-blue-800';
      case 'database': return 'bg-purple-100 text-purple-800';
      case 'storage': return 'bg-orange-100 text-orange-800';
      case 'search': return 'bg-green-100 text-green-800';
      case 'integration': return 'bg-pink-100 text-pink-800';
      case 'analytics': return 'bg-yellow-100 text-yellow-800';
      case 'monitoring': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatLastTested = (lastTested?: string) => {
    if (!lastTested) return 'Never';
    try {
      return new Date(lastTested).toLocaleString();
    } catch {
      return 'Invalid date';
    }
  };

  const filteredInstances = instances.filter(instance =>
    instance.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    instance.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (instance.description && instance.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (instance.category && instance.category.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Group instances by category
  const groupedInstances = filteredInstances.reduce((acc, instance) => {
    const category = instance.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(instance);
    return acc;
  }, {} as Record<string, ServiceInstance[]>);

  const instanceCategories = Object.keys(groupedInstances).sort();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Service Instances</h1>
          <p className="text-muted-foreground">Manage your configured service instances</p>
        </div>
        <div className="flex space-x-2">
          <Button asChild variant="outline">
            <Link to="/services">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Service Catalog
            </Link>
          </Button>
          <Button onClick={loadData} variant="outline">
            Refresh
          </Button>
          <AddServiceInstanceDialog 
            onAddService={addServiceInstance}
            triggerButton={
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Instance
              </Button>
            }
          />
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Search service instances..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {loading && (
        <div className="text-center py-12">
          <Loader2 className="h-8 w-8 text-muted-foreground mx-auto mb-4 animate-spin" />
          <h3 className="text-lg font-medium text-muted-foreground mb-2">Loading service instances...</h3>
        </div>
      )}

      {error && !loading && (
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-red-600 mb-2">Error loading service instances</h3>
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <Button onClick={loadData} variant="outline">
            Try Again
          </Button>
        </div>
      )}

      {!loading && !error && (
        <>
          {instanceCategories.map((category) => (
            <div key={category} className="space-y-4">
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-semibold">{category}</h2>
                <Badge className={`${getCategoryColor(category)} text-xs`}>
                  {groupedInstances[category].length}
                </Badge>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {groupedInstances[category].map((instance) => (
                  <Card key={instance.id} className="rounded-xl hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3 min-w-0 flex-1">
                          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                            <ServiceIcon 
                              iconName={instance.catalog_definition?.ui_metadata?.icon}
                              category={instance.category}
                              type={instance.type}
                              className="h-4 w-4 text-muted-foreground" 
                            />
                          </div>
                          <div className="min-w-0 flex-1">
                            <CardTitle className="text-base truncate">{instance.name}</CardTitle>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge className={`${getTypeColor(instance.type)} text-xs`}>
                                {instance.type}
                              </Badge>
                              {instance.version && (
                                <Badge variant="outline" className="text-xs">
                                  v{instance.version}
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <ConfigureServiceInstanceDialog
                              instance={instance}
                              onUpdateService={updateServiceInstance}
                              triggerButton={
                                <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                                  <Settings2 className="h-4 w-4 mr-2" />
                                  Configure
                                </DropdownMenuItem>
                              }
                            />
                            <DropdownMenuItem 
                              onClick={() => testConnection(instance.id)}
                              disabled={testingConnections.has(instance.id)}
                            >
                              <TestTube className="h-4 w-4 mr-2" />
                              Test Connection
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <DropdownMenuItem 
                                  onSelect={(e) => e.preventDefault()} 
                                  className="text-red-600 focus:text-red-600"
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete Service Instance</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    Are you sure you want to delete "{instance.name}"? This action cannot be undone.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => deleteServiceInstance(instance.id)}
                                    className="bg-red-600 hover:bg-red-700"
                                  >
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <CardDescription className="text-sm mb-3 line-clamp-2">
                        {instance.description || 'No description provided'}
                      </CardDescription>
                      
                      {/* Connection Status */}
                      <div className="flex items-center justify-between mb-3 p-2 rounded-md bg-muted/30">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(instance.connection_status?.status)}
                          <Badge className={`${getStatusColor(instance.connection_status?.status)} text-xs`}>
                            {instance.connection_status?.status || 'unknown'}
                          </Badge>
                        </div>
                        {testingConnections.has(instance.id) && (
                          <Loader2 className="h-3 w-3 animate-spin text-blue-600" />
                        )}
                      </div>

                      {/* Connection Details */}
                      <div className="text-xs text-muted-foreground space-y-1">
                        <div className="flex items-center justify-between">
                          <span>Last tested:</span>
                          <span>{formatLastTested(instance.connection_status?.last_tested)}</span>
                        </div>
                        {instance.connection_status?.test_duration_ms && (
                          <div className="flex items-center justify-between">
                            <span>Duration:</span>
                            <span>{instance.connection_status.test_duration_ms}ms</span>
                          </div>
                        )}
                        {instance.connection_status?.error_message && (
                          <div className="text-red-600 text-xs mt-1 p-1 rounded bg-red-50">
                            {instance.connection_status.error_message}
                          </div>
                        )}
                      </div>

                      {/* Tags */}
                      {instance.tags && instance.tags.length > 0 && (
                        <div className="flex gap-1 mt-3 pt-3 border-t overflow-hidden">
                          {instance.tags.slice(0, 3).map((tag, index) => (
                            <Badge key={index} variant="secondary" className="text-xs whitespace-nowrap">
                              {tag}
                            </Badge>
                          ))}
                          {instance.tags.length > 3 && (
                            <Badge variant="secondary" className="text-xs">
                              +{instance.tags.length - 3}
                            </Badge>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}

          {filteredInstances.length === 0 && !loading && (
            <div className="text-center py-12">
              <Server className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-muted-foreground mb-2">
                {instances.length === 0 ? "No service instances" : "No matching instances"}
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                {instances.length === 0 
                  ? "Create your first service instance to get started"
                  : "Try adjusting your search terms"
                }
              </p>
              {instances.length === 0 && (
                <AddServiceInstanceDialog 
                  onAddService={addServiceInstance}
                  triggerButton={
                    <Button>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Your First Instance
                    </Button>
                  }
                />
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ServiceInstances;