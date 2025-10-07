import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { Loader2 } from "lucide-react";
import { 
  SourceCatalogDefinition, 
  SourceInstanceCreateRequest, 
  sourcesApi, 
  ErrorWithData 
} from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { CrawlerSettingsFields } from "@/components/source/CrawlerSettingsFields";
import { SourceSettingsFields } from "@/components/source/SourceSettingsFields";

interface CreateSourceInstanceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  sourceCatalogDefinition: SourceCatalogDefinition;
  onSourceInstanceCreated: () => void;
}

const CreateSourceInstanceDialog = ({ 
  isOpen, 
  onClose, 
  sourceCatalogDefinition: sourceCatalog, 
  onSourceInstanceCreated 
}: CreateSourceInstanceDialogProps) => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const form = useForm<SourceInstanceCreateRequest>({
    defaultValues: {
      name: `${sourceCatalog.name} Instance`.replace(/\s+/g, '_'),
      source_catalog_id: sourceCatalog.id,
      description: `Instance of ${sourceCatalog.name}`,
      settings: {},
      crawler_settings: {},
      enabled: true,
      test_connection: true,
    },
  });

  // Set default values in form when a source is selected
  useEffect(() => {
    if (sourceCatalog?.settings_schema) {
      const defaultSettings: Record<string, any> = {};
      
      Object.entries(sourceCatalog.settings_schema).forEach(([key, schema]) => {
        if (schema.default !== undefined) {
          defaultSettings[key] = schema.default;
        }
      });

      // Update form with default values if we have any
      if (Object.keys(defaultSettings).length > 0) {
        const currentSettings = form.getValues('settings');
        const updatedSettings = { ...defaultSettings, ...currentSettings };
        form.setValue('settings', updatedSettings);
      }
    }
  }, [sourceCatalog, form]);

  // Reset form when dialog is closed
  useEffect(() => {
    if (!isOpen) {
      form.reset({
        name: `${sourceCatalog.name} Instance`.replace(/\s+/g, '_'),
        source_catalog_id: sourceCatalog.id,
        description: `Instance of ${sourceCatalog.name}`,
        settings: {},
        crawler_settings: {},
        enabled: true,
        test_connection: true,
      });
    }
  }, [isOpen, sourceCatalog, form]);

  const onSubmit = async (data: SourceInstanceCreateRequest) => {
    try {
      setLoading(true);
      await sourcesApi.createInstance(data);
      
      toast({
        title: "Success",
        description: "Source instance created successfully",
      });
      
      onSourceInstanceCreated();
      onClose();
    } catch (error) {
      console.error('Error creating source instance:', error);
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
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Source Instance</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              rules={{ 
                required: "Source instance name is required",
                pattern: {
                  value: /^[a-zA-Z0-9_-]+$/,
                  message: "Name can only contain letters, numbers, underscores, and hyphens"
                }
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Instance Name *</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter source instance name" {...field} />
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
                      placeholder="Enter source instance description"
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
                        Test connection on creation
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

            <div className="space-y-4">
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium mb-3">Source Settings</h4>
                <SourceSettingsFields 
                  control={form.control} 
                  fieldPrefix="settings"
                  settingsSchema={sourceCatalog?.settings_schema}
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium mb-3">Crawler Settings</h4>
                <CrawlerSettingsFields control={form.control} fieldPrefix="crawler_settings" />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-4 border-t">
              <Button type="button" variant="outline" onClick={onClose} disabled={loading}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Create Source Instance
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateSourceInstanceDialog;