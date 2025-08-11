// PipelineConfigDemo.tsx - Demo page showcasing the configuration system

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Upload, FileText, Settings, Play } from 'lucide-react';
import StepCatalogBrowser from '../components/StepCatalogBrowser';
import PipelineBuilder from '../components/PipelineBuilder';
import { useConfigLoader } from '../hooks/useConfigLoader';

const PipelineConfigDemo: React.FC = () => {
  const {
    stepCatalog,
    pipelines,
    services,
    loading,
    error,
    loadStepCatalog,
    loadPipelineConfig,
    exportConfig
  } = useConfigLoader();

  const [yamlInput, setYamlInput] = useState('');
  const [activeTab, setActiveTab] = useState('catalog');

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
      account_name: \${STORAGE_ACCOUNT_NAME}
      credential_type: \${STORAGE_ACCOUNT_CREDENTIAL_TYPE}
      credential_key: \${STORAGE_ACCOUNT_KEY}

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

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Pipeline Configuration</h2>
        <p className="text-muted-foreground">
          Manage and configure your document processing pipelines with an intuitive interface
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="catalog">Step Catalog</TabsTrigger>
          <TabsTrigger value="builder">Pipeline Builder</TabsTrigger>
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="overview">Overview</TabsTrigger>
        </TabsList>

        {/* Step Catalog Tab */}
        <TabsContent value="catalog" className="space-y-6">
          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Step Catalog Browser
                </CardTitle>
                <CardDescription>
                  Browse available pipeline steps and add them to your pipelines
                </CardDescription>
              </CardHeader>
            </Card>
            <StepCatalogBrowser />
          </div>
        </TabsContent>

        {/* Pipeline Builder Tab */}
        <TabsContent value="builder" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Pipeline Builder
              </CardTitle>
              <CardDescription>
                Visual pipeline editor for configuring step sequences and settings
              </CardDescription>
            </CardHeader>
          </Card>
          <PipelineBuilder />
        </TabsContent>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-6">
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
                    <li>{pipelines.length} pipeline configurations</li>
                  </ul>
                </div>
                <Button onClick={handleExportConfig}>
                  Export as YAML
                </Button>
              </CardContent>
            </Card>
          </div>

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
        </TabsContent>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Step Catalog</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stepCatalog.length}</div>
                  <p className="text-xs text-gray-600">Available steps</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Services</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{services.length}</div>
                  <p className="text-xs text-gray-600">Configured services</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Pipelines</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{pipelines.length}</div>
                  <p className="text-xs text-gray-600">Active pipelines</p>
                </CardContent>
              </Card>
            </div>

            {/* Step Categories */}
            {stepCatalog.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Step Categories</CardTitle>
                  <CardDescription>Available step types in your catalog</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {Array.from(new Set(stepCatalog.map(s => s.category))).map(category => (
                      <Badge key={category} variant="secondary">
                        {category} ({stepCatalog.filter(s => s.category === category).length})
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Services Overview */}
            {services.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Configured Services</CardTitle>
                  <CardDescription>Available service connections</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {services.map(service => (
                      <div key={service.name} className="flex items-center justify-between p-3 border rounded">
                        <div>
                          <div className="font-medium">{service.name}</div>
                          <div className="text-sm text-gray-600">{service.type}</div>
                        </div>
                        <Badge variant={service.test_connection ? "default" : "secondary"}>
                          {service.test_connection ? "Test Connection" : "No Test"}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Pipelines Overview */}
            {pipelines.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Pipeline Summary</CardTitle>
                  <CardDescription>Overview of your configured pipelines</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {pipelines.map(pipeline => (
                      <div key={pipeline.name} className="p-4 border rounded">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium">{pipeline.name}</h3>
                          <Badge variant={pipeline.settings.enabled ? "default" : "secondary"}>
                            {pipeline.settings.enabled ? "Enabled" : "Disabled"}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">{pipeline.description}</p>
                        <div className="text-xs text-muted-foreground">
                          {pipeline.steps.length} steps • Version {pipeline.version}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Getting Started */}
            {stepCatalog.length === 0 && pipelines.length === 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Getting Started</CardTitle>
                  <CardDescription>Load a configuration to begin</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    To get started with the pipeline configuration system:
                  </p>
                  <ol className="list-decimal list-inside space-y-2 text-sm">
                    <li>Go to the Configuration tab</li>
                    <li>Load a sample step catalog or pipeline configuration</li>
                    <li>Browse the Step Catalog to see available steps</li>
                    <li>Use the Pipeline Builder to create and configure pipelines</li>
                    <li>Export your configuration when ready</li>
                  </ol>
                  <div className="flex gap-2">
                    <Button onClick={() => setActiveTab('config')}>
                      <Play className="h-4 w-4 mr-2" />
                      Go to Configuration
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PipelineConfigDemo;
