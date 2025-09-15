
import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { Plus } from "lucide-react";
import { servicesApi, ServiceCatalogDefinition } from "@/lib/api";
import { ServiceIcon } from "@/components/service/ServiceIcon";

interface AddServiceInstanceFormData {
  name: string;
  service_catalog_id: string;
  description: string;
  settings: Record<string, any>;
}

interface AddServiceInstanceDialogProps {
  onAddService: (service: AddServiceInstanceFormData) => void;
  selectedService?: ServiceCatalogDefinition; // Pre-selected service from catalog
  triggerButton?: React.ReactElement; // Custom trigger button
}

export function AddServiceInstanceDialog({ onAddService, selectedService, triggerButton }: AddServiceInstanceDialogProps) {
  const [open, setOpen] = useState(false);
  const [catalog, setCatalog] = useState<ServiceCatalogDefinition[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCatalogService, setSelectedCatalogService] = useState<ServiceCatalogDefinition | null>(selectedService || null);

  const form = useForm<AddServiceInstanceFormData>({
    defaultValues: {
      name: selectedService ? `${selectedService.name} Instance`.replace(/\s+/g, '_') : "",
      service_catalog_id: selectedService?.id || "",
      description: selectedService ? `Instance of ${selectedService.name}` : "",
      settings: {},
    },
  });

  // Load service catalog when dialog opens (only if no service is pre-selected)
  useEffect(() => {
    if (open && !selectedService) {
      loadCatalog();
    }
  }, [open, selectedService]);

  // Update selected catalog service when form value changes
  useEffect(() => {
    const catalogId = form.watch('service_catalog_id');
    if (catalogId && catalog.length > 0) {
      const service = catalog.find(s => s.id === catalogId);
      setSelectedCatalogService(service || null);
    } else if (selectedService) {
      setSelectedCatalogService(selectedService);
    }
  }, [form.watch('service_catalog_id'), catalog, selectedService]);

  const loadCatalog = async () => {
    try {
      setLoading(true);
      const catalogData = await servicesApi.getCatalog();
      setCatalog(catalogData);
    } catch (error) {
      console.error('Failed to load service catalog:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (data: AddServiceInstanceFormData) => {
    onAddService(data);
    setOpen(false);
    form.reset();
  };

  const renderSettingsFields = () => {
    if (!selectedCatalogService?.settings_schema) {
      return null;
    }

    return (
      <div className="space-y-4">
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium mb-3">Service Settings</h4>
          {Object.entries(selectedCatalogService.settings_schema).map(([key, schema]) => (
            <FormField
              key={key}
              control={form.control}
              name={`settings.${key}`}
              rules={{ 
                required: schema.required ? `${schema.title || key} is required` : false 
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="capitalize">
                    {schema.title || key.replace(/_/g, ' ')}
                    {schema.required && <span className="text-red-500 ml-1">*</span>}
                  </FormLabel>
                  <FormControl>
                    {renderSettingField(key, schema, field)}
                  </FormControl>
                  {schema.description && (
                    <FormDescription>{schema.description}</FormDescription>
                  )}
                  <FormMessage />
                </FormItem>
              )}
            />
          ))}
        </div>
      </div>
    );
  };

  const renderSettingField = (key: string, schema: any, field: any) => {
    const { type, enum: enumValues, sensitive, default: defaultValue } = schema;

    // Set default value if not already set
    if (field.value === undefined && defaultValue !== undefined) {
      field.onChange(defaultValue);
    }

    switch (type) {
      case 'boolean':
        return (
          <div className="flex items-center space-x-2">
            <Switch
              checked={field.value || false}
              onCheckedChange={field.onChange}
            />
            <span className="text-sm">{field.value ? 'Enabled' : 'Disabled'}</span>
          </div>
        );

      case 'integer':
      case 'number':
        return (
          <Input
            type="number"
            placeholder={`Enter ${key.replace(/_/g, ' ')}`}
            {...field}
            onChange={(e) => field.onChange(type === 'integer' ? parseInt(e.target.value) : parseFloat(e.target.value))}
            min={schema.minimum}
            max={schema.maximum}
          />
        );

      case 'string':
        if (enumValues && enumValues.length > 0) {
          return (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger>
                <SelectValue placeholder={`Select ${key.replace(/_/g, ' ')}`} />
              </SelectTrigger>
              <SelectContent>
                {enumValues.map((value: string) => (
                  <SelectItem key={value} value={value}>
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          );
        }

        if (key.toLowerCase().includes('description') || key.toLowerCase().includes('notes')) {
          return (
            <Textarea
              placeholder={`Enter ${key.replace(/_/g, ' ')}`}
              {...field}
            />
          );
        }

        return (
          <Input
            type={sensitive ? 'password' : 'text'}
            placeholder={`Enter ${key.replace(/_/g, ' ')}`}
            {...field}
            pattern={schema.pattern}
          />
        );

      default:
        return (
          <Input
            type="text"
            placeholder={`Enter ${key.replace(/_/g, ' ')}`}
            {...field}
          />
        );
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {triggerButton || (
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Service
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            <div className="flex items-center gap-2">
              {selectedService && (
                <ServiceIcon 
                  iconName={selectedService.ui_metadata?.icon} 
                  category={selectedService.category}
                  type={selectedService.type}
                  className="h-5 w-5" 
                />
              )}
              {selectedService ? `Create ${selectedService.name} Instance` : 'Add New Service'}
            </div>
          </DialogTitle>
          {selectedService?.ui_metadata?.description_short && (
            <p className="text-sm text-muted-foreground">
              {selectedService.ui_metadata.description_short}
            </p>
          )}
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              rules={{ required: "Service name is required", pattern: { value: /^[a-zA-Z0-9_]+$/, message: "Name can only contain letters, numbers, and underscores" } }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Instance Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Enter service instance name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {!selectedService && (
              <FormField
                control={form.control}
                name="service_catalog_id"
                rules={{ required: "Please select a service type" }}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Service Type</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder={loading ? "Loading services..." : "Select service type"} />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {catalog.map((service) => (
                          <SelectItem key={service.id} value={service.id}>
                            <div className="flex items-center space-x-2">
                              <ServiceIcon 
                                iconName={service.ui_metadata?.icon}
                                category={service.category}
                                type={service.type}
                                className="h-4 w-4" 
                              />
                              <span>{service.name}</span>
                              <span className="text-xs text-muted-foreground">({service.type})</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Enter service instance description (optional)" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Render settings fields based on schema */}
            {renderSettingsFields()}

            {selectedCatalogService?.ui_metadata?.description_long && (
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium mb-2">About this service</h4>
                <p className="text-sm text-muted-foreground">
                  {selectedCatalogService.ui_metadata.description_long}
                </p>
              </div>
            )}

            <div className="flex justify-end space-x-2 border-t pt-4">
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                Create Instance
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}