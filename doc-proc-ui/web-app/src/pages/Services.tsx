
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
  ArrowRight,
  Database,
  Activity
} from "lucide-react";
import { AddServiceInstanceDialog } from "@/components/service/AddServiceInstanceDialog";
import { servicesApi, ServiceCatalogDefinition } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { ServiceIcon } from "@/components/service/ServiceIcon";

const Services = () => {
  const [services, setServices] = useState<ServiceCatalogDefinition[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  // Load services from API
  useEffect(() => {
    loadServices();
  }, []);

  const loadServices = async () => {
    try {
      setLoading(true);
      setError(null);
      const catalogServices = await servicesApi.getCatalog();
      setServices(catalogServices);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load services';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage + '. Ensure the Api backend is running and connected to CosmosDB.',
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (serviceId: string) => {
    // For catalog services, we can't test connections directly
    // This would typically create an instance first
    toast({
      title: "Test Connection",
      description: "Connection testing requires creating a service instance first",
      variant: "default",
    });
  };

  const addService = async (serviceData: any) => {
    try {
      const newService = await servicesApi.createInstance({
        name: serviceData.name,
        description: serviceData.description,
        service_catalog_id: serviceData.service_catalog_id,
        settings: serviceData.settings || {}
      });
      
      toast({
        title: "Service instance created",
        description: `${newService.name} instance has been created successfully`,
      });
      
      // Optionally redirect to service instances page or refresh
    } catch (error) {
      toast({
        title: "Failed to create service instance",
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: "destructive",
      });
    }
  };

  const updateService = async (serviceId: string, config: any) => {
    // For catalog services, we can't update them directly
    // They would be updated through the service catalog management
    toast({
      title: "Update Service",
      description: "Catalog services are managed through the service catalog",
      variant: "default",
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="h-3 w-3 text-green-600" />;
      case 'error': return <AlertTriangle className="h-3 w-3 text-red-600" />;
      case 'testing': return <TestTube className="h-3 w-3 text-blue-600 animate-pulse" />;
      default: return <AlertTriangle className="h-3 w-3 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
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

  const filteredServices = services.filter(service =>
    service.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    service.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    service.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (service.category && service.category.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Group services by category instead of type
  const groupedServices = filteredServices.reduce((acc, service) => {
    const category = service.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(service);
    return acc;
  }, {} as Record<string, ServiceCatalogDefinition[]>);

  const serviceCategories = Object.keys(groupedServices).sort();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Service Catalog</h1>
          <p className="text-muted-foreground">Browse available service types and create instances</p>
        </div>
        <div className="flex space-x-2">
          <Button asChild variant="outline">
            <Link to="/service-instances">
              <Database className="h-4 w-4 mr-2" />
              View Instances
              <ArrowRight className="h-4 w-4 ml-2" />
            </Link>
          </Button>
          <Button onClick={loadServices} variant="outline">
            Refresh Catalog
          </Button>
        </div>
      </div>

      {!loading && !error && filteredServices.length > 0 && (
        <div className="bg-muted/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium">Quick Stats</h3>
              <p className="text-xs text-muted-foreground">Service catalog overview</p>
            </div>
            <div className="flex items-center space-x-6 text-sm">
              <div className="text-center">
                <div className="font-bold text-lg">{services.length}</div>
                <div className="text-muted-foreground">Total Services</div>
              </div>
              <div className="text-center">
                <div className="font-bold text-lg">{serviceCategories.length}</div>
                <div className="text-muted-foreground">Categories</div>
              </div>
              
            </div>
          </div>
        </div>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Search service catalog..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {loading && (
        <div className="text-center py-12">
          <div className="text-center">
              <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p className="text-center text-muted-foreground">Loading  service catalog...</p>
            </div>
        </div>
      )}

      {error && !loading && (
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-red-600 mb-2">Error loading service catalog</h3>
          <p className="text-sm text-muted-foreground mb-4">{error}</p>
          <Button onClick={loadServices} variant="outline">
            Try Again
          </Button>
        </div>
      )}

      {!loading && !error && (
        <>
          {serviceCategories.map((category) => (
            <div key={category} className="space-y-4">
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-semibold">{category}</h2>
                <Badge className={`${getCategoryColor(category)} text-xs`}>
                  {groupedServices[category].length}
                </Badge>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {groupedServices[category].map((service) => (
                  <Card key={service.id} className="rounded-xl hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                            <ServiceIcon 
                              iconName={service.ui_metadata?.icon}
                              category={service.category}
                              type={service.type}
                              className="h-4 w-4 text-muted-foreground" 
                            />
                          </div>
                          <div className="min-w-0 flex-1">
                            <CardTitle className="text-base truncate">{service.name}</CardTitle>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge className={`${getTypeColor(service.type)} text-xs`}>
                                {service.type}
                              </Badge>
                              {service.version && (
                                <Badge variant="outline" className="text-xs">
                                  v{service.version}
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <CardDescription className="text-sm mb-3 line-clamp-2">
                        {service.description || 'No description provided'}
                      </CardDescription>
                      
                      {/* Service metadata */}
                      <div className="text-xs text-muted-foreground mb-3 space-y-1">
                        <div>Module: {service.module_name}</div>
                        <div>Class: {service.class_name}</div>
                        {service.tags && service.tags.length > 0 && (
                          <div className="flex gap-1 mt-2 pt-3 overflow-hidden">
                            {service.tags.slice(0, 5).map((tag, index) => (
                              <Badge key={index} variant="secondary" className="text-xs whitespace-nowrap">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      <div className="flex justify-end mt-auto pt-2">
                        <AddServiceInstanceDialog 
                          selectedService={service}
                          onAddService={addService}
                          triggerButton={
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-xs h-8 px-3"
                            >
                              Create Instance
                            </Button>
                          }
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}

          {filteredServices.length === 0 && !loading && (
            <div className="text-center py-12">
              <Server className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-muted-foreground mb-2">No services found in catalog</h3>
              <p className="text-sm text-muted-foreground">Try adjusting your search terms or refresh the catalog</p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Services;