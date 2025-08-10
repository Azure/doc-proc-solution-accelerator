import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
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
  DialogTrigger,
} from "@/components/ui/dialog";
import { 
  Plus, 
  Search, 
  Settings, 
  Trash2, 
  FolderOpen, 
  FileText, 
  Upload,
  Play,
  Pause,
  RotateCcw,
  X,
  Activity,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowLeft
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import vaultConfig from "@/config/vaultConfig";

const Vaults = () => {
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newVault, setNewVault] = useState({ name: "", description: "" });
  const [selectedVault, setSelectedVault] = useState<number | null>(null);
  const [chunkSize, setChunkSize] = useState([512]);
  const [chunkOverlap, setChunkOverlap] = useState([50]);
  const [enableOCR, setEnableOCR] = useState(false);

  const azureSearchConfig = vaultConfig.azureSearch;

  // Editable Azure Search config state
  const [editableAzureConfig, setEditableAzureConfig] = useState({
    endpoint: azureSearchConfig.endpoint,
    apiKey: azureSearchConfig.apiKey,
    indexName: azureSearchConfig.indexName,
    apiVersion: azureSearchConfig.apiVersion || "",
  });

  const handleAzureConfigChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setEditableAzureConfig((prev) => ({ ...prev, [id]: value }));
  };

  const vaults = [
    {
      id: 1,
      name: "Legal Documents",
      description: "Contracts, agreements, and legal correspondence",
      documentCount: 145,
      status: "active",
      created: "2024-01-15",
      lastProcessed: "2024-06-18",
    },
    {
      id: 2,
      name: "Research Papers",
      description: "Academic research and technical papers",
      documentCount: 89,
      status: "active",
      created: "2024-02-03",
      lastProcessed: "2024-06-19",
    },
    {
      id: 3,
      name: "Marketing Materials",
      description: "Brochures, presentations, and marketing content",
      documentCount: 67,
      status: "processing",
      created: "2024-03-10",
      lastProcessed: "2024-06-19",
    },
    {
      id: 4,
      name: "Product Specifications",
      description: "Technical documentation and product specs",
      documentCount: 23,
      status: "active",
      created: "2024-06-01",
      lastProcessed: "2024-06-18",
    },
  ];

  const documents = [
    {
      id: 1,
      name: "contract_template.pdf",
      vaultId: 1,
      size: "2.4 MB",
      uploadDate: "2024-06-19",
      status: "processed",
      chunks: 45,
    },
    {
      id: 2,
      name: "research_paper_ai.pdf",
      vaultId: 2,
      size: "5.1 MB",
      uploadDate: "2024-06-19",
      status: "processing",
      chunks: 0,
    },
    {
      id: 3,
      name: "marketing_brochure.docx",
      vaultId: 3,
      size: "1.8 MB",
      uploadDate: "2024-06-18",
      status: "failed",
      chunks: 0,
    },
    {
      id: 4,
      name: "product_spec_v2.pdf",
      vaultId: 4,
      size: "3.2 MB",
      uploadDate: "2024-06-18",
      status: "processed",
      chunks: 23,
    },
  ];

  const processingJobs = [
    {
      id: 1,
      document: "legal_contract_v3.pdf",
      vaultId: 1,
      status: "processing",
      progress: 65,
      startTime: "2024-06-19 14:30:15",
      estimatedCompletion: "2024-06-19 14:35:00",
      chunks: 12,
      totalChunks: 18,
    },
    {
      id: 2,
      document: "research_data.pdf",
      vaultId: 2,
      status: "queued",
      progress: 0,
      startTime: null,
      estimatedCompletion: null,
      chunks: 0,
      totalChunks: 25,
    },
    {
      id: 3,
      document: "marketing_brief.docx",
      vaultId: 3,
      status: "completed",
      progress: 100,
      startTime: "2024-06-19 14:15:30",
      estimatedCompletion: "2024-06-19 14:20:45",
      chunks: 8,
      totalChunks: 8,
    },
    {
      id: 4,
      document: "product_manual.pdf",
      vaultId: 4,
      status: "failed",
      progress: 45,
      startTime: "2024-06-19 13:45:20",
      estimatedCompletion: null,
      chunks: 5,
      totalChunks: 12,
    },
  ];

  const errorLogs = [
    {
      id: 1,
      jobId: 4,
      vaultId: 4,
      document: "product_manual.pdf",
      error: "OCR processing failed: Unsupported image format",
      timestamp: "2024-06-19 13:50:15",
      severity: "error",
    },
    {
      id: 2,
      jobId: 4,
      vaultId: 4,
      document: "product_manual.pdf",
      error: "Chunk extraction timeout on page 15",
      timestamp: "2024-06-19 13:52:30",
      severity: "warning",
    },
    {
      id: 3,
      jobId: 1,
      vaultId: 1,
      document: "legal_contract_v3.pdf",
      error: "Memory usage high, processing slowed",
      timestamp: "2024-06-19 14:32:45",
      severity: "warning",
    },
  ];

  const handleCreateVault = () => {
    if (!newVault.name.trim()) {
      toast({
        title: "Error",
        description: "Vault name is required",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "Success",
      description: `Vault "${newVault.name}" created successfully`,
    });

    setNewVault({ name: "", description: "" });
    setIsCreateDialogOpen(false);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      toast({
        title: "Files uploaded",
        description: `${files.length} file(s) uploaded successfully`,
      });
    }
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

  const handleRestartJob = (jobId: number) => {
    toast({
      title: "Job restarted",
      description: "Processing job has been restarted successfully",
    });
  };

  const handlePauseJob = (jobId: number) => {
    toast({
      title: "Job paused",
      description: "Processing job has been paused",
    });
  };

  const handleCancelJob = (jobId: number) => {
    toast({
      title: "Job cancelled",
      description: "Processing job has been cancelled",
      variant: "destructive",
    });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processing":
        return <Activity className="h-4 w-4 text-blue-500" />;
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "queued":
        return <Clock className="h-4 w-4 text-yellow-500" />;
      default:
        return null;
    }
  };

  const filteredVaults = vaults.filter(vault =>
    vault.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    vault.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const currentVault = selectedVault ? vaults.find(v => v.id === selectedVault) : null;
  const vaultDocuments = selectedVault ? documents.filter(doc => doc.vaultId === selectedVault) : [];
  const vaultJobs = selectedVault ? processingJobs.filter(job => job.vaultId === selectedVault) : [];
  const vaultErrors = selectedVault ? errorLogs.filter(error => error.vaultId === selectedVault) : [];

  const activeJobs = vaultJobs.filter(job => job.status === "processing" || job.status === "queued");
  const completedJobs = vaultJobs.filter(job => job.status === "completed");
  const failedJobs = vaultJobs.filter(job => job.status === "failed");

  if (selectedVault && currentVault) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedVault(null)}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Vaults
          </Button>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">{currentVault.name}</h2>
            <p className="text-muted-foreground">
              {currentVault.description}
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{vaultDocuments.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activeJobs.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{completedJobs.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{failedJobs.length}</div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="documents" className="space-y-6">
          <TabsList>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="upload">Upload & Configure</TabsTrigger>
            <TabsTrigger value="processing">Processing Status</TabsTrigger>
            <TabsTrigger value="errors">Error Logs</TabsTrigger>
          </TabsList>

          <TabsContent value="documents">
            <Card>
              <CardHeader>
                <CardTitle>Documents in {currentVault.name}</CardTitle>
                <CardDescription>
                  Manage documents and their processing status in this vault.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {vaultDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center space-x-4">
                        <FileText className="h-8 w-8 text-muted-foreground" />
                        <div>
                          <h4 className="font-medium">{doc.name}</h4>
                          <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                            <span>{doc.size}</span>
                            <span>{doc.uploadDate}</span>
                            {doc.chunks > 0 && <span>{doc.chunks} chunks</span>}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Badge
                          variant={
                            doc.status === "processed"
                              ? "default"
                              : doc.status === "failed"
                              ? "destructive"
                              : "secondary"
                          }
                        >
                          {doc.status}
                        </Badge>
                        <div className="flex space-x-1">
                          {doc.status === "failed" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleRetryProcessing(doc.id)}
                            >
                              <RotateCcw className="h-4 w-4" />
                            </Button>
                          )}
                          {doc.status === "processed" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleProcessDocument(doc.id)}
                            >
                              <Settings className="h-4 w-4" />
                            </Button>
                          )}
                          {doc.status === "processing" && (
                            <Button size="sm" variant="outline" disabled>
                              <Pause className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="upload" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Upload Documents</CardTitle>
                  <CardDescription>
                    Upload files to {currentVault.name} vault.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="file-upload">Select Files</Label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                      <Upload className="mx-auto h-12 w-12 text-gray-400" />
                      <div className="mt-4">
                        <Input
                          id="file-upload"
                          type="file"
                          multiple
                          onChange={handleFileUpload}
                          className="hidden"
                        />
                        <Label
                          htmlFor="file-upload"
                          className="cursor-pointer inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary hover:bg-primary/90"
                        >
                          Choose Files
                        </Label>
                        <p className="mt-2 text-sm text-gray-500">
                          PDF, DOC, DOCX files up to 10MB
                        </p>
                      </div>
                    </div>
                  </div>

                  <Button className="w-full">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload Documents
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Processing Configuration</CardTitle>
                  <CardDescription>
                    Configure how documents should be processed and chunked.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <Label>Chunk Size (tokens)</Label>
                    <div className="mt-2">
                      <Slider
                        value={chunkSize}
                        onValueChange={setChunkSize}
                        max={2048}
                        min={128}
                        step={64}
                        className="mb-2"
                      />
                      <div className="text-sm text-muted-foreground">
                        Current: {chunkSize[0]} tokens
                      </div>
                    </div>
                  </div>

                  <div>
                    <Label>Chunk Overlap (tokens)</Label>
                    <div className="mt-2">
                      <Slider
                        value={chunkOverlap}
                        onValueChange={setChunkOverlap}
                        max={200}
                        min={0}
                        step={10}
                        className="mb-2"
                      />
                      <div className="text-sm text-muted-foreground">
                        Current: {chunkOverlap[0]} tokens
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="ocr-switch">Enable OCR</Label>
                      <p className="text-sm text-muted-foreground">
                        Extract text from images and scanned documents
                      </p>
                    </div>
                    <Switch
                      id="ocr-switch"
                      checked={enableOCR}
                      onCheckedChange={setEnableOCR}
                    />
                  </div>

                  <div>
                    <Label htmlFor="processing-mode">Processing Mode</Label>
                    <Select defaultValue="standard">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="fast">Fast (Basic extraction)</SelectItem>
                        <SelectItem value="standard">Standard (Balanced)</SelectItem>
                        <SelectItem value="detailed">Detailed (Full analysis)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Azure AI Search Configuration</CardTitle>
                  <CardDescription>
                    Configure the Azure AI Search Index for this vault.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="endpoint">Endpoint</Label>
                    <Input
                      id="endpoint"
                      value={editableAzureConfig.endpoint}
                      onChange={handleAzureConfigChange}
                      className="mb-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="indexName">Index Name</Label>
                    <Input
                      id="indexName"
                      value={editableAzureConfig.indexName}
                      onChange={handleAzureConfigChange}
                      className="mb-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="apiKey">API Key</Label>
                    <Input
                      id="apiKey"
                      value={editableAzureConfig.apiKey}
                      onChange={handleAzureConfigChange}
                      type="password"
                      className="mb-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="apiVersion">API Version</Label>
                    <Input
                      id="apiVersion"
                      value={editableAzureConfig.apiVersion}
                      onChange={handleAzureConfigChange}
                      className="mb-2"
                    />
                  </div>
                  {/* You can add a save button here to persist changes if needed */}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="processing">
            <div className="space-y-6">
              {activeJobs.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Active Processing Jobs</CardTitle>
                    <CardDescription>
                      Currently running and queued processing jobs in this vault.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {activeJobs.map((job) => (
                        <div
                          key={job.id}
                          className="flex items-center justify-between p-4 border rounded-lg"
                        >
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center space-x-3">
                              {getStatusIcon(job.status)}
                              <span className="font-medium">{job.document}</span>
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {job.startTime && `Started: ${job.startTime}`}
                              {job.estimatedCompletion && ` • ETA: ${job.estimatedCompletion}`}
                            </div>
                            {job.status === "processing" && (
                              <div className="space-y-1">
                                <div className="flex justify-between text-sm">
                                  <span>Progress</span>
                                  <span>{job.chunks}/{job.totalChunks} chunks</span>
                                </div>
                                <Progress value={job.progress} />
                              </div>
                            )}
                          </div>
                          <div className="flex space-x-2">
                            {job.status === "processing" && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handlePauseJob(job.id)}
                              >
                                <Pause className="h-4 w-4" />
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleCancelJob(job.id)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {completedJobs.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Completed Jobs</CardTitle>
                    <CardDescription>
                      Successfully processed documents in this vault.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Document</TableHead>
                          <TableHead>Chunks</TableHead>
                          <TableHead>Completed</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {completedJobs.map((job) => (
                          <TableRow key={job.id}>
                            <TableCell className="font-medium">{job.document}</TableCell>
                            <TableCell>{job.chunks}</TableCell>
                            <TableCell>{job.estimatedCompletion}</TableCell>
                            <TableCell>
                              <Badge>{job.status}</Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}

              {failedJobs.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Failed Jobs</CardTitle>
                    <CardDescription>
                      Jobs that encountered errors during processing in this vault.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {failedJobs.map((job) => (
                        <Alert key={job.id} variant="destructive">
                          <AlertCircle className="h-4 w-4" />
                          <AlertTitle>{job.document}</AlertTitle>
                          <AlertDescription className="mt-2">
                            <div className="flex justify-between items-center">
                              <div>
                                <p>Processing failed at {job.progress}% completion</p>
                                <p className="text-sm text-muted-foreground">
                                  Started: {job.startTime}
                                </p>
                              </div>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleRestartJob(job.id)}
                              >
                                <RotateCcw className="h-4 w-4 mr-2" />
                                Restart
                              </Button>
                            </div>
                          </AlertDescription>
                        </Alert>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="errors">
            <Card>
              <CardHeader>
                <CardTitle>Error Logs</CardTitle>
                <CardDescription>
                  Detailed error information and warnings for this vault.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Document</TableHead>
                      <TableHead>Error</TableHead>
                      <TableHead>Severity</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {vaultErrors.map((error) => (
                      <TableRow key={error.id}>
                        <TableCell>{error.timestamp}</TableCell>
                        <TableCell>{error.document}</TableCell>
                        <TableCell className="max-w-md truncate">
                          {error.error}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={error.severity === "error" ? "destructive" : "secondary"}
                          >
                            {error.severity}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Document Vaults</h2>
          <p className="text-muted-foreground">
            Create and manage your document storage vaults.
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Vault
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Vault</DialogTitle>
              <DialogDescription>
                Create a new document vault to organize and process your files.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="vaultName">Vault Name</Label>
                <Input
                  id="vaultName"
                  value={newVault.name}
                  onChange={(e) => setNewVault({ ...newVault, name: e.target.value })}
                  placeholder="Enter vault name"
                />
              </div>
              <div>
                <Label htmlFor="vaultDescription">Description</Label>
                <Textarea
                  id="vaultDescription"
                  value={newVault.description}
                  onChange={(e) => setNewVault({ ...newVault, description: e.target.value })}
                  placeholder="Describe the purpose of this vault"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateVault}>Create Vault</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center space-x-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search vaults..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredVaults.map((vault) => (
          <Card 
            key={vault.id} 
            className="hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => setSelectedVault(vault.id)}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="flex items-center space-x-2">
                <FolderOpen className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg">{vault.name}</CardTitle>
              </div>
              <Badge
                variant={vault.status === "active" ? "default" : "secondary"}
              >
                {vault.status}
              </Badge>
            </CardHeader>
            <CardContent>
              <CardDescription className="mb-4">
                {vault.description}
              </CardDescription>
              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Documents:</span>
                  <div className="flex items-center space-x-1">
                    <FileText className="h-3 w-3" />
                    <span>{vault.documentCount}</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Created:</span>
                  <span>{vault.created}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Last processed:</span>
                  <span>{vault.lastProcessed}</span>
                </div>
              </div>
              <div className="flex justify-between pt-4 border-t">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Handle configure action
                  }}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  Configure
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-destructive"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Handle delete action
                  }}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Vaults;
