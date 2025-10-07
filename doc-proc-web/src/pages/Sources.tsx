import { useState, useMemo, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, RefreshCw, Settings, Activity } from "lucide-react";
import { sourcesApi, SourceCatalogDefinition } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import SourceCatalogCard from "@/components/source/SourceCatalogCard";
import CreateSourceInstanceDialog from "@/components/source/CreateSourceInstanceDialog";
import { Link } from "react-router-dom";

const Sources = () => {
  const [sources, setSources] = useState<SourceCatalogDefinition[]>([]);
  const [selectedSource, setSelectedSource] = useState<SourceCatalogDefinition | undefined>();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Load sources from API
  const loadSources = async () => {
    setLoading(true);
    try {
      // Try to load sources, initialize catalog if empty
      let sourceCatalog = await sourcesApi.getCatalog();
      
      if (sourceCatalog.length === 0) {
        toast({
          title: "Initializing source catalog...",
          description: "Loading sources from catalog definition.",
        });
        
        await sourcesApi.initializeCatalog();
        sourceCatalog = await sourcesApi.getCatalog();
      }
      
      setSources(sourceCatalog);
    } catch (error) {
      console.error('Error loading sources:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast({
        title: "Failed to load sources",
        description: errorMessage + '. Ensure the API backend is running and connected to CosmosDB.',
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSources();
  }, []);

  const filteredAndGroupedSources = useMemo(() => {
    const filtered = sources.filter(source => 
      source.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      source.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (source.type && source.type.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const grouped = filtered.reduce((acc, source) => {
      const type = source.type || 'other';
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(source);
      return acc;
    }, {} as Record<string, SourceCatalogDefinition[]>);

    return grouped;
  }, [sources, searchQuery]);

  const getTypeDisplayName = (type: string) => {
    switch (type) {
      case 'database': return 'Databases';
      case 'cloud-storage': return 'Cloud Storage';
      case 'file-system': return 'File Systems';
      case 'web-crawler': return 'Web Crawlers';
      case 'api': return 'API Sources';
      case 'sharepoint': return 'SharePoint';
      case 'azure_blob': return 'Blob Storage';
      case 'azure_files': return 'File Storage';
      default: return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };

  const handleCreateSourceInstance = (source: SourceCatalogDefinition) => {
    setSelectedSource(source);
    setIsDialogOpen(true);
  };

  const handleSourceInstanceCreated = () => {
    toast({
      title: "Source Instance Created",
      description: "Source instance has been created successfully.",
    });
    setIsDialogOpen(false);
    setSelectedSource(undefined);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Source Catalog</h1>
          <p className="text-muted-foreground">Browse available source definitions and create instances</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/source-instances">
              <Settings className="h-4 w-4 mr-2" />
              Manage Instances
            </Link>
          </Button>
          <Button variant="outline" onClick={loadSources} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search sources..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {loading && (
        <div className="text-center py-12">
           <div className="text-center">
              <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p className="text-center text-muted-foreground">Loading sources...</p>
            </div>
        </div>
      )}

      {!loading && (
        <div className="space-y-8">
          {Object.entries(filteredAndGroupedSources).map(([type, typeSources]) => (
            <div key={type} className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground">
                {getTypeDisplayName(type)} ({typeSources.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {typeSources.map((source) => (
                  <SourceCatalogCard
                    key={source.id}
                    source={source}
                    onCreateInstance={() => handleCreateSourceInstance(source)}
                  />
                ))}
              </div>
            </div>
          ))}
          
          {Object.keys(filteredAndGroupedSources).length === 0 && !loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No sources found matching your search.</p>
            </div>
          )}
        </div>
      )}

      {selectedSource && (
        <CreateSourceInstanceDialog
          isOpen={isDialogOpen}
          onClose={() => {
            setIsDialogOpen(false);
            setSelectedSource(undefined);
          }}
          sourceCatalogDefinition={selectedSource}
          onSourceInstanceCreated={handleSourceInstanceCreated}
        />
      )}
    </div>
  );
};

export default Sources;