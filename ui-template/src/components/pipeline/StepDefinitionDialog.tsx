
import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Upload, Save, FileText } from "lucide-react";
import { StepDefinition } from "./StepDefinition";

interface StepDefinitionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  step?: StepDefinition;
  onSave: (step: Partial<StepDefinition>) => void;
}

const StepDefinitionDialog = ({ 
  isOpen, 
  onClose, 
  step, 
  onSave 
}: StepDefinitionDialogProps) => {
  const [formData, setFormData] = useState({
    name: step?.name || '',
    description: step?.description || '',
    type: step?.type || 'connector',
    module: step?.module || '',
    version: step?.version || '1.0.0',
    defaultConfig: step?.defaultConfig || {}
  });

  const handleYamlUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const yamlContent = e.target?.result as string;
          console.log('YAML Configuration loaded:', yamlContent);
          // Parse YAML and update form data
        } catch (error) {
          console.error('Error parsing YAML:', error);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleSave = () => {
    onSave({
      ...formData,
      id: step?.id || Date.now().toString(),
      created: step?.created || new Date().toISOString(),
      updated: new Date().toISOString()
    });
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{step ? 'Edit Step Definition' : 'Create Step Definition'}</DialogTitle>
          <DialogDescription>
            Configure the general settings for this step definition
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
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Enter step name"
            />
          </div>
          
          <div>
            <Label htmlFor="step-description">Description</Label>
            <Textarea 
              id="step-description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Enter step description"
            />
          </div>

          <div>
            <Label htmlFor="step-type">Step Type</Label>
            <Select value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value as any })}>
              <SelectTrigger>
                <SelectValue placeholder="Select step type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="connector">Connector</SelectItem>
                <SelectItem value="extractor">Text Extractor</SelectItem>
                <SelectItem value="image-extractor">Image Extractor</SelectItem>
                <SelectItem value="ai-prompt">AI Prompt</SelectItem>
                <SelectItem value="summarizer">Summarizer</SelectItem>
                <SelectItem value="output">Output Writer</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="step-module">Module</Label>
            <Input 
              id="step-module" 
              value={formData.module}
              onChange={(e) => setFormData({ ...formData, module: e.target.value })}
              placeholder="e.g., azure-document-intelligence"
            />
          </div>

          <div>
            <Label htmlFor="step-version">Version</Label>
            <Input 
              id="step-version" 
              value={formData.version}
              onChange={(e) => setFormData({ ...formData, version: e.target.value })}
              placeholder="1.0.0"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSave}>
              <Save className="h-4 w-4 mr-2" />
              Save Step Definition
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default StepDefinitionDialog;