
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { 
  Save, 
  AlertTriangle,
  Globe,
  Clock,
  Loader2
} from "lucide-react";
import { Pipeline, PipelineSettings as PipelineSettingsType, pipelinesApi } from "@/lib/api";

interface PipelineSettingsProps {
  pipeline?: Pipeline;
  onPipelineUpdated?: (pipeline: Pipeline) => void;
}

const PipelineSettings = ({ pipeline, onPipelineUpdated }: PipelineSettingsProps) => {
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Pipeline basic info
  const [pipelineName, setPipelineName] = useState("");
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("");
  
  // Pipeline settings
  const [isEnabled, setIsEnabled] = useState(true);
  const [retryDelay, setRetryDelay] = useState(5);
  const [timeoutValue, setTimeoutValue] = useState(600);
  const [retryAttempts, setRetryAttempts] = useState(3);
  const [maxConcurrency, setMaxConcurrency] = useState(5);
  
  // Load pipeline data when component mounts or pipeline prop changes
  useEffect(() => {
    if (pipeline) {
      setPipelineName(pipeline.name);
      setDescription(pipeline.description || "");
      setVersion(pipeline.version || "1.0");
      
      const settings = pipeline.settings;
      if (settings) {
        setIsEnabled(settings.enabled);
        setRetryDelay(settings.retry_delay);
        setTimeoutValue(settings.timeout);
        setRetryAttempts(settings.retries);
        setMaxConcurrency(settings.max_concurrent_runs);
      }
    }
  }, [pipeline]);

  const handleSave = async () => {
    if (!pipeline) {
      toast({
        title: "Error",
        description: "No pipeline selected",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    
    try {
      const updatedSettings: PipelineSettingsType = {
        enabled: isEnabled,
        retry_delay: retryDelay,
        timeout: timeoutValue,
        retries: retryAttempts,
        max_concurrent_runs: maxConcurrency,
      };

      const updateData = {
        description,
        version,
        settings: updatedSettings,
        // Keep the existing data
        steps: pipeline.steps,
        execution_sequence: pipeline.execution_sequence,
      };

      // For now, we'll create a full pipeline object since the API expects it
      const fullPipelineUpdate: Pipeline = {
        ...pipeline,
        description,
        version,
        settings: updatedSettings,
      };

      const updatedPipeline = await pipelinesApi.updatePipeline(pipeline.id, fullPipelineUpdate);
      
      toast({
        title: "Settings saved",
        description: "Pipeline settings have been updated successfully.",
      });

      if (onPipelineUpdated) {
        onPipelineUpdated(updatedPipeline);
      }
    } catch (error) {
      console.error("Error saving pipeline settings:", error);
      toast({
        title: "Error",
        description: "Failed to save pipeline settings. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleNumberChange = (value: string, setter: (val: number) => void, min: number = 0) => {
    const numValue = parseInt(value, 10);
    if (!isNaN(numValue) && numValue >= min) {
      setter(numValue);
    }
  };

  if (!pipeline) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">No pipeline selected</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* General Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            General Settings
          </CardTitle>
          <CardDescription>Configure basic pipeline settings and behavior</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-base">Enable Pipeline</Label>
              <div className="text-sm text-muted-foreground">
                When disabled, the pipeline won't process any documents
              </div>
            </div>
            <Switch
              checked={isEnabled}
              onCheckedChange={setIsEnabled}
            />
          </div>

          <Separator />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="pipeline-name">Pipeline Name</Label>
              <Input
                id="pipeline-name"
                value={pipelineName}
                readOnly
                className="bg-muted"
                title="Pipeline name can only be changed from the main pipeline view"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Name can only be changed from the main pipeline view
              </p>
            </div>
            
            <div>
              <Label htmlFor="version">Pipeline Version</Label>
              <Input
                id="version"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="1.0"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Performance Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Performance & Reliability
          </CardTitle>
          <CardDescription>Configure execution limits and retry behavior</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="max-concurrency">Max Concurrent Jobs</Label>
              <Input
                id="max-concurrency"
                type="number"
                value={maxConcurrency.toString()}
                onChange={(e) => handleNumberChange(e.target.value, setMaxConcurrency, 1)}
                min="1"
                max="20"
              />
            </div>
            
            <div>
              <Label htmlFor="timeout">Timeout (seconds)</Label>
              <Input
                id="timeout"
                type="number"
                value={timeoutValue.toString()}
                onChange={(e) => handleNumberChange(e.target.value, setTimeoutValue, 30)}
                min="30"
                max="3600"
              />
            </div>
            
            <div>
              <Label htmlFor="retry-attempts">Retry Attempts</Label>
              <Input
                id="retry-attempts"
                type="number"
                value={retryAttempts.toString()}
                onChange={(e) => handleNumberChange(e.target.value, setRetryAttempts, 0)}
                min="0"
                max="10"
              />
            </div>

            <div>
              <Label htmlFor="retry-delay">Retry Delay (seconds)</Label>
              <Input
                id="retry-delay"
                type="number"
                value={retryDelay.toString()}
                onChange={(e) => handleNumberChange(e.target.value, setRetryDelay, 1)}
                min="1"
                max="300"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Actions */}
      <div className="flex justify-end space-x-2">
        <Button variant="outline" disabled={isSaving}>
          Cancel
        </Button>
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Configuration
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default PipelineSettings;