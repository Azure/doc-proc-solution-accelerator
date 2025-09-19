
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
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
import { useToast } from "@/hooks/use-toast";
import { 
  Workflow, 
  Settings, 
  BarChart3, 
  Plus, 
  Play, 
  Pause, 
  CheckCircle,
  XCircle,
  ArrowLeft,
  Settings2,
  FileText,
  Upload,
  Download,
  Wrench,
  Save,
  Loader2,
  Activity,
  GitBranch,
  Clock,
  Files,
  Calendar,
  Trash2
} from "lucide-react";
import PipelineWorkflow from "../components/pipeline/PipelineWorkflow";
import PipelineMetrics from "../components/pipeline/PipelineMetrics";
import PipelineSettings from "../components/pipeline/PipelineSettings";
import NewPipelineDialog from "../components/pipeline/NewPipelineDialog";
import { useConfigLoader } from "../hooks/useConfigLoader";
import { pipelinesApi, Pipeline as PipelineModel, CreatePipelineRequest, ApiError, ErrorWithData } from "../lib/api";

// Extended interface for UI display purposes
interface PipelineDisplayInfo extends PipelineModel {
  status: 'active' | 'inactive' | 'running' | 'failed';
  lastRun?: string;
  documentsProcessed?: number;
}

const Pipeline = () => {
  const [activeTab, setActiveTab] = useState("builder");
  const [selectedPipeline, setSelectedPipeline] = useState<PipelineDisplayInfo | null>(null);
  const [pipelines, setPipelines] = useState<PipelineDisplayInfo[]>([]);
  const [pipelineLoading, setPipelineLoading] = useState(true);
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [isNewPipelineOpen, setIsNewPipelineOpen] = useState(false);
  const [yamlInput, setYamlInput] = useState('');
  const [configView, setConfigView] = useState<'builder' | 'yaml'>('builder');
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  // Configuration loader hook for YAML/config management
  const {
    stepCatalog,
    services,
    pipelines: configPipelines,
    loading,
    error,
    loadStepCatalog,
    loadPipelineConfig,
    exportConfig
  } = useConfigLoader();

  // Load pipelines from API
  useEffect(() => {
    loadPipelines();
  }, []);

  const loadPipelines = async () => {
    try {
      setPipelineLoading(true);
      setPipelineError(null);
      const apiPipelines = await pipelinesApi.getPipelines();
      
      // Transform API pipelines to display format
      const transformedPipelines: PipelineDisplayInfo[] = apiPipelines.map(pipeline => ({
        ...pipeline,
        status: pipeline.settings?.enabled ? 'active' : 'inactive' as 'active' | 'inactive' | 'running' | 'failed',
        lastRun: 'Never', // This would come from execution service
        documentsProcessed: 0 // This would come from execution service
      }));
      
      setPipelines(transformedPipelines);
    } catch (err) {
      const error = err as ApiError;
      setPipelineError(error.message || 'Failed to load pipelines');
      console.error('Error loading pipelines:', err);
    } finally {
      setPipelineLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return CheckCircle;
      case 'running': return Play;
      case 'failed': return XCircle;
      default: return Pause;
    }
  };

  const handleCreatePipeline = async (pipelineData: { name: string; description: string }) => {
    const createRequest: CreatePipelineRequest = {
      name: pipelineData.name,
      description: pipelineData.description,
      steps: [],
      execution_sequence: [],
    };

    try {
      const newPipeline = await pipelinesApi.createPipeline(createRequest);
      
      // Transform to display format
      const displayPipeline: PipelineDisplayInfo = {
        ...newPipeline,
        status: newPipeline.settings?.enabled ? 'active' : 'inactive',
        lastRun: 'Never',
        documentsProcessed: 0
      };

      setPipelines(prev => [...prev, displayPipeline]);
      setIsNewPipelineOpen(false);
    } catch (error) {
      console.error('Error creating pipeline:', error);
      const errorMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error occurred';
      
      // Show error toast
      toast({
        title: "Failed to create pipeline",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleDeletePipeline = async (pipelineId: string) => {
    try {
      await pipelinesApi.deletePipeline(pipelineId);
      setPipelines(prev => prev.filter(p => p.id !== pipelineId));
      
      // Show success toast
      toast({
        title: "Pipeline deleted successfully",
        description: `${selectedPipeline?.name || 'Pipeline'} has been deleted.`,
        variant: "default",
      });
      
      // If the deleted pipeline was selected, clear the selection
      if (selectedPipeline && selectedPipeline.id === pipelineId) {
        setSelectedPipeline(null);
      }
    } catch (error) {
      console.error('Error deleting pipeline:', error);
      const errorMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error occurred';
      
      // Show error toast
      toast({
        title: "Failed to delete pipeline",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handlePipelineStepsChange = (steps: string[], executionSequence: string[]) => {
    if (selectedPipeline) {
      const updatedPipeline = {
        ...selectedPipeline,
        steps,
        execution_sequence: executionSequence
      };
      setSelectedPipeline(updatedPipeline);
      
      // Optionally auto-save or mark as changed
      // You can add a save button or auto-save logic here
    }
  };

  const handleUpdatePipeline = async (pipeline: PipelineDisplayInfo) => {
    try {
      setIsSaving(true);
      const updatedPipeline = await pipelinesApi.updatePipeline(pipeline.id, pipeline);
      
      // Update the pipeline in the list
      setPipelines(prev => prev.map(p => 
        p.id === pipeline.id 
          ? { ...updatedPipeline, status: pipeline.status, lastRun: pipeline.lastRun, documentsProcessed: pipeline.documentsProcessed }
          : p
      ));

      // Update selected pipeline if it's the one that was updated
      if (selectedPipeline && selectedPipeline.id === pipeline.id) {
        setSelectedPipeline({
          ...updatedPipeline,
          status: pipeline.status,
          lastRun: pipeline.lastRun,
          documentsProcessed: pipeline.documentsProcessed
        });
      }

      // Show success toast
      toast({
        title: "Pipeline saved successfully",
        description: `${pipeline.name} has been updated.`,
        variant: "default",
      });

    } catch (err) {
      const error = err as ApiError;
      console.error('Error updating pipeline:', err);
      
      // Show error toast
      toast({
        title: "Failed to save pipeline",
        description: error.message || "An unexpected error occurred while saving the pipeline.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handlePipelineUpdated = (updatedPipeline: PipelineModel) => {
    // Convert Pipeline to PipelineDisplayInfo
    const displayPipeline: PipelineDisplayInfo = {
      ...updatedPipeline,
      status: updatedPipeline.settings?.enabled ? 'active' : 'inactive' as 'active' | 'inactive' | 'running' | 'failed',
      lastRun: selectedPipeline?.lastRun || 'Never',
      documentsProcessed: selectedPipeline?.documentsProcessed || 0
    };

    // Update the pipeline in the list
    setPipelines(prev => prev.map(p => 
      p.id === updatedPipeline.id ? displayPipeline : p
    ));

    // Update selected pipeline if it's the one that was updated
    if (selectedPipeline && selectedPipeline.id === updatedPipeline.id) {
      setSelectedPipeline(displayPipeline);
    }
  };

  // Sample YAML configurations for demo
  const sampleStepCatalog = `# step_catalog.yaml
step_catalog:
  - id: pdf_to_png
    name: "PDF to PNG Converter"
    description: "Convert PDF pages to PNG images"
    type: script
    module_name: pdf_to_png
    module_path: ./doc/proc/step/extract_pdf_to_png.py
    class_name: PDFPagesToPNGStep
    tags: [pdf, png, conversion]
    category: "Document Processing"
    version: "2.1"
    default_settings:
      fail_pipeline_on_error: true
      retry_on_failure: false
      retries: 3
      timeout: 600
    ui_metadata:
      icon: "image"
      color: "#10B981"
      description_long: "Converts PDF document pages into PNG image files with configurable DPI and output formats."
    config_schema:
      properties:
        png_output_folder:
          type: string
          title: "PNG Output Folder"
          description: "Directory path where PNG files will be saved"
          default: "./output/png"
          required: true
        num_pages:
          type: integer
          title: "Number of Pages"
          description: "Maximum number of pages to convert (0 = all pages)"
          default: 10
          minimum: 0
          maximum: 1000
        dpi:
          type: integer
          title: "DPI Resolution"
          description: "Resolution for PNG output in dots per inch"
          default: 300
          minimum: 72
          maximum: 600`;

  const samplePipelineConfig = `# pipeline_config.yaml
services:
  - name: azure_storage_01
    type: azure_blob
    test_connection: true
    settings:
      account_name: \${AZURE_STORAGE_SERVICE_ACCOUNT_NAME}
      credential_type: \${AZURE_STORAGE_SERVICE_CREDENTIAL_TYPE}
      credential_key: \${AZURE_STORAGE_SERVICE_ACCOUNT_KEY}

pipelines:
  - name: pipeline_1
    description: 'Document processing pipeline'
    updated_at: '2024-01-01T12:00:00Z'
    version: '1.0'
    steps:
      - name: pdf_converter_1
        step_catalog_id: pdf_to_png
        enabled: true
        settings:
          png_output_folder: "./output/png"
          num_pages: 5
          dpi: 300
    execution_sequence: [pdf_converter_1]
    settings:
      enabled: true
      retries: 2
      retry_delay: 60
      timeout: 300
      max_concurrent_runs: 5
      logging:
        enabled: true
        level: INFO
        format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        handlers:
          - type: console
            level: INFO`;

  const loadSampleData = async (type: 'catalog' | 'pipeline') => {
    try {
      if (type === 'catalog') {
        await loadStepCatalog(sampleStepCatalog);
        setYamlInput(sampleStepCatalog);
      } else {
        await loadPipelineConfig(samplePipelineConfig);
        setYamlInput(samplePipelineConfig);
      }
    } catch (err) {
      console.error('Failed to load sample data:', err);
    }
  };

  const handleLoadYaml = async () => {
    if (!yamlInput.trim()) return;
    
    try {
      // Determine if it's a step catalog or pipeline config based on content
      if (yamlInput.includes('step_catalog:')) {
        await loadStepCatalog(yamlInput);
      } else {
        await loadPipelineConfig(yamlInput);
      }
    } catch (err) {
      console.error('Failed to load YAML:', err);
    }
  };

  const handleExportConfig = () => {
    const { yaml, json } = exportConfig();
    console.log('Exported YAML:', yaml);
    console.log('Exported JSON:', json);
    
    // Download YAML file
    const blob = new Blob([yaml], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'exported_pipeline_config.yaml';
    link.click();
  };

  if (selectedPipeline) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button 
              variant="ghost" 
              onClick={() => setSelectedPipeline(null)}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Pipelines</span>
            </Button>
            <div>
              <h1 className="text-3xl font-bold">{selectedPipeline.name}</h1>
              <p className="text-muted-foreground">{selectedPipeline.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button 
                  variant="outline"
                  size="sm"
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Pipeline</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to delete "{selectedPipeline.name}"? This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => selectedPipeline && handleDeletePipeline(selectedPipeline.id)}
                    className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            
            <TabsTrigger value="builder" className="flex items-center gap-2">
              <Workflow className="h-4 w-4" />
              Workflow Builder
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings2 className="h-4 w-4" />
              Settings
            </TabsTrigger>
            <TabsTrigger value="metrics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Metrics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="builder" className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium">Pipeline Builder</h3>
                <p className="text-sm text-muted-foreground">
                  Visual pipeline editor for configuring step sequences and settings
                </p>
              </div>
              <div className="flex gap-2">
                <Button 
                  onClick={() => selectedPipeline && handleUpdatePipeline(selectedPipeline)}
                  variant="outline"
                  size="sm"
                  disabled={isSaving}
                >
                  {isSaving ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  {isSaving ? 'Saving...' : 'Save Pipeline'}
                </Button>
                <Button 
                  variant={configView === 'builder' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setConfigView('builder')}
                >
                  Visual Builder
                </Button>
                <Button 
                  variant={configView === 'yaml' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setConfigView('yaml')}
                >
                  YAML Config
                </Button>
              </div>
            </div>

            {configView === 'builder' ? (
              <PipelineWorkflow 
                pipelineId={selectedPipeline.id}
                steps={selectedPipeline.steps}
                executionSequence={selectedPipeline.execution_sequence}
                onStepsChange={handlePipelineStepsChange}
              />
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Load Configuration</CardTitle>
                    <CardDescription>
                      Load step catalog or pipeline configuration from YAML
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Textarea
                      placeholder="Paste your YAML configuration here..."
                      value={yamlInput}
                      onChange={(e) => setYamlInput(e.target.value)}
                      rows={12}
                      className="font-mono text-sm"
                    />
                    <div className="flex gap-2">
                      <Button onClick={handleLoadYaml} disabled={!yamlInput.trim()}>
                        <Upload className="h-4 w-4 mr-2" />
                        Load YAML
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => loadSampleData('catalog')}
                      >
                        Load Sample Catalog
                      </Button>
                      <Button 
                        variant="outline" 
                        onClick={() => loadSampleData('pipeline')}
                      >
                        Load Sample Pipeline
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Export Configuration</CardTitle>
                    <CardDescription>
                      Export your current configuration as YAML or JSON
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="text-sm text-muted-foreground">
                      <p>Current configuration includes:</p>
                      <ul className="list-disc list-inside mt-2">
                        <li>{stepCatalog.length} step definitions</li>
                        <li>{services.length} service configurations</li>
                        <li>{configPipelines.length} pipeline configurations</li>
                      </ul>
                    </div>
                    <Button onClick={handleExportConfig}>
                      <Download className="h-4 w-4 mr-2" />
                      Export as YAML
                    </Button>
                  </CardContent>
                </Card>

                {loading && (
                  <Card>
                    <CardContent className="text-center p-8">
                      Loading configuration...
                    </CardContent>
                  </Card>
                )}

                {error && (
                  <Card className="border-red-200">
                    <CardContent className="text-red-600 p-4">
                      Error: {error}
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <PipelineSettings 
              pipeline={selectedPipeline}
              onPipelineUpdated={handlePipelineUpdated}
            />
          </TabsContent>

          <TabsContent value="metrics" className="space-y-4">
            <PipelineMetrics />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Document Processing Pipelines</h1>
          <p className="text-muted-foreground">Manage and monitor your document processing workflows</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setIsNewPipelineOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Pipeline
          </Button>
        </div>
      </div>

      {pipelineLoading && (
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <Activity className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p className="text-center text-muted-foreground">Loading pipelines...</p>
            </div>
          </CardContent>
        </Card>
      )}

      {pipelineError && (
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-red-600">Error: {pipelineError}</p>
            <div className="text-center mt-4">
              <Button onClick={loadPipelines} variant="outline">
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {!pipelineLoading && !pipelineError && (
        <div className="grid gap-4">
          {pipelines.length === 0 ? (
            <Card>
              <CardContent className="py-8">
                <p className="text-center text-muted-foreground">
                  No pipelines found. Create your first pipeline to get started.
                </p>
              </CardContent>
            </Card>
          ) : (
            pipelines.map((pipeline) => {
              const StatusIcon = getStatusIcon(pipeline.status);
              
              return (
                <Card 
                  key={pipeline.id} 
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => setSelectedPipeline(pipeline)}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                          <Workflow className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{pipeline.name}</CardTitle>
                      <CardDescription>{pipeline.description}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(pipeline.status)}>
                      <StatusIcon className="h-3 w-3 mr-1" />
                      {pipeline.status}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                      <GitBranch className="h-4 w-4" />
                      <span>Steps</span>
                    </div>
                    <p className="font-semibold text-base">{pipeline.steps?.length || 0}</p>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                      <Clock className="h-4 w-4" />
                      <span>Last Run</span>
                    </div>
                    <p className="font-semibold text-base">{pipeline.lastRun}</p>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                      <Files className="h-4 w-4" />
                      <span>Documents</span>
                    </div>
                    <p className="font-semibold text-base">{pipeline.documentsProcessed?.toLocaleString() || 0}</p>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 text-muted-foreground mb-1">
                      <Calendar className="h-4 w-4" />
                      <span>Created</span>
                    </div>
                    <p className="font-semibold text-base">
                      {pipeline.created_at 
                        ? new Date(pipeline.created_at).toLocaleDateString()
                        : 'Unknown'
                      }
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
              );
            })
          )}
        </div>
      )}

      <NewPipelineDialog
        isOpen={isNewPipelineOpen}
        onClose={() => setIsNewPipelineOpen(false)}
        onSave={handleCreatePipeline}
      />
    </div>
  );
};

export default Pipeline;