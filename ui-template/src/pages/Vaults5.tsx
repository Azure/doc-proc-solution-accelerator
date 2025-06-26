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
import { Checkbox } from "@/components/ui/checkbox";
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
  ArrowLeft,
  Database,
  Edit,
  Save,
  ArrowRight,
  Eye,
  Download,
  RefreshCw
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const Vaults5 = () => {
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [isIndexDialogOpen, setIsIndexDialogOpen] = useState(false);
  const [newVault, setNewVault] = useState({ 
    name: "", 
    description: "",
    createIndex: false,
    indexName: "",
    dataStore: "elasticsearch",
    embeddingModel: "text-embedding-ada-002"
  });
  const [selectedVault, setSelectedVault] = useState<number | null>(null);
  const [chunkSize, setChunkSize] = useState([512]);
  const [chunkOverlap, setChunkOverlap] = useState([50]);
  const [enableOCR, setEnableOCR] = useState(false);
  const [enableIndexing, setEnableIndexing] = useState(false);
  const [indexDataStore, setIndexDataStore] = useState("elasticsearch");
  const [indexName, setIndexName] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("text-embedding-ada-002");
  const [indexFields, setIndexFields] = useState([
    { id: 1, name: "content", type: "text", searchable: true, facetable: false },
    { id: 2, name: "title", type: "text", searchable: true, facetable: false },
    { id: 3, name: "author", type: "keyword", searchable: false, facetable: true },
    { id: 4, name: "created_date", type: "date", searchable: false, facetable: true },
    { id: 5, name: "file_type", type: "keyword", searchable: false, facetable: true }
  ]);
  const [isEditingFields, setIsEditingFields] = useState(false);
  const [newField, setNewField] = useState({ name: "", type: "text", searchable: true, facetable: false });

  const vaults = [
    {
      id: 1,
      name: "Legal Documents",
      description: "Contracts, agreements, and legal correspondence",
      documentCount: 145,
      status: "active",
      created: "2024-01-15",
      lastProcessed: "2024-06-18",
      hasIndex: true,
      indexName: "legal_docs_index",
      dataStore: "elasticsearch"
    },
    {
      id: 2,
      name: "Research Papers",
      description: "Academic research and technical papers",
      documentCount: 89,
      status: "active",
      created: "2024-02-03",
      lastProcessed: "2024-06-19",
      hasIndex: true,
      indexName: "research_papers_index",
      dataStore: "pinecone"
    },
    {
      id: 3,
      name: "Marketing Materials",
      description: "Brochures, presentations, and marketing content",
      documentCount: 67,
      status: "processing",
      created: "2024-03-10",
      lastProcessed: "2024-06-19",
      hasIndex: false,
      indexName: "",
      dataStore: ""
    },
    {
      id: 4,
      name: "Product Specifications",
      description: "Technical documentation and product specs",
      documentCount: 23,
      status: "active",
      created: "2024-06-01",
      lastProcessed: "2024-06-18",
      hasIndex: true,
      indexName: "product_specs_index",
      dataStore: "opensearch"
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

  const processingPipelines = [
    {
      id: 1,
      documentId: 1,
      document: "contract_template.pdf",
      vaultId: 1,
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
            content: "A comprehensive legal contract template outlining terms and conditions for service agreements, including payment terms, liability clauses, and termination procedures.",
            metadata: { model: "gpt-4", tokens_used: 2500 }
          }
        },
        {
          id: 3,
          name: "Entity Extraction",
          status: "completed",
          startTime: "2024-06-19 14:17:30",
          endTime: "2024-06-19 14:18:00",
          duration: 30,
          output: {
            type: "entities",
            content: [
              { type: "PERSON", value: "John Doe", confidence: 0.95 },
              { type: "ORG", value: "ABC Corporation", confidence: 0.92 },
              { type: "DATE", value: "2024-06-19", confidence: 0.88 },
              { type: "MONEY", value: "$50,000", confidence: 0.94 }
            ],
            metadata: { total_entities: 15 }
          }
        },
        {
          id: 4,
          name: "Key Information Extraction",
          status: "completed",
          startTime: "2024-06-19 14:18:00",
          endTime: "2024-06-19 14:18:45",
          duration: 45,
          output: {
            type: "key_info",
            content: {
              contract_type: "Service Agreement",
              parties: ["ABC Corporation", "John Doe"],
              effective_date: "2024-07-01",
              termination_date: "2025-06-30",
              payment_terms: "Net 30 days",
              total_value: "$50,000"
            },
            metadata: { confidence_score: 0.91 }
          }
        }
      ]
    },
    {
      id: 2,
      documentId: 2,
      document: "research_paper_ai.pdf",
      vaultId: 2,
      status: "failed",
      startTime: "2024-06-19 15:00:00",
      endTime: "2024-06-19 15:03:30",
      steps: [
        {
          id: 1,
          name: "Text Extraction",
          status: "completed",
          startTime: "2024-06-19 15:00:00",
          endTime: "2024-06-19 15:01:20",
          duration: 80,
          output: {
            type: "text",
            content: "Abstract: This paper presents a novel approach to artificial intelligence...",
            metadata: { pages: 12, characters: 45600, words: 7800 }
          }
        },
        {
          id: 2,
          name: "Document Summarization",
          status: "failed",
          startTime: "2024-06-19 15:01:20",
          endTime: "2024-06-19 15:03:30",
          duration: 130,
          error: {
            code: "RATE_LIMIT_EXCEEDED",
            message: "API rate limit exceeded. Please try again later.",
            details: "OpenAI API returned 429 status code"
          }
        },
        {
          id: 3,
          name: "Entity Extraction",
          status: "skipped",
          reason: "Previous step failed"
        },
        {
          id: 4,
          name: "Key Information Extraction",
          status: "skipped",
          reason: "Previous step failed"
        }
      ]
    }
  ];

  const [selectedPipeline, setSelectedPipeline] = useState<number | null>(null);
  const [selectedStep, setSelectedStep] = useState<number | null>(null);
  const [isStepDialogOpen, setIsStepDialogOpen] = useState(false);

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

  const handleCreateVault = () => {
    if (!newVault.name.trim()) {
      toast({
        title: "Error",
        description: "Vault name is required",
        variant: "destructive",
      });
      return;
    }

    if (newVault.createIndex && !newVault.indexName.trim()) {
      toast({
        title: "Error",
        description: "Index name is required when creating an index",
        variant: "destructive",
      });
      return;
    }

    toast({
      title: "Success",
      description: `Vault "${newVault.name}" created successfully${newVault.createIndex ? ' with search index' : ''}`,
    });

    setNewVault({ 
      name: "", 
      description: "",
      createIndex: false,
      indexName: "",
      dataStore: "elasticsearch",
      embeddingModel: "text-embedding-ada-002"
    });
    setIsCreateDialogOpen(false);
  };

  const handleAddIndexField = () => {
    if (!newField.name.trim()) {
      toast({
        title: "Error",
        description: "Field name is required",
        variant: "destructive",
      });
      return;
    }

    const newId = Math.max(...indexFields.map(f => f.id)) + 1;
    setIndexFields([...indexFields, { ...newField, id: newId }]);
    setNewField({ name: "", type: "text", searchable: true, facetable: false });
    
    toast({
      title: "Success", 
      description: "Index field added successfully",
    });
  };

  const handleRemoveIndexField = (fieldId: number) => {
    setIndexFields(indexFields.filter(f => f.id !== fieldId));
    toast({
      title: "Success",
      description: "Index field removed successfully",
    });
  };

  const handleUpdateIndexField = (fieldId: number, updates: Partial<typeof indexFields[0]>) => {
    setIndexFields(indexFields.map(f => f.id === fieldId ? { ...f, ...updates } : f));
  };

  const handleSaveIndexConfiguration = () => {
    toast({
      title: "Success",
      description: "Index configuration saved successfully",
    });
    setIsEditingFields(false);
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

  const vaultPipelines = selectedVault ? processingPipelines.filter(pipeline => pipeline.vaultId === selectedVault) : [];
  const currentPipeline = selectedPipeline ? vaultPipelines.find(p => p.id === selectedPipeline) : null;
  const currentStep = selectedStep && currentPipeline ? currentPipeline.steps.find(s => s.id === selectedStep) : null;

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

      case "entities":
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              {step.output.content.map((entity: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <Badge variant="outline">{entity.type}</Badge>
                    <span className="font-medium">{entity.value}</span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {Math.round(entity.confidence * 100)}% confidence
                  </div>
                </div>
              ))}
            </div>
            <div className="text-sm">
              <Label>Total Entities</Label>
              <p>{step.output.metadata.total_entities}</p>
            </div>
          </div>
        );

      case "key_info":
        return (
          <div className="space-y-4">
            <div className="grid gap-4">
              {Object.entries(step.output.content).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center p-3 border rounded-lg">
                  <Label className="capitalize">{key.replace(/_/g, ' ')}</Label>
                  <span className="font-medium">
                    {Array.isArray(value) ? value.join(', ') : String(value)}
                  </span>
                </div>
              ))}
            </div>
            <div className="text-sm">
              <Label>Confidence Score</Label>
              <p>{Math.round(step.output.metadata.confidence_score * 100)}%</p>
            </div>
          </div>
        );

      default:
        return <p className="text-muted-foreground">Unknown output type</p>;
    }
  };

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
          <div className="flex-1">
            <h2 className="text-3xl font-bold tracking-tight">{currentVault.name}</h2>
            <p className="text-muted-foreground">
              {currentVault.description}
            </p>
          </div>
          {currentVault.hasIndex && (
            <Badge variant="outline" className="bg-blue-50">
              <Database className="h-3 w-3 mr-1" />
              Index: {currentVault.indexName}
            </Badge>
          )}
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

        <div className="flex space-x-4">
          <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
            <DialogTrigger asChild>
              <Button size="lg" className="px-8">
                <Upload className="h-5 w-5 mr-2" />
                Upload & Configure Documents
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Upload & Configure Documents</DialogTitle>
                <DialogDescription>
                  Upload files and configure processing settings for {currentVault.name}.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-6 lg:grid-cols-2 py-4">
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

                    <div className="flex items-center justify-between">
                      <div>
                        <Label htmlFor="indexing-switch">Enable Search Indexing</Label>
                        <p className="text-sm text-muted-foreground">
                          Create searchable index for documents
                        </p>
                      </div>
                      <Switch
                        id="indexing-switch"
                        checked={enableIndexing}
                        onCheckedChange={setEnableIndexing}
                      />
                    </div>

                    {enableIndexing && (
                      <div className="space-y-4 p-4 border rounded-lg bg-muted/20">
                        <div className="grid gap-4 md:grid-cols-2">
                          <div>
                            <Label htmlFor="index-name">Index Name</Label>
                            <Input
                              id="index-name"
                              value={indexName}
                              onChange={(e) => setIndexName(e.target.value)}
                              placeholder="Enter index name"
                            />
                          </div>
                          <div>
                            <Label htmlFor="data-store">Data Store</Label>
                            <Select value={indexDataStore} onValueChange={setIndexDataStore}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="elasticsearch">Elasticsearch</SelectItem>
                                <SelectItem value="opensearch">OpenSearch</SelectItem>
                                <SelectItem value="pinecone">Pinecone</SelectItem>
                                <SelectItem value="weaviate">Weaviate</SelectItem>
                                <SelectItem value="qdrant">Qdrant</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div>
                          <Label htmlFor="embedding-model">Embedding Model</Label>
                          <Select 
                            value={embeddingModel} 
                            onValueChange={setEmbeddingModel}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="text-embedding-ada-002">OpenAI Ada-002</SelectItem>
                              <SelectItem value="text-embedding-3-small">OpenAI 3-Small</SelectItem>
                              <SelectItem value="text-embedding-3-large">OpenAI 3-Large</SelectItem>
                              <SelectItem value="sentence-transformers">Sentence Transformers</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    )}

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
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsUploadDialogOpen(false)}>
                  Close
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {currentVault.hasIndex && (
            <Dialog open={isIndexDialogOpen} onOpenChange={setIsIndexDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" size="lg" className="px-8">
                  <Database className="h-5 w-5 mr-2" />
                  Configure Search Index
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Search Index Configuration</DialogTitle>
                  <DialogDescription>
                    Configure the search index fields and their properties for {currentVault.name}.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-6 py-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Index Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid gap-4 md:grid-cols-3">
                        <div>
                          <Label className="text-sm font-medium">Index Name</Label>
                          <p className="text-sm text-muted-foreground">{currentVault.indexName}</p>
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Data Store</Label>
                          <p className="text-sm text-muted-foreground capitalize">{currentVault.dataStore}</p>
                        </div>
                        <div>
                          <Label className="text-sm font-medium">Status</Label>
                          <Badge variant="default">Active</Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <div>
                          <CardTitle>Index Fields</CardTitle>
                          <CardDescription>
                            Configure which fields are indexed and their search properties.
                          </CardDescription>
                        </div>
                        <div className="flex space-x-2">
                          {isEditingFields ? (
                            <Button size="sm" onClick={handleSaveIndexConfiguration}>
                              <Save className="h-4 w-4 mr-2" />
                              Save Changes
                            </Button>
                          ) : (
                            <Button size="sm" variant="outline" onClick={() => setIsEditingFields(true)}>
                              <Edit className="h-4 w-4 mr-2" />
                              Edit Fields
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Field Name</TableHead>
                              <TableHead>Type</TableHead>
                              <TableHead>Searchable</TableHead>
                              <TableHead>Facetable</TableHead>
                              {isEditingFields && <TableHead>Actions</TableHead>}
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {indexFields.map((field) => (
                              <TableRow key={field.id}>
                                <TableCell className="font-medium">{field.name}</TableCell>
                                <TableCell>
                                  {isEditingFields ? (
                                    <Select 
                                      value={field.type} 
                                      onValueChange={(value) => handleUpdateIndexField(field.id, { type: value })}
                                    >
                                      <SelectTrigger className="w-32">
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="text">Text</SelectItem>
                                        <SelectItem value="keyword">Keyword</SelectItem>
                                        <SelectItem value="date">Date</SelectItem>
                                        <SelectItem value="number">Number</SelectItem>
                                        <SelectItem value="boolean">Boolean</SelectItem>
                                      </SelectContent>
                                    </Select>
                                  ) : (
                                    <Badge variant="outline">{field.type}</Badge>
                                  )}
                                </TableCell>
                                <TableCell>
                                  {isEditingFields ? (
                                    <Checkbox
                                      checked={field.searchable}
                                      onCheckedChange={(checked) => 
                                        handleUpdateIndexField(field.id, { searchable: !!checked })
                                      }
                                    />
                                  ) : (
                                    <Badge variant={field.searchable ? "default" : "secondary"}>
                                      {field.searchable ? "Yes" : "No"}
                                    </Badge>
                                  )}
                                </TableCell>
                                <TableCell>
                                  {isEditingFields ? (
                                    <Checkbox
                                      checked={field.facetable}
                                      onCheckedChange={(checked) => 
                                        handleUpdateIndexField(field.id, { facetable: !!checked })
                                      }
                                    />
                                  ) : (
                                    <Badge variant={field.facetable ? "default" : "secondary"}>
                                      {field.facetable ? "Yes" : "No"}
                                    </Badge>
                                  )}
                                </TableCell>
                                {isEditingFields && (
                                  <TableCell>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleRemoveIndexField(field.id)}
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </Button>
                                  </TableCell>
                                )}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>

                        {isEditingFields && (
                          <Card>
                            <CardHeader>
                              <CardTitle className="text-lg">Add New Field</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                  <Label htmlFor="new-field-name">Field Name</Label>
                                  <Input
                                    id="new-field-name"
                                    value={newField.name}
                                    onChange={(e) => setNewField({ ...newField, name: e.target.value })}
                                    placeholder="Enter field name"
                                  />
                                </div>
                                <div>
                                  <Label htmlFor="new-field-type">Field Type</Label>
                                  <Select 
                                    value={newField.type} 
                                    onValueChange={(value) => setNewField({ ...newField, type: value })}
                                  >
                                    <SelectTrigger>
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="text">Text</SelectItem>
                                      <SelectItem value="keyword">Keyword</SelectItem>
                                      <SelectItem value="date">Date</SelectItem>
                                      <SelectItem value="number">Number</SelectItem>
                                      <SelectItem value="boolean">Boolean</SelectItem>
                                    </SelectContent>
                                  </Select>
                                </div>
                              </div>
                              <div className="flex items-center space-x-6">
                                <div className="flex items-center space-x-2">
                                  <Checkbox
                                    id="new-field-searchable"
                                    checked={newField.searchable}
                                    onCheckedChange={(checked) => 
                                      setNewField({ ...newField, searchable: !!checked })
                                    }
                                  />
                                  <Label htmlFor="new-field-searchable">Searchable</Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <Checkbox
                                    id="new-field-facetable"
                                    checked={newField.facetable}
                                    onCheckedChange={(checked) => 
                                      setNewField({ ...newField, facetable: !!checked })
                                    }
                                  />
                                  <Label htmlFor="new-field-facetable">Facetable</Label>
                                </div>
                              </div>
                              <Button onClick={handleAddIndexField}>
                                <Plus className="h-4 w-4 mr-2" />
                                Add Field
                              </Button>
                            </CardContent>
                          </Card>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsIndexDialogOpen(false)}>
                    Close
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
        </div>

        <Tabs defaultValue="documents" className="space-y-6">
          <TabsList>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="processing">Processing Status</TabsTrigger>
            <TabsTrigger value="pipeline">Processing Pipeline</TabsTrigger>
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

          <TabsContent value="pipeline">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Processing Pipelines</CardTitle>
                  <CardDescription>
                    View the processing pipeline flow and step outputs for documents in this vault.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {vaultPipelines.map((pipeline) => (
                      <Card key={pipeline.id} className="border">
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <FileText className="h-5 w-5 text-muted-foreground" />
                              <div>
                                <CardTitle className="text-lg">{pipeline.document}</CardTitle>
                                <CardDescription>
                                  Started: {pipeline.startTime}
                                  {pipeline.endTime && ` • Completed: ${pipeline.endTime}`}
                                </CardDescription>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Badge
                                variant={
                                  pipeline.status === "completed"
                                    ? "default"
                                    : pipeline.status === "failed"
                                    ? "destructive"
                                    : "secondary"
                                }
                              >
                                {pipeline.status}
                              </Badge>
                              {pipeline.status === "failed" && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleRetryPipeline(pipeline.id)}
                                >
                                  <RefreshCw className="h-4 w-4 mr-2" />
                                  Retry
                                </Button>
                              )}
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-4">
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

                            <div className="grid gap-2 md:grid-cols-4 text-sm">
                              {pipeline.steps.map((step) => (
                                <div
                                  key={step.id}
                                  className="flex items-center justify-between p-2 border rounded cursor-pointer hover:bg-muted/50"
                                  onClick={() => handleViewStepOutput(pipeline.id, step.id)}
                                >
                                  <div className="flex items-center space-x-2">
                                    {getStepStatusIcon(step.status)}
                                    <span className="truncate">{step.name}</span>
                                  </div>
                                  <Eye className="h-3 w-3 text-muted-foreground" />
                                </div>
                              ))}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
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

        {/* Step Output Dialog */}
        <Dialog open={isStepDialogOpen} onOpenChange={setIsStepDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {currentStep?.name} - {currentPipeline?.document}
              </DialogTitle>
              <DialogDescription>
                Step output and details from the processing pipeline.
              </DialogDescription>
            </DialogHeader>
            {currentStep && (
              <div className="space-y-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStepStatusIcon(currentStep.status)}
                    <div>
                      <h3 className="font-medium">{currentStep.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        Status: {currentStep.status}
                        {currentStep.duration && ` • Duration: ${currentStep.duration}s`}
                      </p>
                    </div>
                  </div>
                  {currentStep.output && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownloadOutput(currentStep.id)}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                  )}
                </div>

                <div className="space-y-4">
                  <div>
                    <Label className="text-base font-medium">Output</Label>
                    <div className="mt-2">
                      {renderStepOutput(currentStep)}
                    </div>
                  </div>

                  {currentStep.startTime && (
                    <div className="grid gap-4 md:grid-cols-2 text-sm">
                      <div>
                        <Label>Start Time</Label>
                        <p>{currentStep.startTime}</p>
                      </div>
                      {currentStep.endTime && (
                        <div>
                          <Label>End Time</Label>
                          <p>{currentStep.endTime}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsStepDialogOpen(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
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
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Vault</DialogTitle>
              <DialogDescription>
                Create a new document vault to organize and process your files.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
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
                    className="min-h-[80px]"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="create-index"
                    checked={newVault.createIndex}
                    onCheckedChange={(checked) => 
                      setNewVault({ ...newVault, createIndex: !!checked })
                    }
                  />
                  <Label htmlFor="create-index" className="text-sm font-medium">
                    Create search index for this vault
                  </Label>
                </div>

                {newVault.createIndex && (
                  <div className="space-y-4 p-4 border rounded-lg bg-muted/20">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div>
                        <Label htmlFor="indexName">Index Name</Label>
                        <Input
                          id="indexName"
                          value={newVault.indexName}
                          onChange={(e) => setNewVault({ ...newVault, indexName: e.target.value })}
                          placeholder="Enter index name"
                        />
                      </div>
                      <div>
                        <Label htmlFor="dataStore">Data Store</Label>
                        <Select 
                          value={newVault.dataStore} 
                          onValueChange={(value) => setNewVault({ ...newVault, dataStore: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="elasticsearch">Elasticsearch</SelectItem>
                            <SelectItem value="opensearch">OpenSearch</SelectItem>
                            <SelectItem value="pinecone">Pinecone</SelectItem>
                            <SelectItem value="weaviate">Weaviate</SelectItem>
                            <SelectItem value="qdrant">Qdrant</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="embeddingModel">Embedding Model</Label>
                      <Select 
                        value={newVault.embeddingModel} 
                        onValueChange={(value) => setNewVault({ ...newVault, embeddingModel: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="text-embedding-ada-002">OpenAI Ada-002</SelectItem>
                          <SelectItem value="text-embedding-3-small">OpenAI 3-Small</SelectItem>
                          <SelectItem value="text-embedding-3-large">OpenAI 3-Large</SelectItem>
                          <SelectItem value="sentence-transformers">Sentence Transformers</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}
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
              <div className="flex items-center space-x-2">
                <Badge
                  variant={vault.status === "active" ? "default" : "secondary"}
                >
                  {vault.status}
                </Badge>
                {vault.hasIndex && (
                  <Badge variant="outline" className="bg-blue-50">
                    <Database className="h-3 w-3 mr-1" />
                    Index
                  </Badge>
                )}
              </div>
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
                {vault.hasIndex && (
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Index:</span>
                    <span className="text-xs bg-blue-100 px-2 py-1 rounded">
                      {vault.indexName}
                    </span>
                  </div>
                )}
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

export default Vaults5;