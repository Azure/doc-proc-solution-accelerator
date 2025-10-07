import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { Loader2 } from "lucide-react";
import { SourceInstance, SourceInstanceUpdateRequest, sourcesApi, ErrorWithData } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { CrawlerSettingsFields } from "@/components/source/CrawlerSettingsFields";
import { SourceSettingsFields } from "@/components/source/SourceSettingsFields";

interface ConfigureSourceInstanceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  sourceInstance: SourceInstance;
  onInstanceUpdated: () => void;
}

interface SourceConfigFormData {
  name: string;
  description: string;
  enabled: boolean;
  test_connection: boolean;
  settings: Record<string, any>;
  crawler_settings: Record<string, any>;
}

const ConfigureSourceInstanceDialog = ({ 
  isOpen, 
  onClose, 
  sourceInstance, 
  onInstanceUpdated 
}: ConfigureSourceInstanceDialogProps) => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const form = useForm<SourceConfigFormData>({
    defaultValues: {
      name: sourceInstance.name || "",
      description: sourceInstance.description || "",
      enabled: sourceInstance.enabled || false,
      test_connection: sourceInstance.test_connection || false,
      settings: sourceInstance.settings || {},
      crawler_settings: sourceInstance.crawler_settings || {},
    },
  });

  const onSubmit = async (data: SourceConfigFormData) => {
    try {
      setLoading(true);
      
      const updateData: SourceInstanceUpdateRequest = {
        name: data.name,
        description: data.description,
        enabled: data.enabled,
        test_connection: data.test_connection,
        settings: data.settings,
        crawler_settings: data.crawler_settings,
      };
      
      await sourcesApi.updateInstance(sourceInstance.id, updateData);
      
      toast({
        title: "Success",
        description: "Source instance updated successfully",
      });
      
      onInstanceUpdated();
      onClose();
    } catch (error) {
      console.error('Error updating source instance:', error);
      const errorMessage = error instanceof ErrorWithData ? error.details || error.message : 'Unknown error occurred';
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };



  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Configure {sourceInstance.name}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                rules={{ required: "Instance name is required" }}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Instance Name *</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter instance name..." {...field} />
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

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="enabled"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                      <div className="space-y-0.5">
                        <FormLabel>Enable Instance</FormLabel>
                        <FormDescription className="text-xs">
                          Enable this source instance for use
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="test_connection"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                      <div className="space-y-0.5">
                        <FormLabel>Test Connection</FormLabel>
                        <FormDescription className="text-xs">
                          Test connection when validating
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>
            </div>

            {/* Source Information */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium mb-3">Source Information</h3>
              <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                <div>
                  <span className="font-medium">Type:</span> {sourceInstance.catalog_definition?.type || 'Unknown'}
                </div>
                <div>
                  <span className="font-medium">Category:</span> {sourceInstance.catalog_definition?.category || 'N/A'}
                </div>
                <div>
                  <span className="font-medium">Version:</span> {sourceInstance.catalog_definition?.version || 'N/A'}
                </div>
                <div>
                  <span className="font-medium">Catalog ID:</span> {sourceInstance.source_catalog_id}
                </div>
              </div>
            </div>

            {/* Configuration Settings */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium mb-3">Source Settings</h3>
              <SourceSettingsFields 
                control={form.control} 
                fieldPrefix="settings"
                settingsSchema={sourceInstance.catalog_definition?.settings_schema}
                fallbackToJson={true}
              />
            </div>

            {/* Crawler Settings */}
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium mb-3">Crawler Settings</h3>
              <CrawlerSettingsFields control={form.control} fieldPrefix="crawler_settings" />
            </div>

            {/* Connection Status */}
            {sourceInstance.status && (
              <div className="border-t pt-4">
                <h3 className="text-sm font-medium mb-3">Connection Status</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Status:</span>{' '}
                    <span className={`capitalize ${
                      sourceInstance.status.status === 'connected' ? 'text-green-600' :
                      sourceInstance.status.status === 'error' ? 'text-red-600' :
                      'text-yellow-600'
                    }`}>
                      {sourceInstance.status.status}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Last Tested:</span>{' '}
                    {sourceInstance.status.tested_at 
                      ? new Date(sourceInstance.status.tested_at).toLocaleString()
                      : 'Never'
                    }
                  </div>
                  {sourceInstance.status.message && (
                    <div className="col-span-2">
                      <span className="font-medium">Message:</span>{' '}
                      <span className={sourceInstance.status.status === 'error' ? 'text-red-600' : ''}>
                        {sourceInstance.status.message}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-2 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Save Changes
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export default ConfigureSourceInstanceDialog;