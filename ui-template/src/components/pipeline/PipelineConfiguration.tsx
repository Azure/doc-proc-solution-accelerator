
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  Plus, 
  Save, 
  FileText, 
  Database, 
  Brain, 
  Search, 
  Upload,
  Settings2
} from "lucide-react";

const stepTypes = [
  { value: 'connector', label: 'Connector', icon: Upload, description: 'Input/Output connectors' },
  { value: 'extractor', label: 'Entity Extractor', icon: Search, description: 'Extract entities and key information' },
  { value: 'summarizer', label: 'Summarizer', icon: Brain, description: 'AI-powered content summarization' },
  { value: 'output', label: 'Output Writer', icon: Database, description: 'Data output and storage' }
];

const PipelineConfiguration = () => {
  const [selectedStep, setSelectedStep] = useState<string | null>(null);
  const [stepConfig, setStepConfig] = useState({
    name: '',
    type: '',
    description: '',
    enabled: true,
    settings: {}
  });

  const renderStepConfiguration = () => {
    switch (stepConfig.type) {
      case 'connector':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="source-type">Source Type</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select source type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="file">File Upload</SelectItem>
                  <SelectItem value="blob">Azure Blob Storage</SelectItem>
                  <SelectItem value="sharepoint">SharePoint</SelectItem>
                  <SelectItem value="api">REST API</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="file-types">Supported File Types</Label>
              <Input id="file-types" placeholder="pdf, docx, txt" />
            </div>
          </div>
        );
      
      case 'extractor':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="extraction-type">Extraction Method</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select extraction method" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="nlp">Natural Language Processing</SelectItem>
                  <SelectItem value="regex">Regular Expressions</SelectItem>
                  <SelectItem value="ai">AI-Powered Extraction</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="entities">Target Entities</Label>
              <Textarea id="entities" placeholder="Person, Organization, Date, Amount..." />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox id="confidence-threshold" />
              <Label htmlFor="confidence-threshold">Set confidence threshold</Label>
            </div>
          </div>
        );
      
      case 'summarizer':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="model">AI Model</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select AI model" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4">GPT-4</SelectItem>
                  <SelectItem value="gpt-3.5">GPT-3.5 Turbo</SelectItem>
                  <SelectItem value="claude">Claude</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="summary-length">Summary Length</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select length" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="short">Short (1-2 sentences)</SelectItem>
                  <SelectItem value="medium">Medium (1 paragraph)</SelectItem>
                  <SelectItem value="detailed">Detailed (2-3 paragraphs)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="prompt">Custom Prompt (Optional)</Label>
              <Textarea id="prompt" placeholder="Enter custom summarization prompt..." />
            </div>
          </div>
        );
      
      case 'output':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="output-type">Output Destination</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select destination" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cosmosdb">Azure Cosmos DB</SelectItem>
                  <SelectItem value="search">Azure AI Search</SelectItem>
                  <SelectItem value="blob">Azure Blob Storage</SelectItem>
                  <SelectItem value="api">REST API</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="format">Output Format</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="xml">XML</SelectItem>
                  <SelectItem value="csv">CSV</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        );
      
      default:
        return <p className="text-muted-foreground">Select a step type to configure</p>;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Step Types */}
      <Card>
        <CardHeader>
          <CardTitle>Available Step Types</CardTitle>
          <CardDescription>Choose from different types of processing steps</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {stepTypes.map((type) => {
            const IconComponent = type.icon;
            return (
              <div 
                key={type.value}
                className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-accent"
                onClick={() => setStepConfig({ ...stepConfig, type: type.value })}
              >
                <IconComponent className="h-8 w-8 text-muted-foreground mr-3" />
                <div className="flex-1">
                  <h3 className="font-medium">{type.label}</h3>
                  <p className="text-sm text-muted-foreground">{type.description}</p>
                </div>
                <Button size="sm">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Step Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Step Configuration</CardTitle>
          <CardDescription>Configure the selected processing step</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="step-name">Step Name</Label>
            <Input 
              id="step-name" 
              value={stepConfig.name}
              onChange={(e) => setStepConfig({ ...stepConfig, name: e.target.value })}
              placeholder="Enter step name"
            />
          </div>
          
          <div>
            <Label htmlFor="step-description">Description</Label>
            <Textarea 
              id="step-description"
              value={stepConfig.description}
              onChange={(e) => setStepConfig({ ...stepConfig, description: e.target.value })}
              placeholder="Enter step description"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox 
              id="enabled"
              checked={stepConfig.enabled}
              onCheckedChange={(checked) => setStepConfig({ ...stepConfig, enabled: !!checked })}
            />
            <Label htmlFor="enabled">Enable this step</Label>
          </div>

          <Separator />

          <div>
            <Label className="text-base font-medium mb-3 block">Step-Specific Settings</Label>
            {renderStepConfiguration()}
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline">Cancel</Button>
            <Button>
              <Save className="h-4 w-4 mr-2" />
              Save Step
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PipelineConfiguration;