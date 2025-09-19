import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { 
  Play,
  Pause,
  RotateCcw,
  X,
  ArrowLeft,
  Workflow,
  Activity,
  CheckCircle,
  AlertCircle,
  Clock,
  FileText,
  ArrowRight,
  Download,
  RefreshCw,
  Settings
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import UploadVaultDocuments from "@/components/vault/UploadVaultDocuments";
import ConfigureVaultDialog from "@/components/vault/ConfigureVaultDialog";
import { 
  vaultsApi,
  type Vault, 
  type Pipeline, 
  type DocumentInfo
} from "@/lib/api";

interface ViewVaultDetailsProps {
  vault: Vault;
  pipeline: Pipeline | null;
  // documents: DocumentInfo[];
  onBack: () => void;
  onProcessAllDocuments: () => void;
  // onLoadVaultDocuments: (vaultId: string) => void;
}

const ViewVaultDetails = ({ 
  vault, 
  pipeline, 
  // documents, 
  onBack, 
  onProcessAllDocuments
  // onLoadVaultDocuments
}: ViewVaultDetailsProps) => {
  const { toast } = useToast();
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);

  // Dialog states
  const [isStepDialogOpen, setIsStepDialogOpen] = useState(false);
  const [isPipelineDialogOpen, setIsPipelineDialogOpen] = useState(false);
  const [isConfigureDialogOpen, setIsConfigureDialogOpen] = useState(false);
  const [selectedPipeline, setSelectedPipeline] = useState<number | null>(null);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);

  // Load documents when vault changes
  useEffect(() => {
    if (vault?.id) {
      loadVaultDocuments(vault.id);
    }
  }, []);

  const loadVaultDocuments = async (vaultId: string) => {
    try {
      setIsLoadingDocuments(true);
      const docs = await vaultsApi.getVaultDocuments(vaultId);
      setDocuments(docs);
    } catch (error) {
      console.error('Error loading documents:', error);
      toast({
        title: "Error",
        description: "Failed to load vault documents",
        variant: "destructive",
      });
    } finally {
      setIsLoadingDocuments(false);
    }
  };

  const errorLogs = [
    {
      id: 1,
      jobId: 4,
      vaultId: vault?.id,
      document: "product_manual.pdf",
      error: "OCR processing failed: Unsupported image format",
      timestamp: "2024-06-19 13:50:15",
      severity: "error",
    },
  ];

  const processingPipelines = [
    {
      id: 1,
      documentId: 1,
      document: "contract_template.pdf",
      vaultId: vault?.id,
      status: "completed",
      startTime: "2024-06-19 14:15:30",
      endTime: "2024-06-19 14:18:45",
      steps: [
        {
          id: 1,
          name: "Text Extraction",
          status: "completed",
          startTime: "2024-06-19 14:15:30",
          endTime: "2024-06-19 14:16:15",
          duration: 45,
          output: {
            type: "text",
            content: "This is a sample contract template for legal agreements...",
            metadata: { pages: 5, characters: 12450, words: 2100 }
          }
        },
        {
          id: 2,
          name: "Document Summarization",
          status: "completed",
          startTime: "2024-06-19 14:16:15",
          endTime: "2024-06-19 14:17:30",
          duration: 75,
          output: {
            type: "summary",
            content: "A comprehensive legal contract template outlining terms and conditions for service agreements.",
            metadata: { model: "gpt-4", tokens_used: 2500 }
          }
        },
      ]
    }
  ];

  // Handler functions
  const handleUploadComplete = async (files: File[]) => {
    // Here you would typically call an API to upload the files
    // For now, we'll just simulate the upload and refresh the documents
    console.log('Uploading files:', files.map(f => f.name));
    
    // Simulate API call
    // await vaultsApi.uploadDocuments(vault.id, files);
    
    // Refresh the documents list after upload
    loadVaultDocuments(vault.id);
  };

  const handleProcessDocument = (documentId: number) => {
    toast({
      title: "Processing started",
      description: "Document processing has been initiated",
    });
  };

  const handleRetryProcessing = (documentId: number) => {
    toast({
      title: "Retrying processing", 
      description: "Document processing has been restarted",
    });
  };

  const handleViewStepOutput = (pipelineId: number, stepId: number) => {
    setSelectedPipeline(pipelineId);
    setSelectedStep(stepId);
    setIsStepDialogOpen(true);
  };

  const handleRetryPipeline = (pipelineId: number) => {
    toast({
      title: "Pipeline restarted",
      description: "Processing pipeline has been restarted successfully",
    });
  };

  const handleDownloadOutput = (stepId: number) => {
    toast({
      title: "Download started",
      description: "Step output is being downloaded",
    });
  };

  const handleViewProcessingPipeline = (documentId: string) => {
    setSelectedDocumentId(documentId);
    setIsPipelineDialogOpen(true);
  };

  const handleViewErrorLogs = (documentId: string) => {
    setSelectedDocumentId(documentId);
    // setIsErrorLogsDialogOpen(true);
  };

  const handleSaveVaultConfiguration = (config: any) => {
    // Here you would typically call an API to save the vault configuration
    console.log('Saving vault configuration:', config);
    toast({
      title: "Configuration Saved",
      description: "Vault configuration has been updated successfully",
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processing":
        return <Activity className="h-4 w-4 text-blue-500" />;
      case "active":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "inactive":
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return null;
    }
  };

  const getStepStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "running":
        return <Activity className="h-4 w-4 text-blue-500" />;
      case "skipped":
        return <Clock className="h-4 w-4 text-gray-400" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const renderStepOutput = (step: any) => {
    if (step.error) {
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error: {step.error.code}</AlertTitle>
          <AlertDescription>
            <p>{step.error.message}</p>
            {step.error.details && (
              <p className="text-sm mt-2 text-muted-foreground">{step.error.details}</p>
            )}
          </AlertDescription>
        </Alert>
      );
    }

    if (!step.output) {
      return <p className="text-muted-foreground">No output available</p>;
    }

    switch (step.output.type) {
      case "text":
        return (
          <div className="space-y-4">
            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm">{step.output.content}</p>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <Label>Pages</Label>
                <p>{step.output.metadata.pages}</p>
              </div>
              <div>
                <Label>Words</Label>
                <p>{step.output.metadata.words}</p>
              </div>
              <div>
                <Label>Characters</Label>
                <p>{step.output.metadata.characters}</p>
              </div>
            </div>
          </div>
        );

      case "summary":
        return (
          <div className="space-y-4">
            <div className="bg-muted p-4 rounded-lg">
              <p className="text-sm">{step.output.content}</p>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <Label>Model</Label>
                <p>{step.output.metadata.model}</p>
              </div>
              <div>
                <Label>Tokens Used</Label>
                <p>{step.output.metadata.tokens_used}</p>
              </div>
            </div>
          </div>
        );

      default:
        return <p className="text-muted-foreground">Unknown output type</p>;
    }
  };

  // Computed values
  const vaultJobs = [];
  const vaultErrors = vault?.id ? errorLogs.filter(error => error.vaultId === vault.id) : [];
  const vaultPipelines = vault?.id ? processingPipelines.filter(pipeline => pipeline.vaultId === vault.id) : [];
  
  const activeJobs = vaultJobs.filter(job => job.status === "processing" || job.status === "queued");
  const completedJobs = vaultJobs.filter(job => job.status === "completed");
  const failedJobs = vaultJobs.filter(job => job.status === "failed");
  
  const currentProcessingPipeline = selectedPipeline ? vaultPipelines.find(p => p.id === selectedPipeline) : null;
  const currentStep = selectedStep && currentProcessingPipeline ? currentProcessingPipeline.steps.find(s => s.id === selectedStep) : null;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={onBack}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Vaults
          </Button>
          <div className="flex-1">
            <h2 className="text-3xl font-bold tracking-tight">{vault.name}</h2>
            <p className="text-muted-foreground">
              {vault.description || "No description available"}
            </p>
          </div>
          {pipeline && (
            <Badge variant="outline" className="bg-blue-50">
              <Workflow className="h-3 w-3 mr-1" />
              Pipeline: {pipeline.name}
            </Badge>
          )}
        </div>
        <div className="flex space-x-3">
          <Button 
            size="lg" 
            variant="outline" 
            onClick={() => setIsConfigureDialogOpen(true)}
          >
            <Settings className="h-5 w-5 mr-2" />
            Configure
          </Button>
          <UploadVaultDocuments 
            vault={vault}
            onUploadComplete={handleUploadComplete}
          />
          <Button size="lg" variant="outline" onClick={onProcessAllDocuments}>
            <Play className="h-5 w-5 mr-2" />
            Process All Documents
          </Button>
        </div>
      </div>

      <div className="grid gap-2 md:grid-cols-4">
        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3 px-3">
            <CardTitle className="text-xs font-medium">Total Documents</CardTitle>
            <FileText className="h-3 w-3 text-muted-foreground" />
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="text-lg font-bold">{vault.stats.total_documents}</div>
          </CardContent>
        </Card>
        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3 px-3">
            <CardTitle className="text-xs font-medium">Active Jobs</CardTitle>
            <Activity className="h-3 w-3 text-muted-foreground" />
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="text-lg font-bold">{activeJobs.length}</div>
          </CardContent>
        </Card>
        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3 px-3">
            <CardTitle className="text-xs font-medium">Completed</CardTitle>
            <CheckCircle className="h-3 w-3 text-muted-foreground" />
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="text-lg font-bold">{completedJobs.length}</div>
          </CardContent>
        </Card>
        <Card className="h-fit">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-3 px-3">
            <CardTitle className="text-xs font-medium">Failed</CardTitle>
            <AlertCircle className="h-3 w-3 text-muted-foreground" />
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="text-lg font-bold">{failedJobs.length}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="documents" className="space-y-6">
        <TabsList>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="errors">Error Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="documents">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Documents in {vault.name}</CardTitle>
                  <CardDescription>
                    Documents stored in this vault and their processing status.
                  </CardDescription>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => loadVaultDocuments(vault.id)}
                  disabled={isLoadingDocuments}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className={`h-4 w-4 ${isLoadingDocuments ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {isLoadingDocuments ? (
                <div className="text-center py-8">
                  <RefreshCw className="h-8 w-8 mx-auto mb-4 animate-spin text-muted-foreground" />
                  <p className="text-muted-foreground">Loading documents...</p>
                </div>
              ) : documents.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>No documents in this vault yet.</p>
                  <p className="text-sm">Upload documents to get started.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Document</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Upload Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documents.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell>
                          <div className="flex items-center space-x-3">
                            <FileText className="h-5 w-5 text-muted-foreground" />
                            <span className="font-medium">{doc.name}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          {(doc.size_bytes / (1024 * 1024)).toFixed(2)} MB
                        </TableCell>
                        <TableCell>
                          {new Date(doc.upload_date).toLocaleDateString()} - {new Date(doc.upload_date).toLocaleTimeString()}
                        </TableCell>
                        <TableCell>
                          <Badge variant={doc.status === "processed" ? "default" : "secondary"}>
                            {doc.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleViewProcessingPipeline(doc.id)}
                            >
                              <Workflow className="h-3 w-3 mr-1" />
                              Pipeline
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleViewErrorLogs(doc.id)}
                            >
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Errors
                            </Button>
                            {doc.status === "failed" && (
                              <Button 
                                size="sm" 
                                variant="outline" 
                                onClick={() => handleRetryProcessing(parseInt(doc.id))}
                              >
                                <RotateCcw className="h-3 w-3 mr-1" />
                                Retry
                              </Button>
                            )}
                            {doc.status === "pending" && (
                              <Button 
                                size="sm" 
                                onClick={() => handleProcessDocument(parseInt(doc.id))}
                              >
                                <Play className="h-3 w-3 mr-1" />
                                Process
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
       
        <TabsContent value="errors">
          <Card>
            <CardHeader>
              <CardTitle>Error Logs</CardTitle>
              <CardDescription>
                Processing errors and warnings for documents in this vault.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {vaultErrors.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>No errors found.</p>
                    <p className="text-sm">All processing jobs completed successfully.</p>
                  </div>
                ) : (
                  vaultErrors.map((error) => (
                    <Alert key={error.id} variant={error.severity === "error" ? "destructive" : "default"}>
                      <AlertCircle className="h-4 w-4" />
                      <AlertTitle>{error.document}</AlertTitle>
                      <AlertDescription>
                        <p>{error.error}</p>
                        <p className="text-xs mt-2 text-muted-foreground">{error.timestamp}</p>
                      </AlertDescription>
                    </Alert>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Step Output Dialog */}
      <Dialog open={isStepDialogOpen} onOpenChange={setIsStepDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {currentProcessingPipeline?.document} - {currentStep?.name}
            </DialogTitle>
            <DialogDescription>
              Step output and details from the processing pipeline.
            </DialogDescription>
          </DialogHeader>
          {currentStep && (
            <div className="space-y-6 py-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <Label>Status</Label>
                  <div className="flex items-center space-x-2 mt-1">
                    {getStepStatusIcon(currentStep.status)}
                    <span className="capitalize">{currentStep.status}</span>
                  </div>
                </div>
                <div>
                  <Label>Duration</Label>
                  <p>{currentStep.duration}s</p>
                </div>
                <div>
                  <Label>Start Time</Label>
                  <p>{currentStep.startTime}</p>
                </div>
                <div>
                  <Label>End Time</Label>
                  <p>{currentStep.endTime}</p>
                </div>
              </div>
              <div>
                <Label>Output</Label>
                <div className="mt-2">
                  {renderStepOutput(currentStep)}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsStepDialogOpen(false)}>
              Close
            </Button>
            {currentStep?.status === "completed" && (
              <Button onClick={() => handleDownloadOutput(currentStep.id)}>
                <Download className="h-4 w-4 mr-2" />
                Download Output
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Pipeline Dialog */}
      <Dialog open={isPipelineDialogOpen} onOpenChange={setIsPipelineDialogOpen}>
        <DialogContent className="max-w-5xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Processing Pipeline
              {selectedDocumentId && documents.find(d => d.id === selectedDocumentId) && 
                ` - ${documents.find(d => d.id === selectedDocumentId)?.name}`
              }
            </DialogTitle>
            <DialogDescription>
              Detailed view of processing pipeline execution for this document.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {selectedDocumentId && (() => {
              const documentPipelines = vaultPipelines.filter(pipeline => 
                pipeline.documentId.toString() === selectedDocumentId
              );
              
              if (documentPipelines.length === 0) {
                return (
                  <div className="text-center py-8 text-muted-foreground">
                    <Workflow className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>No pipeline executions found for this document.</p>
                    <p className="text-sm">The document may not have been processed yet.</p>
                  </div>
                );
              }

              return (
                <div className="space-y-4">
                  {documentPipelines.map((pipeline) => (
                    <div key={pipeline.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(pipeline.status)}
                          <span className="font-medium">{pipeline.document}</span>
                          <Badge variant={pipeline.status === "completed" ? "default" : "destructive"}>
                            {pipeline.status}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-2">
                          {pipeline.status === "failed" && (
                            <Button size="sm" variant="outline" onClick={() => handleRetryPipeline(pipeline.id)}>
                              <RefreshCw className="h-3 w-3 mr-1" />
                              Retry Pipeline
                            </Button>
                          )}
                          <div className="text-sm text-muted-foreground">
                            {pipeline.startTime} - {pipeline.endTime || "Running"}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 overflow-x-auto pb-4">
                        {pipeline.steps.map((step, index) => (
                          <div key={step.id} className="flex items-center space-x-2">
                            <div className="flex flex-col items-center space-y-2 min-w-[120px]">
                              <div
                                className={`w-12 h-12 rounded-full border-2 flex items-center justify-center cursor-pointer transition-colors ${
                                  step.status === "completed"
                                    ? "border-green-500 bg-green-50"
                                    : step.status === "failed"
                                    ? "border-red-500 bg-red-50"
                                    : step.status === "running"
                                    ? "border-blue-500 bg-blue-50"
                                    : "border-gray-300 bg-gray-50"
                                }`}
                                onClick={() => handleViewStepOutput(pipeline.id, step.id)}
                              >
                                {getStepStatusIcon(step.status)}
                              </div>
                              <div className="text-center">
                                <p className="text-xs font-medium">{step.name}</p>
                                {step.duration && (
                                  <p className="text-xs text-muted-foreground">{step.duration}s</p>
                                )}
                                {step.status === "skipped" && (
                                  <p className="text-xs text-muted-foreground">Skipped</p>
                                )}
                              </div>
                            </div>
                            {index < pipeline.steps.length - 1 && (
                              <ArrowRight className="h-4 w-4 text-muted-foreground" />
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsPipelineDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Configure Vault Dialog */}
      <ConfigureVaultDialog
        vault={vault}
        isOpen={isConfigureDialogOpen}
        onClose={() => setIsConfigureDialogOpen(false)}
        onSave={handleSaveVaultConfiguration}
      />
    </div>
  );
};

export default ViewVaultDetails;