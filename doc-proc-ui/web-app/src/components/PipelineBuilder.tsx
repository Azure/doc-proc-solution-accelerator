// PipelineBuilder.tsx - Visual pipeline builder component

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { 
  Play, 
  Pause, 
  Trash2, 
  Edit, 
  ArrowDown, 
  ArrowUp, 
  Settings,
  Plus,
  Download,
  Upload
} from 'lucide-react';
import { useConfigLoader } from '../hooks/useConfigLoader';
import { StepInstance } from '../lib/configLoader';

interface PipelineBuilderProps {
  pipelineName?: string;
}

const PipelineBuilder: React.FC<PipelineBuilderProps> = ({ 
  pipelineName = 'pipeline_1' 
}) => {
  const {
    stepCatalog,
    pipelines,
    loading,
    error,
    loadStepCatalog,
    loadPipelineConfig,
    createStepInstance,
    validateStepInstance,
    addStepToPipeline,
    removeStepFromPipeline,
    updateStepInPipeline,
    reorderStepsInPipeline,
    exportConfig
  } = useConfigLoader();

  const [selectedStepForEdit, setSelectedStepForEdit] = useState<StepInstance | null>(null);
  const [showAddStep, setShowAddStep] = useState(false);

  const currentPipeline = pipelines.find(p => p.name === pipelineName);

  // Load initial configuration
  useEffect(() => {
    // In a real app, you'd load this from files or API
    const loadInitialConfig = async () => {
      // Mock step catalog YAML
      const mockStepCatalogYaml = `
step_catalog:
  - id: sample_step
    name: "Sample Development Step"
    description: "Sample step for development and testing"
    type: script
    module_name: sample
    module_path: ./doc/proc/step/sample.py
    class_name: SampleStep
    tags: [sample, development]
    category: "Development"
    version: "1.0"
    default_settings:
      fail_pipeline_on_error: true
      retry_on_failure: true
      retries: 3
      timeout: 600
    ui_metadata:
      icon: "gear"
      color: "#6B7280"
      description_long: "A sample step used for development and testing purposes."
    config_schema:
      properties:
        key1:
          type: string
          title: "Custom Key 1"
          description: "First custom configuration key"
          default: "value1"
        key2:
          type: string
          title: "Custom Key 2"
          description: "Second custom configuration key"
          default: "value2"
        debug_mode:
          type: boolean
          title: "Debug Mode"
          description: "Enable debug logging for this step"
          default: false
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
      description_long: "Converts PDF document pages into PNG image files."
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
          description: "Maximum number of pages to convert"
          default: 10
          minimum: 0
          maximum: 1000
      `;

      // Mock pipeline configuration YAML
      const mockPipelineConfigYaml = `
services:
  - name: azure_storage_01
    type: azure_blob
    test_connection: true
    settings:
      account_name: \${STORAGE_ACCOUNT_NAME}
      credential_type: \${STORAGE_ACCOUNT_CREDENTIAL_TYPE}
      credential_key: \${STORAGE_ACCOUNT_KEY}

pipelines:
  - name: pipeline_1
    description: 'Document processing pipeline for converting PDFs'
    updated_at: '2024-12-29T12:00:00Z'
    version: '1.0'
    steps:
      - name: sample_step_1
        step_catalog_id: sample_step
        enabled: true
        settings:
          fail_pipeline_on_error: true
          retry_on_failure: true
          retries: 3
          timeout: 600
          key1: "demo_value1"
          key2: "demo_value2"
          debug_mode: false
      - name: pdf_converter_1
        step_catalog_id: pdf_to_png
        enabled: true
        settings:
          fail_pipeline_on_error: true
          retry_on_failure: false
          retries: 3
          timeout: 600
          png_output_folder: "./output/png"
          num_pages: 10
    execution_sequence: [sample_step_1, pdf_converter_1]
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
            level: INFO
          - type: file
            level: ERROR
            filename: pipeline_errors.log
      `;

      try {
        await loadStepCatalog(mockStepCatalogYaml);
        await loadPipelineConfig(mockPipelineConfigYaml);
      } catch (err) {
        console.error('Failed to load configuration:', err);
      }
    };

    loadInitialConfig();
  }, [loadStepCatalog, loadPipelineConfig]);

  const handleAddStep = (stepId: string) => {
    const instanceName = `${stepId}_${Date.now()}`;
    const stepInstance = createStepInstance(stepId, instanceName);
    
    if (stepInstance) {
      addStepToPipeline(pipelineName, stepInstance);
      setShowAddStep(false);
    }
  };

  const handleEditStep = (step: StepInstance) => {
    setSelectedStepForEdit({ ...step });
  };

  const handleSaveStep = () => {
    if (selectedStepForEdit) {
      const validation = validateStepInstance(selectedStepForEdit);
      
      if (validation.valid) {
        updateStepInPipeline(pipelineName, selectedStepForEdit.name, selectedStepForEdit);
        setSelectedStepForEdit(null);
      } else {
        alert('Validation errors:\n' + validation.errors.join('\n'));
      }
    }
  };

  const handleDeleteStep = (stepName: string) => {
    if (confirm('Are you sure you want to delete this step?')) {
      removeStepFromPipeline(pipelineName, stepName);
    }
  };

  const handleMoveStep = (stepName: string, direction: 'up' | 'down') => {
    if (!currentPipeline) return;
    
    const currentIndex = currentPipeline.execution_sequence.indexOf(stepName);
    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    
    if (newIndex >= 0 && newIndex < currentPipeline.execution_sequence.length) {
      reorderStepsInPipeline(pipelineName, currentIndex, newIndex);
    }
  };

  const handleExport = () => {
    const { yaml, json } = exportConfig();
    
    // Create and download YAML file
    const yamlBlob = new Blob([yaml], { type: 'text/yaml' });
    const yamlUrl = URL.createObjectURL(yamlBlob);
    const yamlLink = document.createElement('a');
    yamlLink.href = yamlUrl;
    yamlLink.download = 'pipeline_config.yaml';
    yamlLink.click();
    
    // Also log JSON for debugging
    console.log('Exported JSON:', json);
  };

  if (loading) {
    return <div className="flex justify-center p-8">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">Error: {error}</div>;
  }

  if (!currentPipeline) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-2xl font-bold tracking-tight">Pipeline Builder</h3>
          <p className="text-muted-foreground">Pipeline not found: {pipelineName}</p>
        </div>
        
        {pipelines.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Available Pipelines</CardTitle>
              <CardDescription>Select a pipeline to edit</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {pipelines.map(pipeline => (
                  <div key={pipeline.name} className="p-3 border rounded">
                    <div className="font-medium">{pipeline.name}</div>
                    <div className="text-sm text-muted-foreground">{pipeline.description}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
        
        {pipelines.length === 0 && (
          <Card>
            <CardContent className="text-center p-8">
              <p className="text-muted-foreground">No pipelines loaded. Please wait for configuration to load...</p>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  const getStepFromCatalog = (stepId?: string) => {
    return stepCatalog.find(s => s.id === stepId);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-2xl font-bold tracking-tight">Pipeline Builder</h3>
          <p className="text-muted-foreground">{currentPipeline.description}</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowAddStep(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Add Step
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Pipeline Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline: {currentPipeline.name}</CardTitle>
          <CardDescription>
            Version {currentPipeline.version} • Last updated: {currentPipeline.updated_at}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch checked={currentPipeline.settings.enabled} />
              <Label>Enabled</Label>
            </div>
            <Separator orientation="vertical" className="h-6" />
            <div className="text-sm text-muted-foreground">
              Max Concurrent Runs: {currentPipeline.settings.max_concurrent_runs}
            </div>
            <div className="text-sm text-muted-foreground">
              Timeout: {currentPipeline.settings.timeout}s
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Steps List */}
      <div className="space-y-4">
        {currentPipeline.execution_sequence.map((stepName, index) => {
          const step = currentPipeline.steps.find(s => s.name === stepName);
          const catalogStep = getStepFromCatalog(step?.step_catalog_id);
          
          if (!step) return null;

          return (
            <Card key={stepName} className={`${!step.enabled ? 'opacity-50' : ''}`}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl font-bold text-muted-foreground">
                      {index + 1}
                    </div>
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {catalogStep?.name || step.name}
                        {!step.enabled && <Badge variant="secondary">Disabled</Badge>}
                      </CardTitle>
                      <CardDescription>
                        {catalogStep?.description || 'Custom step'}
                      </CardDescription>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleMoveStep(stepName, 'up')}
                      disabled={index === 0}
                    >
                      <ArrowUp className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleMoveStep(stepName, 'down')}
                      disabled={index === currentPipeline.execution_sequence.length - 1}
                    >
                      <ArrowDown className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditStep(step)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteStep(stepName)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <Label className="text-xs text-muted-foreground">Status</Label>
                    <div className="flex items-center gap-1">
                      {step.enabled ? (
                        <Play className="h-3 w-3 text-green-500" />
                      ) : (
                        <Pause className="h-3 w-3 text-muted-foreground" />
                      )}
                      {step.enabled ? 'Enabled' : 'Disabled'}
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-xs text-muted-foreground">Retries</Label>
                    <div>{step.settings.retries || 0}</div>
                  </div>
                  
                  <div>
                    <Label className="text-xs text-muted-foreground">Timeout</Label>
                    <div>{step.settings.timeout || 0}s</div>
                  </div>
                  
                  <div>
                    <Label className="text-xs text-muted-foreground">Tags</Label>
                    <div className="flex gap-1 flex-wrap">
                      {catalogStep?.tags.map(tag => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Add Step Modal */}
      {showAddStep && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">Add Step</h2>
            
            <div className="grid gap-4">
              {stepCatalog.map(step => (
                <Card key={step.id} className="cursor-pointer hover:shadow-md">
                  <CardHeader onClick={() => handleAddStep(step.id)}>
                    <CardTitle className="flex items-center justify-between">
                      {step.name}
                      <Badge>{step.category}</Badge>
                    </CardTitle>
                    <CardDescription>{step.description}</CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" onClick={() => setShowAddStep(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Step Modal */}
      {selectedStepForEdit && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">Edit Step</h2>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="step-name">Step Name</Label>
                <Input
                  id="step-name"
                  value={selectedStepForEdit.name}
                  onChange={(e) => setSelectedStepForEdit({
                    ...selectedStepForEdit,
                    name: e.target.value
                  })}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  checked={selectedStepForEdit.enabled}
                  onCheckedChange={(enabled) => setSelectedStepForEdit({
                    ...selectedStepForEdit,
                    enabled
                  })}
                />
                <Label>Enable Step</Label>
              </div>

              <div className="border-t pt-4">
                <h3 className="text-lg font-semibold mb-3">Settings</h3>
                <div className="space-y-3">
                  {Object.entries(selectedStepForEdit.settings).map(([key, value]) => (
                    <div key={key}>
                      <Label htmlFor={key}>{key}</Label>
                      <Input
                        id={key}
                        value={typeof value === 'object' ? JSON.stringify(value) : value}
                        onChange={(e) => {
                          let newValue: any = e.target.value;
                          try {
                            // Try to parse as JSON for objects
                            if (typeof selectedStepForEdit.settings[key] === 'object') {
                              newValue = JSON.parse(e.target.value);
                            } else if (typeof selectedStepForEdit.settings[key] === 'number') {
                              newValue = Number(e.target.value);
                            } else if (typeof selectedStepForEdit.settings[key] === 'boolean') {
                              newValue = e.target.value === 'true';
                            }
                          } catch {
                            // Keep as string if parsing fails
                          }
                          
                          setSelectedStepForEdit({
                            ...selectedStepForEdit,
                            settings: {
                              ...selectedStepForEdit.settings,
                              [key]: newValue
                            }
                          });
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex justify-end gap-2 mt-6">
              <Button variant="outline" onClick={() => setSelectedStepForEdit(null)}>
                Cancel
              </Button>
              <Button onClick={handleSaveStep}>
                Save Changes
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PipelineBuilder;
