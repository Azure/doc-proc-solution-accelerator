import React, { useState, useMemo, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { StepCatalogDefinition, StepInstanceCreateRequest, stepsApi, servicesApi, ServiceInstance, ErrorWithData } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface CreateStepInstanceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  stepCatalogDefinition: StepCatalogDefinition;
  onStepInstanceCreated: () => void;
}

const CreateStepInstanceDialog = ({ 
  isOpen, 
  onClose, 
  stepCatalogDefinition: stepCatalog, 
  onStepInstanceCreated 
}: CreateStepInstanceDialogProps) => {
  const [loading, setLoading] = useState(false);
  const [serviceInstances, setServiceInstances] = useState<ServiceInstance[]>([]);
  const [loadingServices, setLoadingServices] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const { toast } = useToast();
  
  const [formData, setFormData] = useState<StepInstanceCreateRequest>(() => {
    // Initialize with default values from settings schema
    const defaultSettings: Record<string, any> = {};
    if (stepCatalog.settings_schema) {
      Object.entries(stepCatalog.settings_schema).forEach(([key, schema]) => {
        if (schema.default !== undefined) {
          defaultSettings[key] = schema.default;
        }
      });
    }
    
    return {
      name: "",
      description: "",
      step_catalog_id: stepCatalog.id,
      settings: defaultSettings,
      enabled: true,
      fail_pipeline_on_error: false,
      timeout: 30,
      services: [],
      condition: "",
      debug_mode: false,
    };
  });

  // Generate dynamic form fields based on settings schema
  const settingsFields = useMemo(() => {
    if (!stepCatalog.settings_schema) return [];
    
    return Object.entries(stepCatalog.settings_schema).map(([key, schema]) => ({
      key,
      ...schema,
    }));
  }, [stepCatalog.settings_schema]);

  // Fetch service instances when dialog opens and when it has service-type fields
  useEffect(() => {
    const hasServiceFields = settingsFields.some(field => 
      field.ui_component === 'service_selector' || field.service_type
    );

    if (isOpen && hasServiceFields) {
      const loadServiceInstances = async () => {
        setLoadingServices(true);
        try {
          const instances = await servicesApi.getInstances();
          setServiceInstances(instances);
        } catch (error) {
          console.error('Error loading service instances:', error);
          toast({
            title: "Warning",
            description: "Failed to load service instances. Service dropdowns may not work correctly.",
            variant: "destructive",
          });
        } finally {
          setLoadingServices(false);
        }
      };

      loadServiceInstances();
    }
  }, [isOpen, settingsFields, toast]);

  // Initialize settings with default values from schema
  const initializeSettingsWithDefaults = useMemo(() => {
    const defaultSettings: Record<string, any> = {};
    if (stepCatalog.settings_schema) {
      Object.entries(stepCatalog.settings_schema).forEach(([key, schema]) => {
        if (schema.default !== undefined) {
          defaultSettings[key] = schema.default;
        }
      });
    }
    return defaultSettings;
  }, [stepCatalog.settings_schema]);

  // Reset form when dialog is closed or step catalog changes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        name: "",
        description: "",
        step_catalog_id: stepCatalog.id,
        settings: initializeSettingsWithDefaults,
        enabled: true,
        fail_pipeline_on_error: false,
        timeout: 30,
        services: [], // Reset services array
        condition: "",
        debug_mode: false,
      });
      setServiceInstances([]); // Clear service instances
      setFieldErrors({}); // Clear field errors
    }
  }, [isOpen, stepCatalog.id, initializeSettingsWithDefaults]);

  const handleInputChange = (field: keyof StepInstanceCreateRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (fieldErrors[field as string]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field as string];
        return newErrors;
      });
    }
  };

  const handleSettingChange = (key: string, value: any) => {
    setFormData(prev => {
      const newFormData = {
        ...prev,
        settings: { ...prev.settings, [key]: value }
      };

      // If this is a service selector field, also add/update the services array
      const field = settingsFields.find(f => f.key === key);
      if (field && (field.ui_component === 'service_selector' || field.service_type)) {
        if (value && !newFormData.services.includes(value)) {
          // Add service ID to services array if it's not already there
          newFormData.services = [...newFormData.services, value];
        } else if (!value) {
          // Remove service ID from services array if value is cleared
          newFormData.services = newFormData.services.filter(serviceId => {
            // Keep services that are still being used by other service selector fields
            const otherServiceFields = settingsFields.filter(f => 
              f.key !== key && (f.ui_component === 'service_selector' || f.service_type)
            );
            return otherServiceFields.some(otherField => 
              newFormData.settings[otherField.key] === serviceId
            );
          });
        }
      }

      return newFormData;
    });
    
    // Clear error for this setting field when user starts typing
    const errorKey = `settings.${key}`;
    if (fieldErrors[errorKey]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[errorKey];
        return newErrors;
      });
    }
  };

  const handleArrayFieldChange = (field: keyof StepInstanceCreateRequest, values: string[]) => {
    setFormData(prev => ({ ...prev, [field]: values }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear previous errors
    setFieldErrors({});
    
    // Collect all validation errors
    const errors: Record<string, string> = {};
    
    // Check basic required fields
    if (!formData.name.trim()) {
      errors.name = "Step instance name is required";
    } else {
      // Validate name format - only letters, numbers, underscores, and hyphens
      const namePattern = /^[a-zA-Z0-9_-]+$/;
      if (!namePattern.test(formData.name.trim())) {
        errors.name = "Step instance name can only contain letters, numbers, underscores (_), and hyphens (-)";
      }
    }
    
    // Check required settings fields
    settingsFields.forEach(field => {
      if (field.required) {
        const value = formData.settings[field.key];
        const fieldLabel = field.title || field.key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        if (value === undefined || value === null || value === '') {
          if (field.ui_component === 'service_selector' || field.service_type) {
            errors[`settings.${field.key}`] = `${fieldLabel} service must be selected`;
          } else {
            errors[`settings.${field.key}`] = `${fieldLabel} is required`;
          }
        }
      }
    });

    // If there are validation errors, set them and return
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setLoading(true);
    
    try {
      // Debug log to verify all settings are included
      console.log('Creating step instance with data:', formData);
      
      await stepsApi.createInstance(formData);
      
      toast({
        title: "Success",
        description: "Step instance created successfully",
      });
      onStepInstanceCreated();
    
    } catch (error) {
      console.error('Error creating step instance:', error);
      const errorMessage = error instanceof ErrorWithData ? error?.details : 'Unknown error occurred';
    
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const renderSettingField = (field: { key: string; type: string; title?: string; description?: string; required?: boolean; default?: any; enum?: string[]; min?: number; max?: number; pattern?: string; ui_component?: string; service_type?: string }) => {
    const value = formData.settings[field.key] ?? field.default ?? '';
    const label = field.title || field.key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    const errorKey = `settings.${field.key}`;
    const hasError = !!fieldErrors[errorKey];

    // Handle service selector fields first (before type-based switch)
    if (field.ui_component === 'service_selector' || field.service_type) {
      const filteredServices = serviceInstances.filter(service => 
        !field.service_type || service.type === field.service_type
      );

      return (
        <div key={field.key} className="space-y-2">
          <Label htmlFor={field.key}>
            {label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
          <Select 
            value={value} 
            onValueChange={(newValue) => handleSettingChange(field.key, newValue)}
            disabled={loadingServices}
          >
            <SelectTrigger className={hasError ? "border-red-500" : ""}>
              <SelectValue 
                placeholder={
                  loadingServices 
                    ? "Loading services..." 
                    : filteredServices.length === 0 
                      ? `No ${field.service_type || 'services'} available`
                      : `Select ${label.toLowerCase()}`
                } 
              />
            </SelectTrigger>
            <SelectContent>
              {filteredServices.map((service) => (
                <SelectItem key={service.id} value={service.id}>
                  <div className="flex flex-col text-left">
                    <span>{service.name}</span>
                    {service.description && (
                      <span className="text-xs text-muted-foreground">{service.description}</span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {hasError && (
            <p className="text-sm text-red-500">{fieldErrors[errorKey]}</p>
          )}
          {!hasError && field.description && (
            <p className="text-sm text-muted-foreground">{field.description}</p>
          )}
          {!hasError && field.service_type && (
            <p className="text-xs text-muted-foreground">
              Service type: {field.service_type} • Found {filteredServices.length} service(s)
            </p>
          )}
          {!hasError && field.required && filteredServices.length === 0 && !loadingServices && (
            <p className="text-xs text-yellow-600 dark:text-yellow-400">
              ⚠️ No services of type "{field.service_type}" are available. Please create a service instance first.
            </p>
          )}
        </div>
      );
    }

    switch (field.ui_component) {
      
      case 'select':
      case 'enum':
        return (
          <div key={field.key} className="space-y-2">
            <Label htmlFor={field.key}>
              {label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Select value={value} onValueChange={(newValue) => handleSettingChange(field.key, newValue)}>
              <SelectTrigger className={hasError ? "border-red-500" : ""}>
                <SelectValue placeholder={`Select ${label.toLowerCase()}`} />
              </SelectTrigger>
              <SelectContent>
                {field.enum?.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {hasError && (
              <p className="text-sm text-red-500">{fieldErrors[errorKey]}</p>
            )}
            {!hasError && field.description && (
              <p className="text-sm text-muted-foreground">{field.description}</p>
            )}
          </div>
        );

      case 'textarea':
        return (
          <div key={field.key} className="space-y-2">
            <Label htmlFor={field.key}>
              {label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Textarea
              id={field.key}
              value={value}
              onChange={(e) => handleSettingChange(field.key, e.target.value)}
              placeholder={`Enter ${label.toLowerCase()}`}
              rows={4}
              className={hasError ? "border-red-500" : ""}
            />
            {hasError && (
              <p className="text-sm text-red-500">{fieldErrors[errorKey]}</p>
            )}
            {!hasError && field.description && (
              <p className="text-sm text-muted-foreground">{field.description}</p>
            )}
          </div>
        );

      case 'password':
        return (
          <div key={field.key} className="space-y-2">
            <Label htmlFor={field.key}>
              {label}
              {field.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Input
              id={field.key}
              type="password"
              value={value}
              onChange={(e) => handleSettingChange(field.key, e.target.value)}
              placeholder={`Enter ${label.toLowerCase()}`}
              className={hasError ? "border-red-500" : ""}
            />
            {hasError && (
              <p className="text-sm text-red-500">{fieldErrors[errorKey]}</p>
            )}
            {!hasError && field.description && (
              <p className="text-sm text-muted-foreground">{field.description}</p>
            )}
          </div>
        );

      default: // input ui_component and fallback
        if (field.type === 'boolean') {
          return (
            <div key={field.key} className="space-y-2">
              <div className="flex items-center space-x-2">
                <Switch
                  id={field.key}
                  checked={Boolean(value)}
                  onCheckedChange={(checked) => handleSettingChange(field.key, checked)}
                />
                <Label htmlFor={field.key}>{label}</Label>
                {field.required && <span className="text-red-500">*</span>}
              </div>
              {hasError && (
                <p className="text-sm text-red-500">{fieldErrors[errorKey]}</p>
              )}
              {!hasError && field.description && (
                <p className="text-sm text-muted-foreground">{field.description}</p>
              )}
            </div>
          );
        } else if (field.type === 'number' || field.type === 'integer') {
          return (
            <div key={field.key} className="space-y-2">
              <Label htmlFor={field.key}>
                {label}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              <Input
                id={field.key}
                type="number"
                value={value}
                min={field.min}
                max={field.max}
                step={field.type === 'integer' ? 1 : 0.1}
                onChange={(e) => handleSettingChange(field.key, field.type === 'integer' ? parseInt(e.target.value) || 0 : parseFloat(e.target.value) || 0)}
                placeholder={`Enter ${label.toLowerCase()}`}
                className={hasError ? "border-red-500" : ""}
              />
              {hasError && (
                <p className="text-sm text-red-500">{fieldErrors[errorKey]}</p>
              )}
              {!hasError && field.description && (
                <p className="text-sm text-muted-foreground">{field.description}</p>
              )}
            </div>
          );
        } else { // Default to string input
          return (
            <div key={field.key} className="space-y-2">
              <Label htmlFor={field.key}>
                {label}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              <Input
                id={field.key}
                type="text"
                value={value}
                pattern={field.pattern}
                onChange={(e) => handleSettingChange(field.key, e.target.value)}
                placeholder={`Enter ${label.toLowerCase()}`}
                className={hasError ? "border-red-500" : ""}
              />
              {hasError && (
                <p className="text-sm text-red-500">{fieldErrors[errorKey]}</p>
              )}
              {!hasError && field.description && (
                <p className="text-sm text-muted-foreground">{field.description}</p>
              )}
            </div>
          );  
        }
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Step Instance: {stepCatalog.name}</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Basic Information</h3>
            
            <div className="space-y-2">
              <Label htmlFor="name">Name <span className="text-red-500">*</span></Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="Enter step instance name"
                pattern="[a-zA-Z0-9_-]+"
                title="Only letters, numbers, underscores (_), and hyphens (-) are allowed"
                required
                className={fieldErrors.name ? "border-red-500" : ""}
              />
              {fieldErrors.name && (
                <p className="text-sm text-red-500">{fieldErrors.name}</p>
              )}
              {!fieldErrors.name && (
                <p className="text-sm text-muted-foreground">
                  Only letters, numbers, underscores (_), and hyphens (-) are allowed
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Enter step instance description (optional)"
                rows={2}
              />
            </div>
          </div>

          {/* Execution Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Execution Settings</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="enabled"
                    checked={formData.enabled}
                    onCheckedChange={(checked) => handleInputChange('enabled', checked)}
                  />
                  <Label htmlFor="enabled">Enabled</Label>
                </div>
                <p className="text-sm text-muted-foreground">Whether this step is active</p>
              </div>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="fail_pipeline"
                    checked={formData.fail_pipeline_on_error}
                    onCheckedChange={(checked) => handleInputChange('fail_pipeline_on_error', checked)}
                  />
                  <Label htmlFor="fail_pipeline">Fail Pipeline on Error</Label>
                </div>
                <p className="text-sm text-muted-foreground">Stop pipeline if this step fails</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="timeout">Timeout (seconds)</Label>
                <Input
                  id="timeout"
                  type="number"
                  value={formData.timeout}
                  onChange={(e) => handleInputChange('timeout', parseInt(e.target.value) || 600)}
                  min={1}
                  placeholder="600"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="debug_mode"
                    checked={formData.debug_mode}
                    onCheckedChange={(checked) => handleInputChange('debug_mode', checked)}
                  />
                  <Label htmlFor="debug_mode">Debug Mode</Label>
                </div>
                <p className="text-sm text-muted-foreground">Enable detailed logging</p>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="condition">Condition (optional)</Label>
              <Input
                id="condition"
                value={formData.condition}
                onChange={(e) => handleInputChange('condition', e.target.value)}
                placeholder="Python expression to control execution"
              />
              <p className="text-sm text-muted-foreground">
                Optional condition to control when this step should execute
              </p>
            </div>
          </div>

          {/* Step-specific Settings */}
          {settingsFields.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Step Configuration</h3>
              <div className="space-y-4">
                {settingsFields.map(renderSettingField)}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Instance
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateStepInstanceDialog;