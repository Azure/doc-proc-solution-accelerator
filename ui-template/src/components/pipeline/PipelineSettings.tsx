
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { 
  Save, 
  AlertTriangle,
  Globe,
  Key,
  Clock
} from "lucide-react";

const PipelineSettings = () => {
  const [isEnabled, setIsEnabled] = useState(true);
  const [pipelineName, setPipelineName] = useState("Legal Document Processing");
  const [description, setDescription] = useState("Extract entities and summarize legal contracts and agreements");
  const [schedule, setSchedule] = useState("manual");
  const [maxConcurrency, setMaxConcurrency] = useState("5");
  const [timeoutValue, setTimeoutValue] = useState("300");
  const [retryAttempts, setRetryAttempts] = useState("3");

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
                onChange={(e) => setPipelineName(e.target.value)}
              />
            </div>
            
            <div>
              <Label htmlFor="schedule">Execution Schedule</Label>
              <Select value={schedule} onValueChange={setSchedule}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="manual">Manual Only</SelectItem>
                  <SelectItem value="hourly">Every Hour</SelectItem>
                  <SelectItem value="daily">Daily at 2 AM</SelectItem>
                  <SelectItem value="weekly">Weekly on Sunday</SelectItem>
                  <SelectItem value="custom">Custom Schedule</SelectItem>
                </SelectContent>
              </Select>
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="max-concurrency">Max Concurrent Jobs</Label>
              <Input
                id="max-concurrency"
                type="number"
                value={maxConcurrency}
                onChange={(e) => setMaxConcurrency(e.target.value)}
                min="1"
                max="20"
              />
            </div>
            
            <div>
              <Label htmlFor="timeout">Timeout (seconds)</Label>
              <Input
                id="timeout"
                type="number"
                value={timeoutValue}
                onChange={(e) => setTimeoutValue(e.target.value)}
                min="30"
                max="3600"
              />
            </div>
            
            <div>
              <Label htmlFor="retry-attempts">Retry Attempts</Label>
              <Input
                id="retry-attempts"
                type="number"
                value={retryAttempts}
                onChange={(e) => setRetryAttempts(e.target.value)}
                min="0"
                max="10"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API Keys & Secrets */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            API Keys & Authentication
          </CardTitle>
          <CardDescription>Manage authentication credentials for external services</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-4">
            <div>
              <Label htmlFor="cosmos-key">Azure Cosmos DB Connection String</Label>
              <Input
                id="cosmos-key"
                type="password"
                placeholder="••••••••••••••••••••••••"
              />
            </div>
            <div>
              <Label htmlFor="ai-key">Azure AI Services API Key</Label>
              <Input
                id="ai-key"
                type="password"
                placeholder="••••••••••••••••••••••••"
              />
            </div>
            <div>
              <Label htmlFor="search-key">Azure AI Search Admin Key</Label>
              <Input
                id="search-key"
                type="password"
                placeholder="••••••••••••••••••••••••"
              />
            </div>
          </div>
          <div className="flex items-center p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2" />
            <p className="text-sm text-yellow-800">
              API keys are encrypted and stored securely. They are never displayed in plain text.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Save Actions */}
      <div className="flex justify-end space-x-2">
        <Button variant="outline">Cancel</Button>
        <Button>
          <Save className="h-4 w-4 mr-2" />
          Save Configuration
        </Button>
      </div>
    </div>
  );
};

export default PipelineSettings;