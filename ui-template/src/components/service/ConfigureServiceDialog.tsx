
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useForm } from "react-hook-form";
import { Settings } from "lucide-react";

interface ServiceStatus {
  id: string;
  name: string;
  type: string;
  status: 'connected' | 'error' | 'testing';
  lastTested: string;
  error?: string;
  description: string;
}

interface ConfigureServiceDialogProps {
  service: ServiceStatus;
  onUpdateService: (serviceId: string, config: any) => void;
}

interface BaseConfigFormData {
  timeout: string;
}

interface DatabaseConfigFormData extends BaseConfigFormData {
  connectionString: string;
  database: string;
  username: string;
  password: string;
}

interface AIConfigFormData extends BaseConfigFormData {
  endpoint: string;
  apiKey: string;
  model: string;
  region: string;
}

interface StorageConfigFormData extends BaseConfigFormData {
  endpoint: string;
  accessKey: string;
  secretKey: string;
  bucket: string;
}

interface SearchConfigFormData extends BaseConfigFormData {
  endpoint: string;
  apiKey: string;
  index: string;
}

interface IntegrationConfigFormData extends BaseConfigFormData {
  endpoint: string;
  clientId: string;
  clientSecret: string;
  tenantId: string;
}

interface AnalyticsConfigFormData extends BaseConfigFormData {
  endpoint: string;
  apiKey: string;
  workspace: string;
}

interface MonitoringConfigFormData extends BaseConfigFormData {
  endpoint: string;
  instrumentationKey: string;
  resourceGroup: string;
}

type ConfigFormData = DatabaseConfigFormData | AIConfigFormData | StorageConfigFormData | 
  SearchConfigFormData | IntegrationConfigFormData | AnalyticsConfigFormData | MonitoringConfigFormData;

export function ConfigureServiceDialog({ service, onUpdateService }: ConfigureServiceDialogProps) {
  const [open, setOpen] = useState(false);
  
  const getDefaultValues = () => {
    const baseDefaults = { timeout: "30" };
    
    switch (service.type) {
      case 'Database':
        return { ...baseDefaults, connectionString: "", database: "", username: "", password: "" };
      case 'AI Platform':
        return { ...baseDefaults, endpoint: "", apiKey: "", model: "", region: "" };
      case 'Storage':
        return { ...baseDefaults, endpoint: "", accessKey: "", secretKey: "", bucket: "" };
      case 'Search Engine':
        return { ...baseDefaults, endpoint: "", apiKey: "", index: "" };
      case 'Integration':
        return { ...baseDefaults, endpoint: "", clientId: "", clientSecret: "", tenantId: "" };
      case 'Analytics':
        return { ...baseDefaults, endpoint: "", apiKey: "", workspace: "" };
      case 'Monitoring':
        return { ...baseDefaults, endpoint: "", instrumentationKey: "", resourceGroup: "" };
      default:
        return baseDefaults;
    }
  };

  const form = useForm<ConfigFormData>({
    defaultValues: getDefaultValues()
  });

  const onSubmit = (data: ConfigFormData) => {
    onUpdateService(service.id, data);
    setOpen(false);
  };

  const renderDatabaseFields = () => (
    <>
      <FormField
        control={form.control}
        name="connectionString"
        rules={{ required: "Connection string is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Connection String</FormLabel>
            <FormControl>
              <Input placeholder="Server=...;Database=...;" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="database"
        rules={{ required: "Database name is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Database Name</FormLabel>
            <FormControl>
              <Input placeholder="mydatabase" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="username"
        rules={{ required: "Username is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Username</FormLabel>
            <FormControl>
              <Input placeholder="username" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="password"
        rules={{ required: "Password is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Password</FormLabel>
            <FormControl>
              <Input type="password" placeholder="password" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );

  const renderAIFields = () => (
    <>
      <FormField
        control={form.control}
        name="endpoint"
        rules={{ required: "Endpoint is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>API Endpoint</FormLabel>
            <FormControl>
              <Input placeholder="https://api.openai.com/v1" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="apiKey"
        rules={{ required: "API Key is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>API Key</FormLabel>
            <FormControl>
              <Input type="password" placeholder="sk-..." {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="model"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Model</FormLabel>
            <Select onValueChange={field.onChange} defaultValue={field.value}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="gpt-4">GPT-4</SelectItem>
                <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                <SelectItem value="claude-3">Claude 3</SelectItem>
                <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="region"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Region</FormLabel>
            <FormControl>
              <Input placeholder="us-east-1" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );

  const renderStorageFields = () => (
    <>
      <FormField
        control={form.control}
        name="endpoint"
        rules={{ required: "Endpoint is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Storage Endpoint</FormLabel>
            <FormControl>
              <Input placeholder="https://mystorageaccount.blob.core.windows.net" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="accessKey"
        rules={{ required: "Access Key is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Access Key</FormLabel>
            <FormControl>
              <Input type="password" placeholder="Access key" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="secretKey"
        rules={{ required: "Secret Key is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Secret Key</FormLabel>
            <FormControl>
              <Input type="password" placeholder="Secret key" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="bucket"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Container/Bucket</FormLabel>
            <FormControl>
              <Input placeholder="my-container" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );

  const renderSearchFields = () => (
    <>
      <FormField
        control={form.control}
        name="endpoint"
        rules={{ required: "Endpoint is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Search Endpoint</FormLabel>
            <FormControl>
              <Input placeholder="https://mysearch.search.windows.net" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="apiKey"
        rules={{ required: "API Key is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Admin API Key</FormLabel>
            <FormControl>
              <Input type="password" placeholder="Admin key" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="index"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Search Index</FormLabel>
            <FormControl>
              <Input placeholder="documents-index" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );

  const renderIntegrationFields = () => (
    <>
      <FormField
        control={form.control}
        name="endpoint"
        rules={{ required: "Endpoint is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Service Endpoint</FormLabel>
            <FormControl>
              <Input placeholder="https://graph.microsoft.com" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="clientId"
        rules={{ required: "Client ID is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Client ID</FormLabel>
            <FormControl>
              <Input placeholder="Application ID" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="clientSecret"
        rules={{ required: "Client Secret is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Client Secret</FormLabel>
            <FormControl>
              <Input type="password" placeholder="Client secret" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="tenantId"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Tenant ID</FormLabel>
            <FormControl>
              <Input placeholder="Tenant ID" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );

  const renderAnalyticsFields = () => (
    <>
      <FormField
        control={form.control}
        name="endpoint"
        rules={{ required: "Endpoint is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Analytics Endpoint</FormLabel>
            <FormControl>
              <Input placeholder="https://api.powerbi.com" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="apiKey"
        rules={{ required: "API Key is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>API Key</FormLabel>
            <FormControl>
              <Input type="password" placeholder="API key" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="workspace"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Workspace</FormLabel>
            <FormControl>
              <Input placeholder="workspace-id" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );

  const renderMonitoringFields = () => (
    <>
      <FormField
        control={form.control}
        name="endpoint"
        rules={{ required: "Endpoint is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Monitoring Endpoint</FormLabel>
            <FormControl>
              <Input placeholder="https://api.applicationinsights.io" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="instrumentationKey"
        rules={{ required: "Instrumentation Key is required" }}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Instrumentation Key</FormLabel>
            <FormControl>
              <Input type="password" placeholder="Instrumentation key" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      <FormField
        control={form.control}
        name="resourceGroup"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Resource Group</FormLabel>
            <FormControl>
              <Input placeholder="my-resource-group" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );

  const renderServiceSpecificFields = () => {
    switch (service.type) {
      case 'Database':
        return renderDatabaseFields();
      case 'AI Platform':
        return renderAIFields();
      case 'Storage':
        return renderStorageFields();
      case 'Search Engine':
        return renderSearchFields();
      case 'Integration':
        return renderIntegrationFields();
      case 'Analytics':
        return renderAnalyticsFields();
      case 'Monitoring':
        return renderMonitoringFields();
      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline" className="text-xs h-8 px-3">
          <Settings className="h-3 w-3 mr-1" />
          Configure
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure {service.name}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {renderServiceSpecificFields()}
            
            <FormField
              control={form.control}
              name="timeout"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Timeout (seconds)</FormLabel>
                  <FormControl>
                    <Input type="number" placeholder="30" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <div className="flex justify-end space-x-2 pt-4">
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Save Configuration</Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}