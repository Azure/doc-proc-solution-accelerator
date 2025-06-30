// StepCatalogBrowser.tsx - UI Component for browsing and configuring steps

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Search, Plus, Settings, Image, Brain, Cog } from 'lucide-react';

// Types based on your YAML schema
interface StepCatalogItem {
  id: string;
  name: string;
  description: string;
  type: string;
  module_name: string;
  module_path: string;
  class_name: string;
  tags: string[];
  category: string;
  version: string;
  default_settings: Record<string, any>;
  ui_metadata: {
    icon: string;
    color: string;
    description_long: string;
  };
  config_schema: {
    properties: Record<string, ConfigProperty>;
  };
}

interface ConfigProperty {
  type: string;
  title: string;
  description: string;
  default?: any;
  required?: boolean;
  minimum?: number;
  maximum?: number;
  multipleOf?: number;
  enum?: string[];
  pattern?: string;
  ui_component?: string;
  service_type?: string;
}

interface StepInstance {
  name: string;
  step_catalog_id: string;
  enabled: boolean;
  settings: Record<string, any>;
}

const iconMap = {
  gear: Cog,
  image: Image,
  brain: Brain,
};

const StepCatalogBrowser: React.FC = () => {
  const [stepCatalog, setStepCatalog] = useState<StepCatalogItem[]>([]);
  const [filteredSteps, setFilteredSteps] = useState<StepCatalogItem[]>([]);
  const [selectedStep, setSelectedStep] = useState<StepCatalogItem | null>(null);
  const [stepInstance, setStepInstance] = useState<StepInstance | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showConfigModal, setShowConfigModal] = useState(false);

  // Mock data - in real app, this would come from your YAML loader
  useEffect(() => {
    const mockCatalog: StepCatalogItem[] = [
      {
        id: 'sample_step',
        name: 'Sample Development Step',
        description: 'Sample step for development and testing',
        type: 'script',
        module_name: 'sample',
        module_path: './doc/proc/step/sample.py',
        class_name: 'SampleStep',
        tags: ['sample', 'development'],
        category: 'Development',
        version: '1.0',
        default_settings: {
          fail_pipeline_on_error: true,
          retry_on_failure: true,
          retries: 3,
          timeout: 600
        },
        ui_metadata: {
          icon: 'gear',
          color: '#6B7280',
          description_long: 'A sample step used for development and testing purposes.'
        },
        config_schema: {
          properties: {
            key1: {
              type: 'string',
              title: 'Custom Key 1',
              description: 'First custom configuration key',
              default: 'value1'
            },
            key2: {
              type: 'string',
              title: 'Custom Key 2',
              description: 'Second custom configuration key',
              default: 'value2'
            },
            debug_mode: {
              type: 'boolean',
              title: 'Debug Mode',
              description: 'Enable debug logging for this step',
              default: false
            }
          }
        }
      },
      {
        id: 'pdf_to_png',
        name: 'PDF to PNG Converter',
        description: 'Convert PDF pages to PNG images',
        type: 'script',
        module_name: 'pdf_to_png',
        module_path: './doc/proc/step/extract_pdf_to_png.py',
        class_name: 'PDFPagesToPNGStep',
        tags: ['pdf', 'png', 'conversion', 'azure_blob'],
        category: 'Document Processing',
        version: '2.1',
        default_settings: {
          fail_pipeline_on_error: true,
          retry_on_failure: false,
          retries: 3,
          timeout: 600
        },
        ui_metadata: {
          icon: 'image',
          color: '#10B981',
          description_long: 'Converts PDF document pages into PNG image files.'
        },
        config_schema: {
          properties: {
            png_output_folder: {
              type: 'string',
              title: 'PNG Output Folder',
              description: 'Directory path where PNG files will be saved',
              default: './output/png',
              required: true
            },
            num_pages: {
              type: 'integer',
              title: 'Number of Pages',
              description: 'Maximum number of pages to convert',
              default: 10,
              minimum: 0,
              maximum: 1000
            },
            dpi: {
              type: 'integer',
              title: 'DPI Resolution',
              description: 'Resolution for PNG output in dots per inch',
              default: 300,
              minimum: 72,
              maximum: 600
            },
            image_format: {
              type: 'string',
              title: 'Image Format',
              description: 'Output image format',
              default: 'PNG',
              enum: ['PNG', 'JPEG', 'TIFF']
            }
          }
        }
      },
      {
        id: 'pdf_page_png_to_markdown',
        name: 'PNG to Markdown Converter',
        description: 'Convert PDF page images to Markdown using AI',
        type: 'script',
        module_name: 'pdf_page_png_to_markdown',
        module_path: './doc/proc/step/pdf_page_png_to_markdown.py',
        class_name: 'PDFPagePNGToMarkdownStep',
        tags: ['transform', 'extraction', 'markdown', 'azure_ai_inference', 'ai'],
        category: 'AI Processing',
        version: '1.5',
        default_settings: {
          fail_pipeline_on_error: true,
          retry_on_failure: false,
          retries: 3,
          timeout: 600
        },
        ui_metadata: {
          icon: 'brain',
          color: '#8B5CF6',
          description_long: 'Uses Azure AI services to extract text and generate markdown from PDF page images.'
        },
        config_schema: {
          properties: {
            ai_model_inference_service: {
              type: 'string',
              title: 'AI Inference Service',
              description: 'Reference to the AI service configuration',
              required: true,
              ui_component: 'service_selector',
              service_type: 'azure_ai_inference'
            },
            max_completion_tokens: {
              type: 'integer',
              title: 'Max Completion Tokens',
              description: 'Maximum number of tokens to generate',
              default: 4000,
              minimum: 100,
              maximum: 8000
            },
            temperature: {
              type: 'number',
              title: 'Temperature',
              description: 'Controls randomness in AI responses',
              default: 1.0,
              minimum: 0.0,
              maximum: 2.0,
              multipleOf: 0.1
            }
          }
        }
      }
    ];
    
    // Only set mock data if no data is already loaded
    if (stepCatalog.length === 0) {
      setStepCatalog(mockCatalog);
      setFilteredSteps(mockCatalog);
    }
  }, [stepCatalog.length]);

  // Filter steps based on search and category
  useEffect(() => {
    let filtered = stepCatalog;
    
    if (searchTerm) {
      filtered = filtered.filter(step => 
        step.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        step.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        step.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(step => step.category === selectedCategory);
    }
    
    setFilteredSteps(filtered);
  }, [searchTerm, selectedCategory, stepCatalog]);

  const categories = Array.from(new Set(stepCatalog.map(step => step.category)));

  const handleAddStep = (step: StepCatalogItem) => {
    const newInstance: StepInstance = {
      name: `${step.id}_${Date.now()}`,
      step_catalog_id: step.id,
      enabled: true,
      settings: Object.fromEntries(
        Object.entries(step.config_schema.properties).map(([key, prop]) => [
          key,
          prop.default
        ])
      )
    };
    
    setSelectedStep(step);
    setStepInstance(newInstance);
    setShowConfigModal(true);
  };

  const renderConfigField = (key: string, property: ConfigProperty, value: any, onChange: (value: any) => void) => {
    switch (property.type) {
      case 'boolean':
        return (
          <div className="flex items-center space-x-2">
            <Switch
              checked={value || false}
              onCheckedChange={onChange}
            />
            <Label>{property.title}</Label>
          </div>
        );
      
      case 'integer':
        if (property.minimum !== undefined && property.maximum !== undefined) {
          return (
            <div className="space-y-2">
              <Label>{property.title}: {value}</Label>
              <Slider
                value={[value || property.default]}
                onValueChange={(values) => onChange(values[0])}
                min={property.minimum}
                max={property.maximum}
                step={1}
              />
            </div>
          );
        }
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{property.title}</Label>
            <Input
              id={key}
              type="number"
              value={value || ''}
              onChange={(e) => onChange(parseInt(e.target.value))}
              placeholder={property.description}
            />
          </div>
        );
      
      case 'number':
        if (property.minimum !== undefined && property.maximum !== undefined) {
          return (
            <div className="space-y-2">
              <Label>{property.title}: {value?.toFixed(1)}</Label>
              <Slider
                value={[value || property.default]}
                onValueChange={(values) => onChange(values[0])}
                min={property.minimum}
                max={property.maximum}
                step={property.multipleOf || 0.1}
              />
            </div>
          );
        }
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{property.title}</Label>
            <Input
              id={key}
              type="number"
              value={value || ''}
              onChange={(e) => onChange(parseFloat(e.target.value))}
              placeholder={property.description}
            />
          </div>
        );
      
      case 'string':
        if (property.enum) {
          return (
            <div className="space-y-2">
              <Label>{property.title}</Label>
              <Select value={value || property.default} onValueChange={onChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {property.enum.map(option => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          );
        }
        
        if (property.ui_component === 'textarea') {
          return (
            <div className="space-y-2">
              <Label htmlFor={key}>{property.title}</Label>
              <Textarea
                id={key}
                value={value || ''}
                onChange={(e) => onChange(e.target.value)}
                placeholder={property.description}
                rows={4}
              />
            </div>
          );
        }
        
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{property.title}</Label>
            <Input
              id={key}
              value={value || ''}
              onChange={(e) => onChange(e.target.value)}
              placeholder={property.description}
            />
          </div>
        );
      
      default:
        return (
          <div className="space-y-2">
            <Label htmlFor={key}>{property.title}</Label>
            <Input
              id={key}
              value={JSON.stringify(value) || ''}
              onChange={(e) => {
                try {
                  onChange(JSON.parse(e.target.value));
                } catch {
                  onChange(e.target.value);
                }
              }}
              placeholder={property.description}
            />
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-2xl font-bold tracking-tight">Available Steps</h3>
        <p className="text-muted-foreground">Browse and configure pipeline steps</p>
      </div>

      {/* Search and Filter Controls */}
      <div className="flex gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search steps..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map(category => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Step Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSteps.map((step) => {
          const IconComponent = iconMap[step.ui_metadata.icon as keyof typeof iconMap] || Settings;
          
          return (
            <Card key={step.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${step.ui_metadata.color}20` }}
                    >
                      <IconComponent 
                        className="h-5 w-5" 
                        style={{ color: step.ui_metadata.color }}
                      />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{step.name}</CardTitle>
                      <Badge variant="secondary">{step.category}</Badge>
                    </div>
                  </div>
                  <Badge variant="outline">v{step.version}</Badge>
                </div>
                <CardDescription>{step.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    {step.ui_metadata.description_long}
                  </p>
                  
                  <div className="flex flex-wrap gap-1">
                    {step.tags.map(tag => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  
                  <Button 
                    onClick={() => handleAddStep(step)}
                    className="w-full"
                    size="sm"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add to Pipeline
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Configuration Modal */}
      {showConfigModal && selectedStep && stepInstance && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-4">Configure {selectedStep.name}</h2>
            
            <div className="space-y-4 mb-6">
              <div className="space-y-2">
                <Label htmlFor="step-name">Step Instance Name</Label>
                <Input
                  id="step-name"
                  value={stepInstance.name}
                  onChange={(e) => setStepInstance({
                    ...stepInstance,
                    name: e.target.value
                  })}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  checked={stepInstance.enabled}
                  onCheckedChange={(enabled) => setStepInstance({
                    ...stepInstance,
                    enabled
                  })}
                />
                <Label>Enable Step</Label>
              </div>

              <div className="border-t pt-4">
                <h3 className="text-lg font-semibold mb-3">Configuration</h3>
                <div className="space-y-4">
                  {Object.entries(selectedStep.config_schema.properties).map(([key, property]) => (
                    <div key={key}>
                      {renderConfigField(
                        key,
                        property,
                        stepInstance.settings[key],
                        (value) => setStepInstance({
                          ...stepInstance,
                          settings: {
                            ...stepInstance.settings,
                            [key]: value
                          }
                        })
                      )}
                      <p className="text-xs text-gray-500 mt-1">{property.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button 
                variant="outline" 
                onClick={() => setShowConfigModal(false)}
              >
                Cancel
              </Button>
              <Button onClick={() => {
                // Here you would save the step instance to your pipeline
                console.log('Saving step instance:', stepInstance);
                setShowConfigModal(false);
              }}>
                Add Step
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StepCatalogBrowser;
