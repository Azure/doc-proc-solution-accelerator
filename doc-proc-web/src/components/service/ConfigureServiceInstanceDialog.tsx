import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useForm } from "react-hook-form";
import { Settings2 } from "lucide-react";
import { ServiceInstance } from "@/lib/api";

interface ConfigureServiceInstanceDialogProps {
  instance: ServiceInstance;
  onUpdateService: (instanceId: string, config: any) => void;
  triggerButton?: React.ReactElement;
}

interface ServiceConfigFormData {
  name: string;
  description: string;
  settings: Record<string, any>;
}

export function ConfigureServiceInstanceDialog({ instance, onUpdateService, triggerButton }: ConfigureServiceInstanceDialogProps) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const form = useForm<ServiceConfigFormData>({
    defaultValues: {
      name: instance.name || "",
      description: instance.description || "",
      settings: instance.settings || {},
    },
  });

  const onSubmit = async (data: ServiceConfigFormData) => {
    try {
      setLoading(true);
      await onUpdateService(instance.id, {
        description: data.description,
        settings: data.settings,
      });
      setOpen(false);
      form.reset();
    } catch (error) {
      console.error('Failed to update service instance:', error);
    } finally {
      setLoading(false);
    }
  };

  // Dynamic form fields based on the service type and existing settings
  const renderSettingsFields = () => {
    const settings = instance.settings || {};
    const settingsSchema = instance.catalog_definition?.settings_schema;
    
    if (!settingsSchema) {
      // Generic text area for settings if no schema is available
      return (
        <FormField
          control={form.control}
          name="settings"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Settings (JSON)</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Enter configuration as JSON..."
                  className="min-h-[120px]"
                  value={JSON.stringify(field.value, null, 2)}
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value);
                      field.onChange(parsed);
                    } catch {
                      // Keep the text value for now
                    }
                  }}
                />
              </FormControl>
              <FormDescription>
                Configuration settings for this service instance
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
      );
    }

    // Render fields based on schema (simplified version)
    return Object.entries(settings).map(([key, value]) => (
      <FormField
        key={key}
        control={form.control}
        name={`settings.${key}` as any}
        render={({ field }) => (
          <FormItem>
            <FormLabel className="capitalize">{key.replace(/_/g, ' ')}</FormLabel>
            <FormControl>
              {typeof value === 'boolean' ? (
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              ) : typeof value === 'number' ? (
                <Input
                  type="number"
                  placeholder={`Enter ${key}...`}
                  value={field.value || ''}
                  onChange={(e) => field.onChange(Number(e.target.value) || '')}
                />
              ) : (
                <Input
                  placeholder={`Enter ${key}...`}
                  value={field.value || ''}
                  onChange={field.onChange}
                />
              )}
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    ));
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {triggerButton || (
          <Button variant="outline">
            <Settings2 className="h-4 w-4 mr-2" />
            Configure
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure {instance.name}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* Basic Information */}
            <div className="grid gap-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Instance Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter instance name..." {...field} disabled />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Enter description..."
                        className="min-h-[80px]"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Service Information */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium mb-3">Service Information</h3>
              <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                <div>
                  <span className="font-medium">Type:</span> {instance.type}
                </div>
                <div>
                  <span className="font-medium">Category:</span> {instance.category || 'N/A'}
                </div>
                <div>
                  <span className="font-medium">Version:</span> {instance.version || 'N/A'}
                </div>
                <div>
                  <span className="font-medium">Status:</span> {instance.status || 'Unknown'}
                </div>
              </div>
            </div>

            {/* Configuration Settings */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium mb-3">Configuration Settings</h3>
              <div className="space-y-4">
                {renderSettingsFields()}
              </div>
            </div>

            {/* Connection Status */}
            {instance.connection_status && (
              <div className="border-t pt-4">
                <h3 className="text-sm font-medium mb-3">Connection Status</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Status:</span>{' '}
                    <span className={`capitalize ${
                      instance.connection_status.status === 'connected' ? 'text-green-600' :
                      instance.connection_status.status === 'error' ? 'text-red-600' :
                      'text-yellow-600'
                    }`}>
                      {instance.connection_status.status}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Last Tested:</span>{' '}
                    {instance.connection_status.last_tested 
                      ? new Date(instance.connection_status.last_tested).toLocaleString()
                      : 'Never'
                    }
                  </div>
                  {instance.connection_status.test_duration_ms && (
                    <div>
                      <span className="font-medium">Duration:</span> {instance.connection_status.test_duration_ms}ms
                    </div>
                  )}
                  {instance.connection_status.error_message && (
                    <div className="col-span-2">
                      <span className="font-medium">Error:</span>{' '}
                      <span className="text-red-600">{instance.connection_status.error_message}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}