
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { 
  Server, 
  TestTube, 
  AlertTriangle,
  CheckCircle,
  Search
} from "lucide-react";
import { AddServiceDialog } from "@/components/service/AddServiceDialog";
import { ConfigureServiceDialog } from "@/components/service/ConfigureServiceDialog";

interface ServiceStatus {
  id: string;
  name: string;
  type: string;
  status: 'connected' | 'error' | 'testing';
  lastTested: string;
  error?: string;
  description: string;
}

const mockServices: ServiceStatus[] = [
  // Database Services
  {
    id: "1",
    name: "Azure Cosmos DB",
    type: "Database",
    status: "connected",
    lastTested: "2 minutes ago",
    description: "Document database for storing processed content and metadata"
  },
  {
    id: "2",
    name: "Azure SQL Database",
    type: "Database",
    status: "connected",
    lastTested: "8 minutes ago",
    description: "Relational database for structured data storage"
  },
  {
    id: "3",
    name: "Azure AI Search",
    type: "Search Engine",
    status: "connected", 
    lastTested: "5 minutes ago",
    description: "Cognitive search service for document indexing and full-text search"
  },
  {
    id: "4",
    name: "Elasticsearch",
    type: "Search Engine",
    status: "connected",
    lastTested: "12 minutes ago",
    description: "Distributed search and analytics engine"
  },
  {
    id: "5",
    name: "Azure OpenAI",
    type: "AI Platform",
    status: "connected",
    lastTested: "3 minutes ago",
    description: "GPT models and language services for text generation and analysis"
  },
  {
    id: "6",
    name: "Azure AI Foundry",
    type: "AI Platform",
    status: "error",
    lastTested: "1 hour ago",
    error: "Authentication failed",
    description: "Comprehensive AI development platform for building and deploying AI solutions"
  },
  {
    id: "7",
    name: "Azure AI Content Understanding",
    type: "AI Platform",
    status: "connected",
    lastTested: "7 minutes ago",
    description: "Advanced content analysis and understanding capabilities"
  },
  {
    id: "8",
    name: "Azure AI Document Intelligence",
    type: "AI Platform",
    status: "connected",
    lastTested: "4 minutes ago",
    description: "Extract text, key-value pairs, and tables from documents"
  },
  {
    id: "9",
    name: "Azure AI Language",
    type: "AI Platform",
    status: "connected",
    lastTested: "6 minutes ago",
    description: "Natural language processing for sentiment, entities, and key phrases"
  },
  {
    id: "10",
    name: "Azure AI Vision",
    type: "AI Platform",
    status: "connected",
    lastTested: "9 minutes ago",
    description: "Computer vision capabilities for image and video analysis"
  },
  {
    id: "11",
    name: "Azure Speech Services",
    type: "AI Platform",
    status: "connected",
    lastTested: "11 minutes ago",
    description: "Speech-to-text, text-to-speech, and speech translation services"
  },
  {
    id: "12",
    name: "OpenAI API",
    type: "AI Platform",
    status: "connected",
    lastTested: "3 minutes ago",
    description: "Large language models for text generation and analysis"
  },
  {
    id: "13",
    name: "Anthropic Claude",
    type: "AI Platform",
    status: "connected",
    lastTested: "15 minutes ago",
    description: "Advanced AI assistant for complex reasoning and analysis"
  },
  {
    id: "14",
    name: "Google Vertex AI",
    type: "AI Platform",
    status: "error",
    lastTested: "2 hours ago",
    error: "Service quota exceeded",
    description: "Google's unified AI platform for machine learning workflows"
  },
  {
    id: "15",
    name: "Azure Blob Storage",
    type: "Storage",
    status: "connected",
    lastTested: "10 minutes ago",
    description: "Cloud storage for document files and assets"
  },
  {
    id: "16",
    name: "Azure Data Lake Storage",
    type: "Storage",
    status: "connected",
    lastTested: "13 minutes ago",
    description: "Scalable data lake storage for big data analytics"
  },
  {
    id: "17",
    name: "Amazon S3",
    type: "Storage",
    status: "connected",
    lastTested: "8 minutes ago",
    description: "Object storage service for backup and archiving"
  },
  {
    id: "18",
    name: "Azure Logic Apps",
    type: "Integration",
    status: "connected",
    lastTested: "14 minutes ago",
    description: "Workflow automation and integration platform"
  },
  {
    id: "19",
    name: "Azure Service Bus",
    type: "Integration",
    status: "connected",
    lastTested: "5 minutes ago",
    description: "Reliable cloud messaging service for enterprise integration"
  },
  {
    id: "20",
    name: "Microsoft Graph API",
    type: "Integration",
    status: "connected",
    lastTested: "7 minutes ago",
    description: "Access Microsoft 365 data and services"
  },
  {
    id: "21",
    name: "Azure Synapse Analytics",
    type: "Analytics",
    status: "connected",
    lastTested: "16 minutes ago",
    description: "Analytics service for big data and data warehousing"
  },
  {
    id: "22",
    name: "Power BI",
    type: "Analytics",
    status: "connected",
    lastTested: "12 minutes ago",
    description: "Business analytics and data visualization platform"
  },
  {
    id: "23",
    name: "Azure Application Insights",
    type: "Monitoring",
    status: "connected",
    lastTested: "6 minutes ago",
    description: "Application performance monitoring and analytics"
  },
  {
    id: "24",
    name: "Azure Monitor",
    type: "Monitoring",
    status: "connected",
    lastTested: "9 minutes ago",
    description: "Full-stack monitoring service for applications and infrastructure"
  }
];

const Services = () => {
  const [services, setServices] = useState<ServiceStatus[]>(mockServices);
  const [searchTerm, setSearchTerm] = useState("");

  const testConnection = async (serviceId: string) => {
    setServices(prev => prev.map(service => 
      service.id === serviceId 
        ? { ...service, status: 'testing' as const }
        : service
    ));

    // Simulate API call
    setTimeout(() => {
      setServices(prev => prev.map(service => 
        service.id === serviceId 
          ? { 
              ...service, 
              status: Math.random() > 0.3 ? 'connected' as const : 'error' as const,
              lastTested: "Just now",
              error: Math.random() > 0.3 ? undefined : "Connection timeout"
            }
          : service
      ));
    }, 2000);
  };

  const addService = (serviceData: any) => {
    const newService: ServiceStatus = {
      id: (services.length + 1).toString(),
      name: serviceData.name,
      type: serviceData.type,
      status: 'connected',
      lastTested: 'Just now',
      description: serviceData.description
    };
    setServices(prev => [...prev, newService]);
  };

  const updateService = (serviceId: string, config: any) => {
    console.log(`Updating service ${serviceId} with config:`, config);
    // Here you would typically save the configuration
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="h-3 w-3 text-green-600" />;
      case 'error': return <AlertTriangle className="h-3 w-3 text-red-600" />;
      case 'testing': return <TestTube className="h-3 w-3 text-blue-600 animate-pulse" />;
      default: return null;
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

  const filteredServices = services.filter(service =>
    service.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    service.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    service.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group services by type
  const groupedServices = filteredServices.reduce((acc, service) => {
    if (!acc[service.type]) {
      acc[service.type] = [];
    }
    acc[service.type].push(service);
    return acc;
  }, {} as Record<string, ServiceStatus[]>);

  const serviceTypes = Object.keys(groupedServices).sort();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Services</h1>
          <p className="text-muted-foreground">Manage global services available to all pipelines</p>
        </div>
        <AddServiceDialog onAddService={addService} />
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Search services..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {serviceTypes.map((type) => (
        <div key={type} className="space-y-4">
          <div className="flex items-center space-x-2">
            <h2 className="text-xl font-semibold">{type}</h2>
            <Badge className={`${getTypeColor(type)} text-xs`}>
              {groupedServices[type].length}
            </Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {groupedServices[type].map((service) => (
              <Card key={service.id} className="rounded-xl hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                        <Server className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <CardTitle className="text-base truncate">{service.name}</CardTitle>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge className={`${getStatusColor(service.status)} text-xs`}>
                            {getStatusIcon(service.status)}
                            <span className="ml-1">{service.status}</span>
                          </Badge>
                          <Badge className={`${getTypeColor(service.type)} text-xs`}>
                            {service.type}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <CardDescription className="text-sm mb-3 line-clamp-2">
                    {service.description}
                  </CardDescription>
                  <div className="flex items-center justify-between">
                    <div className="text-xs text-muted-foreground">
                      Last tested: {service.lastTested}
                      {service.error && (
                        <p className="text-red-600 mt-1 text-xs">{service.error}</p>
                      )}
                    </div>
                    <div className="flex space-x-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => testConnection(service.id)}
                        disabled={service.status === 'testing'}
                        className="text-xs h-8 px-3"
                      >
                        <TestTube className="h-3 w-3 mr-1" />
                        Test
                      </Button>
                      <ConfigureServiceDialog 
                        service={service} 
                        onUpdateService={updateService}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ))}

      {filteredServices.length === 0 && (
        <div className="text-center py-12">
          <Server className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-muted-foreground mb-2">No services found</h3>
          <p className="text-sm text-muted-foreground">Try adjusting your search terms</p>
        </div>
      )}
    </div>
  );
};

export default Services;