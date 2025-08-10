
import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Save } from "lucide-react";

interface StepInstanceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  stepName: string;
  stepType: string;
  onSave: (config: any) => void;
}

const StepInstanceDialog = ({ 
  isOpen, 
  onClose, 
  stepName, 
  stepType, 
  onSave 
}: StepInstanceDialogProps) => {
  const [config, setConfig] = useState({
    instanceName: stepName,
    enabled: true,
    instanceConfig: {}
  });

  const renderInstanceConfiguration = () => {
    switch (stepType) {
      case 'connector':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="connection-string">Connection String</Label>
              <Input id="connection-string" placeholder="Enter connection details" />
            </div>
            <div>
              <Label htmlFor="batch-size">Batch Size</Label>
              <Input id="batch-size" type="number" defaultValue="10" />
            </div>
          </div>
        );
      
      case 'extractor':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="confidence-threshold">Confidence Threshold</Label>
              <Input id="confidence-threshold" type="number" step="0.1" defaultValue="0.8" />
            </div>
            <div>
              <Label htmlFor="custom-entities">Custom Entities</Label>
              <Textarea id="custom-entities" placeholder="Enter custom entity types" />
            </div>
          </div>
        );

      case 'ai-prompt':
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="api-key">API Key</Label>
              <Input id="api-key" type="password" placeholder="Enter API key" />
            </div>
            <div>
              <Label htmlFor="custom-prompt">Custom Prompt</Label>
              <Textarea 
                id="custom-prompt" 
                placeholder="Enter your custom prompt template"
                rows={4}
              />
            </div>
          </div>
        );
      
      default:
        return (
          <div className="space-y-4">
            <div>
              <Label htmlFor="custom-setting">Custom Setting</Label>
              <Input id="custom-setting" placeholder="Configure step-specific settings" />
            </div>
          </div>
        );
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Configure Step Instance: {stepName}</DialogTitle>
          <DialogDescription>
            Configure the specific settings for this step instance in the pipeline
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          <div>
            <Label htmlFor="instance-name">Instance Name</Label>
            <Input 
              id="instance-name" 
              value={config.instanceName}
              onChange={(e) => setConfig({ ...config, instanceName: e.target.value })}
              placeholder="Enter instance name"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox 
              id="enabled"
              checked={config.enabled}
              onCheckedChange={(checked) => setConfig({ ...config, enabled: !!checked })}
            />
            <Label htmlFor="enabled">Enable this step instance</Label>
          </div>

          <div>
            <Label className="text-base font-medium mb-3 block">Instance Configuration</Label>
            {renderInstanceConfiguration()}
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

export default StepInstanceDialog;