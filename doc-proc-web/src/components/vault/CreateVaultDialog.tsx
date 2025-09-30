import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Database, Settings, Workflow } from "lucide-react";
import { 
  type Pipeline, 
  type VaultCreateRequest,
  type StorageConfig,
  type DocumentProcessingConfig,
  pipelinesApi,
  ErrorWithData
} from "@/lib/api";


interface CreateVaultDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateVault: (request: VaultCreateRequest) => Promise<void>;
  loading?: boolean;
}

interface FormErrors {
  name?: string;
  pipeline_name?: string;
  storage_config?: {
    account_name?: string;
    container_name?: string;
    credential_type?: string;
    connection_string?: string;
  };
}

const CreateVaultDialog = ({ 
  open, 
  onOpenChange, 
  onCreateVault,
  loading = false 
}: CreateVaultDialogProps) => {
  const { toast } = useToast();
  // Pipeline state
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [pipelinesLoading, setPipelinesLoading] = useState(false);

  const [formData, setFormData] = useState<VaultCreateRequest>({
    name: "",
    description: "",
    pipeline_name: "",
    processing_config: {
      auto_process_documents: true,
      supported_formats: ["pdf", "docx", "pptx", "excel"]
    },
    storage_config: {
      account_name: "",
      container_name: "vaults",
      credential_type: "default_azure_credential",
      connection_string: ""
    },
    metadata: {}
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [useCustomStorage, setUseCustomStorage] = useState(false);

  // Load pipelines when dialog opens
  useEffect(() => {
    if (open && pipelines.length === 0) {
      loadPipelines();
    }
  }, [open]);

  const loadPipelines = async () => {
    try {
      setPipelinesLoading(true);
      const pipelinesData = await pipelinesApi.getPipelines();
      setPipelines(pipelinesData);
    } catch (error) {
      console.error('Error loading pipelines:', error);

      const errMessage = error instanceof ErrorWithData ? error.details.message : 'Unknown error';
      toast({
        title: "Error",
        description: `Failed to load pipelines. ${errMessage}`,
        variant: "destructive",
      });
    } finally {
      setPipelinesLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Validate required fields
    if (!formData.name.trim()) {
      newErrors.name = "Vault name is required";
    }

    if (!formData.pipeline_name.trim()) {
      newErrors.pipeline_name = "Please select a pipeline";
    }

    // Validate storage configuration only if custom storage is enabled
    if (useCustomStorage) {
      const storageErrors: FormErrors['storage_config'] = {};
      
      if (!formData.storage_config?.account_name.trim()) {
        storageErrors.account_name = "Storage account name is required";
      }

      if (!formData.storage_config?.container_name.trim()) {
        storageErrors.container_name = "Container name is required";
      }

      if (formData.storage_config?.credential_type === "connection_string" && 
          !formData.storage_config?.connection_string?.trim()) {
        storageErrors.connection_string = "Connection string is required when using connection string authentication";
      }

      if (Object.keys(storageErrors).length > 0) {
        newErrors.storage_config = storageErrors;
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      // Create request object, conditionally including storage_config
      const request: VaultCreateRequest = {
        name: formData.name,
        description: formData.description,
        pipeline_name: formData.pipeline_name,
        processing_config: formData.processing_config,
        metadata: formData.metadata
      };

      // Only include storage_config if custom storage is enabled
      if (useCustomStorage) {
        request.storage_config = formData.storage_config;
      }

      await onCreateVault(request);
      handleClose();
    } catch (error) {
      // Error handling is done in the parent component
      console.error('Error creating vault:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: "",
      description: "",
      pipeline_name: "",
      processing_config: {
        auto_process_documents: true,
        supported_formats: ["pdf", "docx", "pptx", "excel"],
      },
      storage_config: {
        account_name: "",
        container_name: "",
        credential_type: "connection_string",
        connection_string: ""
      },
      metadata: {}
    });
    setErrors({});
    setIsSubmitting(false);
    setUseCustomStorage(false);
    // Reset pipelines to free up memory when dialog closes
    setPipelines([]);
    onOpenChange(false);
  };

  const updateStorageConfig = (updates: Partial<StorageConfig>) => {
    setFormData(prev => ({
      ...prev,
      storage_config: {
        ...prev.storage_config!,
        ...updates
      }
    }));
  };

  const updateProcessingConfig = (updates: Partial<DocumentProcessingConfig>) => {
    setFormData(prev => ({
      ...prev,
      processing_config: {
        ...prev.processing_config!,
        ...updates
      }
    }));
  };

  const selectedPipeline = pipelines.find(p => p.name === formData.pipeline_name);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Vault</DialogTitle>
          <DialogDescription>
            Create a new document vault to organize and process your files with custom storage and processing configurations.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Settings className="h-5 w-5 mr-2" />
                Basic Information
              </CardTitle>
              <CardDescription>
                Set up the basic properties for your vault.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="vaultName">
                    Vault Name <span className="text-red-500">*</span>
                  </Label>
                  <Input
                    id="vaultName"
                    value={formData.name}
                    onChange={(e) => {
                      setFormData({ ...formData, name: e.target.value });
                      if (errors.name) {
                        setErrors({ ...errors, name: undefined });
                      }
                    }}
                    placeholder="Enter vault name"
                    className={errors.name ? "border-red-500" : ""}
                  />
                  {errors.name && (
                    <p className="text-sm text-red-500 mt-1">{errors.name}</p>
                  )}
                </div>
                <div>
                  <Label htmlFor="vaultDescription">Description</Label>
                  <Textarea
                    id="vaultDescription"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Describe the purpose of this vault"
                    className="min-h-[80px]"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Pipeline Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Workflow className="h-5 w-5 mr-2" />
                Processing Pipeline
              </CardTitle>
              <CardDescription>
                Select the pipeline that will process documents in this vault.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="pipeline">
                  Pipeline <span className="text-red-500">*</span>
                </Label>
                <Select 
                  value={formData.pipeline_name} 
                  onValueChange={(value) => {
                    setFormData({ ...formData, pipeline_name: value });
                    if (errors.pipeline_name) {
                      setErrors({ ...errors, pipeline_name: undefined });
                    }
                  }}
                  disabled={pipelinesLoading || pipelines.length === 0 || pipelines.filter(p => p.settings?.enabled === true).length === 0}
                >
                  <SelectTrigger className={errors.pipeline_name ? "border-red-500" : ""}>
                    <SelectValue placeholder={pipelinesLoading ? "Loading pipelines..." : pipelines.length === 0 ? "No pipelines available" : "Select a pipeline"} />
                  </SelectTrigger>
                  <SelectContent>
                    {pipelines.map((pipeline) => (
                      <SelectItem key={pipeline.name} value={pipeline.name}>
                        <div className="flex flex-col">
                          <span className="font-medium">{pipeline.name}</span>
                          {pipeline.description && (
                            <span className="text-sm text-muted-foreground">{pipeline.description}</span>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.pipeline_name && (
                  <p className="text-sm text-red-500 mt-1">{errors.pipeline_name}</p>
                )}
                {!pipelinesLoading && (pipelines.length === 0 || pipelines.filter(p => p.settings?.enabled === true).length === 0) && (
                  <Alert className="mt-2 text-red-500">
                    <AlertCircle className="h-4 w-4" color="red" />
                    <AlertDescription>
                      No enabled pipelines are available. Please create or enable a pipeline first before creating a vault.
                    </AlertDescription>
                  </Alert>
                )}
              </div>

              {selectedPipeline && (
                <Alert>
                  <Workflow className="h-4 w-4" />
                  <AlertDescription>
                    <div className="space-y-2">
                      <p><strong>Selected Pipeline:</strong> {selectedPipeline.name}</p>
                      {selectedPipeline.description && (
                        <p>{selectedPipeline.description}</p>
                      )}
                      <div className="flex flex-wrap gap-2">
                        <span className="text-sm font-medium">Steps:</span>
                        {selectedPipeline.steps.map((step, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {step}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>
              )}

              <div className="space-y-4 p-4 border rounded-lg bg-muted/20">
                <h4 className="font-medium">Document Processing Settings</h4>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="autoProcess">Auto-process Documents</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically process documents when uploaded to this vault
                    </p>
                  </div>
                  <Switch
                    id="autoProcess"
                    checked={formData.processing_config?.auto_process_documents}
                    onCheckedChange={(checked) => 
                      updateProcessingConfig({ auto_process_documents: checked })
                    }
                  />
                </div>
                
              </div>
            </CardContent>
          </Card>

          {/* Storage Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Database className="h-5 w-5 mr-2" />
                Storage Configuration
              </CardTitle>
              <CardDescription>
                Choose to use the application's default storage or configure your own Azure Storage settings.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/20">
                <div className="space-y-0.5">
                  <Label htmlFor="customStorage">Use Custom Storage Configuration</Label>
                  <p className="text-sm text-muted-foreground">
                    Enable this to configure your own Azure Storage account, otherwise the application's default storage will be used
                  </p>
                </div>
                <Switch
                  id="customStorage"
                  checked={useCustomStorage}
                  onCheckedChange={(checked) => {
                    setUseCustomStorage(checked);
                    // Clear any storage config errors when toggling
                    if (!checked && errors.storage_config) {
                      setErrors({ ...errors, storage_config: undefined });
                    }
                  }}
                />
              </div>

              {!useCustomStorage && (
                <Alert>
                  <Database className="h-4 w-4" />
                  <AlertDescription>
                    This vault will use the application's default storage configuration. Documents will be stored securely using the system's configured storage account.
                  </AlertDescription>
                </Alert>
              )}

              {useCustomStorage && (
                <>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="storageAccount">
                        Storage Account Name <span className="text-red-500">*</span>
                      </Label>
                      <Input
                        id="storageAccount"
                        value={formData.storage_config?.account_name || ""}
                        onChange={(e) => {
                          updateStorageConfig({ account_name: e.target.value });
                          if (errors.storage_config?.account_name) {
                            setErrors({
                              ...errors,
                              storage_config: {
                                ...errors.storage_config,
                                account_name: undefined
                              }
                            });
                          }
                        }}
                        placeholder="mystorageaccount"
                        className={errors.storage_config?.account_name ? "border-red-500" : ""}
                      />
                      {errors.storage_config?.account_name && (
                        <p className="text-sm text-red-500 mt-1">{errors.storage_config.account_name}</p>
                      )}
                    </div>
                    <div>
                      <Label htmlFor="containerName">
                        Container Name <span className="text-red-500">*</span>
                      </Label>
                      <Input
                        id="containerName"
                        value={formData.storage_config?.container_name || ""}
                        onChange={(e) => {
                          updateStorageConfig({ container_name: e.target.value });
                          if (errors.storage_config?.container_name) {
                            setErrors({
                              ...errors,
                              storage_config: {
                                ...errors.storage_config,
                                container_name: undefined
                              }
                            });
                          }
                        }}
                        placeholder="vaults"
                        className={errors.storage_config?.container_name ? "border-red-500" : ""}
                      />
                      {errors.storage_config?.container_name && (
                        <p className="text-sm text-red-500 mt-1">{errors.storage_config.container_name}</p>
                      )}
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="credentialType">Authentication Type</Label>
                    <Select
                      value={formData.storage_config?.credential_type || "default_azure_credential"}
                      onValueChange={(value) => updateStorageConfig({ credential_type: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select authentication type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="default_azure_credential">Default Azure Credential</SelectItem>
                        <SelectItem value="connection_string">Connection String</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {formData.storage_config?.credential_type === "connection_string" && (
                    <div>
                      <Label htmlFor="connectionString">
                        Connection String <span className="text-red-500">*</span>
                      </Label>
                      <Textarea
                        id="connectionString"
                        value={formData.storage_config?.connection_string || ""}
                        onChange={(e) => {
                          updateStorageConfig({ connection_string: e.target.value });
                          if (errors.storage_config?.connection_string) {
                            setErrors({
                              ...errors,
                              storage_config: {
                                ...errors.storage_config,
                                connection_string: undefined
                              }
                            });
                          }
                        }}
                        placeholder="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net"
                        className={errors.storage_config?.connection_string ? "border-red-500" : ""}
                        rows={3}
                      />
                      {errors.storage_config?.connection_string && (
                        <p className="text-sm text-red-500 mt-1">{errors.storage_config.connection_string}</p>
                      )}
                      <p className="text-sm text-muted-foreground mt-1">
                        Provide the complete Azure Storage connection string
                      </p>
                    </div>
                  )}

                  {formData.storage_config?.credential_type === "default_azure_credential" && (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        When using Default Azure Credential, ensure the respective credential has the necessary permissions
                        to access the storage account.
                      </AlertDescription>
                    </Alert>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            disabled={isSubmitting || loading || pipelinesLoading || pipelines.length === 0}
          >
            {isSubmitting ? "Creating..." : "Create Vault"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CreateVaultDialog;