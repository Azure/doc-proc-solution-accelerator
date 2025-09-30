
import { useState, useMemo, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Search, RefreshCw, Settings, Activity } from "lucide-react";
import { stepsApi, StepCatalogDefinition } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import StepCatalogCard from "@/components/step/StepCatalogCard";
import CreateStepInstanceDialog from "@/components/step/CreateStepInstanceDialog";
import { Link } from "react-router-dom";

const Steps = () => {
  const [steps, setSteps] = useState<StepCatalogDefinition[]>([]);
  const [selectedStep, setSelectedStep] = useState<StepCatalogDefinition | undefined>();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Load steps from API
  const loadSteps = async () => {
    setLoading(true);
    try {
      // Try to load steps, initialize catalog if empty
      let stepCatalog = await stepsApi.getCatalog();
      
      if (stepCatalog.length === 0) {
        toast({
          title: "Initializing step catalog...",
          description: "Loading steps from catalog definition.",
        });
        
        await stepsApi.initializeCatalog();
        stepCatalog = await stepsApi.getCatalog();
      }
      
      setSteps(stepCatalog);
    } catch (error) {
      console.error('Error loading steps:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      toast({
        title: "Failed to load steps",
        description: errorMessage + '. Ensure the API backend is running and connected to CosmosDB.',
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSteps();
  }, []);

  const filteredAndGroupedSteps = useMemo(() => {
    const filtered = steps.filter(step => 
      step.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      step.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (step.category && step.category.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const grouped = filtered.reduce((acc, step) => {
      const category = step.category || 'other';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(step);
      return acc;
    }, {} as Record<string, StepCatalogDefinition[]>);

    return grouped;
  }, [steps, searchQuery]);

  const getTypeDisplayName = (type: string) => {
    switch (type) {
      case 'connector': return 'Data Connectors';
      case 'extractor': return 'Text Extractors';
      case 'image-extractor': return 'Image Processing';
      case 'ai-prompt': return 'AI Processing';
      case 'output': return 'Output Connectors';
      default: return type.charAt(0).toUpperCase() + type.slice(1);
    }
  };

  const handleCreateStepInstance = (step: StepCatalogDefinition) => {
    setSelectedStep(step);
    setIsDialogOpen(true);
  };

  const handleStepInstanceCreated = () => {
    toast({
      title: "Step Instance Created",
      description: "Step instance has been created successfully.",
    });
    setIsDialogOpen(false);
    setSelectedStep(undefined);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Step Catalog</h1>
          <p className="text-muted-foreground">Browse available step definitions and create instances</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to="/step-instances">
              <Settings className="h-4 w-4 mr-2" />
              Manage Instances
            </Link>
          </Button>
          <Button variant="outline" onClick={loadSteps} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search steps..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {loading && (
        <div className="text-center py-12">
           <div className="text-center">
              <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p className="text-center text-muted-foreground">Loading steps...</p>
            </div>
        </div>
      )}

      {!loading && (
        <div className="space-y-8">
          {Object.entries(filteredAndGroupedSteps).map(([category, categorySteps]) => (
            <div key={category} className="space-y-4">
              <h2 className="text-xl font-semibold text-foreground">
                {getTypeDisplayName(category)} ({categorySteps.length})
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categorySteps.map((step) => (
                  <StepCatalogCard
                    key={step.id}
                    step={step}
                    onCreateInstance={() => handleCreateStepInstance(step)}
                  />
                ))}
              </div>
            </div>
          ))}
          
          {Object.keys(filteredAndGroupedSteps).length === 0 && !loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No steps found matching your search.</p>
            </div>
          )}
        </div>
      )}

      {selectedStep && (
        <CreateStepInstanceDialog
          isOpen={isDialogOpen}
          onClose={() => {
            setIsDialogOpen(false);
            setSelectedStep(undefined);
          }}
          stepCatalogDefinition={selectedStep}
          onStepInstanceCreated={handleStepInstanceCreated}
        />
      )}
    </div>
  );
};

export default Steps;