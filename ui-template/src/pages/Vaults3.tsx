
import React, { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "@/components/ui/pagination";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AlertCircle, CheckCircle, Clock, Download, Upload, Search, Settings, FileText, Eye } from "lucide-react";
import { toast } from "@/hooks/use-toast";

// Mock data
const mockVaults = [
  {
    id: 1,
    name: "Legal Documents",
    description: "Legal contracts and agreements",
    documentCount: 125,
    status: "active",
    createdAt: "2024-01-15",
    hasSearchIndex: true,
    searchIndexName: "legal-docs-index"
  },
  {
    id: 2,
    name: "Financial Reports",
    description: "Quarterly and annual financial reports",
    documentCount: 87,
    status: "active",
    createdAt: "2024-02-01",
    hasSearchIndex: false,
    searchIndexName: ""
  }
];

// Mock documents with more entries to test pagination
const mockDocuments = Array.from({ length: 45 }, (_, i) => ({
  id: i + 1,
  name: `Document_${String(i + 1).padStart(3, '0')}.pdf`,
  size: Math.floor(Math.random() * 5000000) + 100000,
  uploadedAt: new Date(2024, 0, 1 + i).toISOString(),
  status: ['processed', 'processing', 'failed', 'pending'][Math.floor(Math.random() * 4)],
  extractedText: `Sample extracted text from document ${i + 1}...`,
  summary: `This is a summary of document ${i + 1} content...`,
  entities: ['Entity A', 'Entity B', 'Entity C'],
  keyInfo: { title: `Document ${i + 1}`, author: 'John Doe', date: '2024-01-01' }
}));

const mockProcessingSteps = [
  { id: 1, name: 'Text Extraction', status: 'completed', output: 'Extracted 1,245 characters', duration: '2.3s' },
  { id: 2, name: 'Document Summary', status: 'completed', output: 'Generated summary using GPT-4', duration: '5.7s' },
  { id: 3, name: 'Entity Extraction', status: 'completed', output: 'Found 12 entities', duration: '1.8s' },
  { id: 4, name: 'Key Information', status: 'failed', output: '', duration: '0s', error: 'API rate limit exceeded' }
];

const DOCUMENTS_PER_PAGE = 10;

export default function Vaults3() {
  const [selectedVault, setSelectedVault] = useState<number | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [showIndexDialog, setShowIndexDialog] = useState(false);
  const [showProcessingDialog, setShowProcessingDialog] = useState(false);
  const [documentSearch, setDocumentSearch] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  // ... keep existing code (form states and handlers)
  const [newVault, setNewVault] = useState({
    name: "",
    description: "",
    createSearchIndex: false,
    searchIndexName: "",
    dataStore: "",
    embeddingModel: ""
  });

  const [uploadConfig, setUploadConfig] = useState({
    extractText: true,
    generateSummary: true,
    extractEntities: true,
    extractKeyInfo: true,
    llmModel: "gpt-4",
    chunkSize: 1000,
    overlapSize: 200
  });

  const [indexFields, setIndexFields] = useState([
    { name: "title", type: "text", searchable: true, facetable: false },
    { name: "content", type: "text", searchable: true, facetable: false },
    { name: "date", type: "date", searchable: false, facetable: true }
  ]);

  const handleCreateVault = () => {
    console.log("Creating vault:", newVault);
    toast({ title: "Vault created successfully!" });
    setShowCreateDialog(false);
    setNewVault({ name: "", description: "", createSearchIndex: false, searchIndexName: "", dataStore: "", embeddingModel: "" });
  };

  const handleUploadDocuments = () => {
    console.log("Upload configuration:", uploadConfig);
    toast({ title: "Upload configuration saved!" });
    setShowUploadDialog(false);
  };

  const handleSaveIndexConfig = () => {
    console.log("Index configuration:", indexFields);
    toast({ title: "Index configuration saved!" });
    setShowIndexDialog(false);
  };

  const vault = selectedVault ? mockVaults.find(v => v.id === selectedVault) : null;

  // Filter and paginate documents
  const filteredDocuments = mockDocuments.filter(doc => 
    doc.name.toLowerCase().includes(documentSearch.toLowerCase())
  );
  const totalPages = Math.ceil(filteredDocuments.length / DOCUMENTS_PER_PAGE);
  const paginatedDocuments = filteredDocuments.slice(
    (currentPage - 1) * DOCUMENTS_PER_PAGE,
    currentPage * DOCUMENTS_PER_PAGE
  );

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (!selectedVault) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">Vaults</h1>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>Create New Vault</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
              <DialogHeader>
                <DialogTitle>Create New Vault</DialogTitle>
                <DialogDescription>Set up a new document vault with optional search indexing.</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Vault Name</Label>
                  <Input
                    id="name"
                    value={newVault.name}
                    onChange={(e) => setNewVault({ ...newVault, name: e.target.value })}
                    placeholder="Enter vault name"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newVault.description}
                    onChange={(e) => setNewVault({ ...newVault, description: e.target.value })}
                    placeholder="Enter vault description"
                  />
                </div>
                <Separator />
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="createIndex"
                    checked={newVault.createSearchIndex}
                    onCheckedChange={(checked) => setNewVault({ ...newVault, createSearchIndex: checked as boolean })}
                  />
                  <Label htmlFor="createIndex">Create Search Index</Label>
                </div>
                {newVault.createSearchIndex && (
                  <div className="grid gap-4 pl-6">
                    <div className="grid gap-2">
                      <Label htmlFor="indexName">Index Name</Label>
                      <Input
                        id="indexName"
                        value={newVault.searchIndexName}
                        onChange={(e) => setNewVault({ ...newVault, searchIndexName: e.target.value })}
                        placeholder="Enter search index name"
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="dataStore">Data Store</Label>
                      <Select value={newVault.dataStore} onValueChange={(value) => setNewVault({ ...newVault, dataStore: value })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select data store" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="elasticsearch">Elasticsearch</SelectItem>
                          <SelectItem value="opensearch">OpenSearch</SelectItem>
                          <SelectItem value="pinecone">Pinecone</SelectItem>
                          <SelectItem value="weaviate">Weaviate</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="embeddingModel">Embedding Model</Label>
                      <Select value={newVault.embeddingModel} onValueChange={(value) => setNewVault({ ...newVault, embeddingModel: value })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select embedding model" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="text-embedding-ada-002">OpenAI Ada v2</SelectItem>
                          <SelectItem value="text-embedding-3-small">OpenAI v3 Small</SelectItem>
                          <SelectItem value="text-embedding-3-large">OpenAI v3 Large</SelectItem>
                          <SelectItem value="sentence-transformers">Sentence Transformers</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
                <Button onClick={handleCreateVault}>Create Vault</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {mockVaults.map((vault) => (
            <Card key={vault.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setSelectedVault(vault.id)}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{vault.name}</CardTitle>
                  <Badge variant={vault.status === 'active' ? 'default' : 'secondary'}>
                    {vault.status}
                  </Badge>
                </div>
                <CardDescription>{vault.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>{vault.documentCount} documents</span>
                  <span>Created {vault.createdAt}</span>
                </div>
                {vault.hasSearchIndex && (
                  <div className="mt-2">
                    <Badge variant="outline" className="text-xs">
                      Search Index: {vault.searchIndexName}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center gap-4 mb-6">
        <Button variant="outline" onClick={() => setSelectedVault(null)}>
          ← Back to Vaults
        </Button>
        <h1 className="text-3xl font-bold">{vault?.name}</h1>
        <Badge variant={vault?.status === 'active' ? 'default' : 'secondary'}>
          {vault?.status}
        </Badge>
      </div>

      <Tabs defaultValue="documents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="search-index">Search Index</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="documents" className="space-y-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search documents..."
                value={documentSearch}
                onChange={(e) => {
                  setDocumentSearch(e.target.value);
                  setCurrentPage(1); // Reset to first page when searching
                }}
                className="w-64"
              />
            </div>
            <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
              <DialogTrigger asChild>
                <Button size="lg" className="h-12 px-8">
                  <Upload className="mr-2 h-4 w-4" />
                  Upload & Configure
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[700px]">
                <DialogHeader>
                  <DialogTitle>Upload & Configure Documents</DialogTitle>
                  <DialogDescription>Configure document processing settings and upload files.</DialogDescription>
                </DialogHeader>
                <div className="grid gap-6 py-4">
                  <div className="space-y-4">
                    <h4 className="font-medium">Processing Configuration</h4>
                    <div className="grid gap-3">
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="extractText"
                          checked={uploadConfig.extractText}
                          onCheckedChange={(checked) => setUploadConfig({ ...uploadConfig, extractText: checked as boolean })}
                        />
                        <Label htmlFor="extractText">Extract Text</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="generateSummary"
                          checked={uploadConfig.generateSummary}
                          onCheckedChange={(checked) => setUploadConfig({ ...uploadConfig, generateSummary: checked as boolean })}
                        />
                        <Label htmlFor="generateSummary">Generate Summary</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="extractEntities"
                          checked={uploadConfig.extractEntities}
                          onCheckedChange={(checked) => setUploadConfig({ ...uploadConfig, extractEntities: checked as boolean })}
                        />
                        <Label htmlFor="extractEntities">Extract Entities</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id="extractKeyInfo"
                          checked={uploadConfig.extractKeyInfo}
                          onCheckedChange={(checked) => setUploadConfig({ ...uploadConfig, extractKeyInfo: checked as boolean })}
                        />
                        <Label htmlFor="extractKeyInfo">Extract Key Information</Label>
                      </div>
                    </div>
                  </div>
                  <div className="grid gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="llmModel">LLM Model</Label>
                      <Select value={uploadConfig.llmModel} onValueChange={(value) => setUploadConfig({ ...uploadConfig, llmModel: value })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="gpt-4">GPT-4</SelectItem>
                          <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                          <SelectItem value="claude-3">Claude 3</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="grid gap-2">
                        <Label htmlFor="chunkSize">Chunk Size</Label>
                        <Input
                          id="chunkSize"
                          type="number"
                          value={uploadConfig.chunkSize}
                          onChange={(e) => setUploadConfig({ ...uploadConfig, chunkSize: parseInt(e.target.value) })}
                        />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="overlapSize">Overlap Size</Label>
                        <Input
                          id="overlapSize"
                          type="number"
                          value={uploadConfig.overlapSize}
                          onChange={(e) => setUploadConfig({ ...uploadConfig, overlapSize: parseInt(e.target.value) })}
                        />
                      </div>
                    </div>
                  </div>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <Upload className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-2 text-sm text-gray-600">Click to upload files or drag and drop</p>
                    <p className="text-xs text-gray-500">PDF, DOC, DOCX, TXT files up to 10MB</p>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowUploadDialog(false)}>Cancel</Button>
                  <Button onClick={handleUploadDocuments}>Save Configuration</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedDocuments.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">{doc.name}</TableCell>
                    <TableCell>{formatFileSize(doc.size)}</TableCell>
                    <TableCell>{new Date(doc.uploadedAt).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(doc.status)}>
                        {doc.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedDocument(doc)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedDocument(doc);
                            setShowProcessingDialog(true);
                          }}
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {totalPages > 1 && (
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious 
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    className={currentPage === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                  />
                </PaginationItem>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <PaginationItem key={page}>
                    <PaginationLink
                      onClick={() => setCurrentPage(page)}
                      isActive={currentPage === page}
                      className="cursor-pointer"
                    >
                      {page}
                    </PaginationLink>
                  </PaginationItem>
                ))}
                <PaginationItem>
                  <PaginationNext
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    className={currentPage === totalPages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )}

          {/* Document Details Dialog */}
          <Dialog open={!!selectedDocument && !showProcessingDialog} onOpenChange={() => setSelectedDocument(null)}>
            <DialogContent className="sm:max-w-[800px] max-h-[80vh]">
              <DialogHeader>
                <DialogTitle>{selectedDocument?.name}</DialogTitle>
                <DialogDescription>Document details and extracted information</DialogDescription>
              </DialogHeader>
              <ScrollArea className="max-h-96">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">Extracted Text</h4>
                    <div className="bg-gray-50 p-3 rounded text-sm">
                      {selectedDocument?.extractedText}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Summary</h4>
                    <div className="bg-gray-50 p-3 rounded text-sm">
                      {selectedDocument?.summary}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Entities</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedDocument?.entities.map((entity: string, index: number) => (
                        <Badge key={index} variant="outline">{entity}</Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Key Information</h4>
                    <div className="bg-gray-50 p-3 rounded text-sm">
                      <pre>{JSON.stringify(selectedDocument?.keyInfo, null, 2)}</pre>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </DialogContent>
          </Dialog>

          {/* Processing Pipeline Dialog */}
          <Dialog open={showProcessingDialog} onOpenChange={setShowProcessingDialog}>
            <DialogContent className="sm:max-w-[900px] max-h-[80vh]">
              <DialogHeader>
                <DialogTitle>Processing Pipeline - {selectedDocument?.name}</DialogTitle>
                <DialogDescription>View the processing steps and their outputs for this document</DialogDescription>
              </DialogHeader>
              <ScrollArea className="max-h-96">
                <div className="space-y-4">
                  {mockProcessingSteps.map((step, index) => (
                    <div key={step.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          {step.status === 'completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
                          {step.status === 'processing' && <Clock className="h-5 w-5 text-blue-500" />}
                          {step.status === 'failed' && <AlertCircle className="h-5 w-5 text-red-500" />}
                          <h4 className="font-medium">Step {index + 1}: {step.name}</h4>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge className={getStatusColor(step.status)}>{step.status}</Badge>
                          <span className="text-sm text-muted-foreground">{step.duration}</span>
                        </div>
                      </div>
                      
                      {step.status === 'failed' && step.error && (
                        <div className="bg-red-50 border border-red-200 rounded p-3 mb-3">
                          <div className="flex items-center space-x-2 text-red-800">
                            <AlertCircle className="h-4 w-4" />
                            <span className="font-medium">Error:</span>
                          </div>
                          <p className="text-red-700 text-sm mt-1">{step.error}</p>
                        </div>
                      )}
                      
                      {step.output && (
                        <div className="bg-gray-50 rounded p-3">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">Output:</span>
                            <Button variant="ghost" size="sm">
                              <Download className="h-4 w-4 mr-1" />
                              Download
                            </Button>
                          </div>
                          <p className="text-sm text-gray-700">{step.output}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowProcessingDialog(false)}>Close</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>

        <TabsContent value="search-index" className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Search Index Configuration</h2>
            <Dialog open={showIndexDialog} onOpenChange={setShowIndexDialog}>
              <DialogTrigger asChild>
                <Button>Configure Index</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                  <DialogTitle>Configure Search Index</DialogTitle>
                  <DialogDescription>Manage the fields and settings for the search index.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Field Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Searchable</TableHead>
                        <TableHead>Facetable</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {indexFields.map((field, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Input
                              value={field.name}
                              onChange={(e) => {
                                const newFields = [...indexFields];
                                newFields[index].name = e.target.value;
                                setIndexFields(newFields);
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Select
                              value={field.type}
                              onValueChange={(value) => {
                                const newFields = [...indexFields];
                                newFields[index].type = value;
                                setIndexFields(newFields);
                              }}
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
                          </TableCell>
                          <TableCell>
                            <Checkbox
                              checked={field.searchable}
                              onCheckedChange={(checked) => {
                                const newFields = [...indexFields];
                                newFields[index].searchable = checked as boolean;
                                setIndexFields(newFields);
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Checkbox
                              checked={field.facetable}
                              onCheckedChange={(checked) => {
                                const newFields = [...indexFields];
                                newFields[index].facetable = checked as boolean;
                                setIndexFields(newFields);
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <Button
                    variant="outline"
                    onClick={() => setIndexFields([...indexFields, { name: "", type: "text", searchable: true, facetable: false }])}
                  >
                    Add Field
                  </Button>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowIndexDialog(false)}>Cancel</Button>
                  <Button onClick={handleSaveIndexConfig}>Save Configuration</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {vault?.hasSearchIndex ? (
            <Card>
              <CardHeader>
                <CardTitle>Index: {vault.searchIndexName}</CardTitle>
                <CardDescription>Search index is active and configured</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <Badge variant="default">Active</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Documents Indexed:</span>
                    <span>{vault.documentCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last Updated:</span>
                    <span>2 hours ago</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>No Search Index</CardTitle>
                <CardDescription>This vault doesn't have a search index configured</CardDescription>
              </CardHeader>
              <CardContent>
                <Button>Create Search Index</Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Vault Settings</CardTitle>
              <CardDescription>Manage vault configuration and preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <Label htmlFor="vaultName">Vault Name</Label>
                <Input id="vaultName" value={vault?.name} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="vaultDescription">Description</Label>
                <Textarea id="vaultDescription" value={vault?.description} />
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="autoProcess" />
                <Label htmlFor="autoProcess">Auto-process uploaded documents</Label>
              </div>
              <Button>Save Settings</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
