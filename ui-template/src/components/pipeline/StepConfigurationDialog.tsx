
import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Upload, Save, FileText } from "lucide-react";

interface StepConfigurationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  stepType: string;
  stepName: string;
  stepDescription: string;
  onSave: (config: any) => void;
}

const StepConfigurationDialog = ({ 
  isOpen, 
  onClose, 
  stepType, 
  stepName, 
  stepDescription, 
  onSave 
}: StepConfigurationDialogProps) => {
  const [config, setConfig] = useState({
    name: stepName,
    description: stepDescription,
    enabled: true,
    settings: {}
  });

  const handleYamlUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          // Simple YAML parsing - in production you'd use a proper YAML parser
          const yamlContent = e.target?.result as string;
          console.log('YAML Configuration loaded:', yamlContent);
          // Here you would parse the YAML and update the config
        } catch (error) {
          console.error('Error parsing YAML:', error);
        }
      };
      reader.readAsText(file);
    }
  };

  const renderStepConfiguration = () => {
    switch (stepType) {
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
              <Input id="file-types" placeholder="pdf, docx, txt, png, jpg" />
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
          </div>
        );

      case 'image-extractor':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="image-processing">Image Processing</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select processing method" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ocr">OCR Text Extraction</SelectItem>
                  <SelectItem value="vision">AI Vision Analysis</SelectItem>
                  <SelectItem value="both">OCR + Vision Analysis</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="image-formats">Supported Formats</Label>
              <Input id="image-formats" placeholder="jpg, png, gif, bmp, tiff" />
            </div>
          </div>
        );

      case 'ai-prompt':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="ai-model">AI Model</Label>
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
              <Label htmlFor="prompt-template">Prompt Template</Label>
              <Textarea 
                id="prompt-template" 
                placeholder="Analyze the following document text and extract key insights: {extracted_text}"
                rows={4}
              />
            </div>
          </div>
        );
      
      default:
        return <p className="text-muted-foreground">Select a step type to configure</p>;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Configure {stepName}</DialogTitle>
          <DialogDescription>
            Configure the settings for this pipeline step
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="flex gap-2">
            <Button variant="outline" className="flex-1">
              <Upload className="h-4 w-4 mr-2" />
              <Label htmlFor="yaml-upload" className="cursor-pointer">
                Load from YAML
              </Label>
              <Input
                id="yaml-upload"
                type="file"
                accept=".yml,.yaml"
                onChange={handleYamlUpload}
                className="hidden"
              />
            </Button>
            <Button variant="outline">
              <FileText className="h-4 w-4 mr-2" />
              Export YAML
            </Button>
          </div>

          <div>
            <Label htmlFor="step-name">Step Name</Label>
            <Input 
              id="step-name" 
              value={config.name}
              onChange={(e) => setConfig({ ...config, name: e.target.value })}
              placeholder="Enter step name"
            />
          </div>
          
          <div>
            <Label htmlFor="step-description">Description</Label>
            <Textarea 
              id="step-description"
              value={config.description}
              onChange={(e) => setConfig({ ...config, description: e.target.value })}
              placeholder="Enter step description"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox 
              id="enabled"
              checked={config.enabled}
              onCheckedChange={(checked) => setConfig({ ...config, enabled: !!checked })}
            />
            <Label htmlFor="enabled">Enable this step</Label>
          </div>

          <div>
            <Label className="text-base font-medium mb-3 block">Step Configuration</Label>
            {renderStepConfiguration()}
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={() => onSave(config)}>
              <Save className="h-4 w-4 mr-2" />
              Save Configuration
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default StepConfigurationDialog;