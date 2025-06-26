
import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Search } from "lucide-react";
import StepDefinitionCard, { StepDefinition } from "../components/pipeline/StepDefinition";
import StepDefinitionDialog from "../components/pipeline/StepDefinitionDialog";

const mockSteps: StepDefinition[] = [
  // Ingestion Steps
  {
    id: "1",
    name: "Azure Blob Storage Connector",
    description: "Ingest documents from Azure Blob Storage containers",
    type: "connector",
    module: "azure-blob-connector",
    version: "2.1.0",
    defaultConfig: {
      connectionString: "",
      containerName: "",
      batchSize: 50
    },
    created: "2024-01-15T10:00:00Z",
    updated: "2024-01-20T14:30:00Z"
  },
  {
    id: "2",
    name: "SharePoint Document Connector",
    description: "Ingest documents from SharePoint document libraries",
    type: "connector",
    module: "sharepoint-connector",
    version: "1.3.0",
    defaultConfig: {
      siteUrl: "",
      libraryName: "",
      credentials: {}
    },
    created: "2024-01-12T09:00:00Z",
    updated: "2024-01-18T11:20:00Z"
  },
  {
    id: "3",
    name: "File System Connector",
    description: "Ingest documents from local or network file systems",
    type: "connector",
    module: "filesystem-connector",
    version: "1.0.5",
    defaultConfig: {
      rootPath: "",
      fileTypes: ["pdf", "docx", "txt"],
      recursive: true
    },
    created: "2024-02-01T08:30:00Z",
    updated: "2024-02-05T16:45:00Z"
  },
  
  // Text Extraction Steps
  {
    id: "4",
    name: "Azure Document Intelligence",
    description: "Extract text and layout from documents using Azure AI",
    type: "extractor",
    module: "azure-document-intelligence",
    version: "1.2.0",
    defaultConfig: {
      endpoint: "",
      apiKey: "",
      modelId: "prebuilt-document"
    },
    created: "2024-01-15T10:00:00Z",
    updated: "2024-01-20T14:30:00Z"
  },
  {
    id: "5",
    name: "OCR Text Extractor",
    description: "Extract text from images and scanned documents using OCR",
    type: "extractor",
    module: "ocr-text-extractor",
    version: "2.0.1",
    defaultConfig: {
      language: "en",
      confidence: 0.7,
      preprocessImage: true
    },
    created: "2024-01-08T14:00:00Z",
    updated: "2024-01-25T09:15:00Z"
  },
  {
    id: "6",
    name: "PDF Text Extractor",
    description: "Extract text content directly from PDF documents",
    type: "extractor",
    module: "pdf-text-extractor",
    version: "1.5.2",
    defaultConfig: {
      preserveFormatting: true,
      extractImages: false,
      pageRange: "all"
    },
    created: "2024-01-05T11:30:00Z",
    updated: "2024-01-22T13:40:00Z"
  },

  // NLP and Entity Extraction Steps
  {
    id: "7",
    name: "NLP Entity Extractor",
    description: "Extract entities using natural language processing",
    type: "extractor",
    module: "nlp-entity-extractor",
    version: "2.1.0",
    defaultConfig: {
      entities: ["PERSON", "ORG", "DATE", "MONEY"],
      confidence: 0.8,
      customModels: []
    },
    created: "2024-01-10T09:00:00Z",
    updated: "2024-01-15T16:45:00Z"
  },
  {
    id: "8",
    name: "Sentiment Analysis",
    description: "Analyze sentiment and emotional tone of text content",
    type: "extractor",
    module: "sentiment-analyzer",
    version: "1.4.0",
    defaultConfig: {
      model: "transformer-based",
      languages: ["en", "es", "fr"],
      includeScores: true
    },
    created: "2024-01-18T10:15:00Z",
    updated: "2024-02-02T14:20:00Z"
  },
  {
    id: "9",
    name: "Topic Classification",
    description: "Classify documents into predefined topics and categories",
    type: "extractor",
    module: "topic-classifier",
    version: "1.6.0",
    defaultConfig: {
      categories: ["legal", "financial", "technical", "medical"],
      threshold: 0.75,
      multiLabel: true
    },
    created: "2024-01-20T12:00:00Z",
    updated: "2024-02-08T10:30:00Z"
  },
  {
    id: "10",
    name: "Key Phrase Extraction",
    description: "Extract key phrases and important terms from documents",
    type: "extractor",
    module: "keyphrase-extractor",
    version: "1.3.1",
    defaultConfig: {
      maxPhrases: 20,
      minScore: 0.6,
      filterStopwords: true
    },
    created: "2024-01-22T15:45:00Z",
    updated: "2024-02-10T11:25:00Z"
  },

  // AI-Based Processing Steps
  {
    id: "11",
    name: "OpenAI GPT Summarizer",
    description: "Generate summaries using OpenAI GPT models",
    type: "ai-prompt",
    module: "openai-gpt-summarizer",
    version: "1.0.5",
    defaultConfig: {
      model: "gpt-4",
      maxTokens: 500,
      temperature: 0.3,
      prompt: "Summarize the following document:"
    },
    created: "2024-02-01T11:00:00Z",
    updated: "2024-02-05T13:20:00Z"
  },
  {
    id: "12",
    name: "Claude Document Analyzer",
    description: "Analyze and process documents using Anthropic Claude",
    type: "ai-prompt",
    module: "claude-analyzer",
    version: "1.2.0",
    defaultConfig: {
      model: "claude-3-sonnet",
      maxTokens: 1000,
      temperature: 0.2,
      systemPrompt: "You are a document analysis expert."
    },
    created: "2024-02-03T09:30:00Z",
    updated: "2024-02-12T16:10:00Z"
  },
  {
    id: "13",
    name: "Custom AI Prompt",
    description: "Execute custom AI prompts for specialized document processing",
    type: "ai-prompt",
    module: "custom-ai-prompt",
    version: "2.0.0",
    defaultConfig: {
      provider: "openai",
      model: "gpt-4",
      customPrompt: "",
      outputFormat: "json"
    },
    created: "2024-02-05T14:20:00Z",
    updated: "2024-02-15T12:35:00Z"
  },

  // Image Processing Steps
  {
    id: "14",
    name: "Image Content Extractor",
    description: "Extract and describe visual content from images in documents",
    type: "image-extractor",
    module: "image-content-extractor",
    version: "1.1.0",
    defaultConfig: {
      extractText: true,
      describeContent: true,
      detectObjects: false,
      confidence: 0.8
    },
    created: "2024-01-28T13:15:00Z",
    updated: "2024-02-07T15:50:00Z"
  },
  {
    id: "15",
    name: "Chart Data Extractor",
    description: "Extract data and insights from charts and graphs in documents",
    type: "image-extractor",
    module: "chart-data-extractor",
    version: "1.0.3",
    defaultConfig: {
      chartTypes: ["bar", "line", "pie", "scatter"],
      extractValues: true,
      preserveLabels: true
    },
    created: "2024-02-10T10:45:00Z",
    updated: "2024-02-18T14:25:00Z"
  },

  // Output Steps
  {
    id: "16",
    name: "Cosmos DB Writer",
    description: "Store processed documents and metadata in Azure Cosmos DB",
    type: "output",
    module: "cosmosdb-writer",
    version: "1.4.0",
    defaultConfig: {
      connectionString: "",
      databaseName: "documents",
      containerName: "processed",
      partitionKey: "/documentId"
    },
    created: "2024-01-25T11:20:00Z",
    updated: "2024-02-08T09:40:00Z"
  },
  {
    id: "17",
    name: "Search Index Writer",
    description: "Index processed content in Azure AI Search for full-text search",
    type: "output",
    module: "search-index-writer",
    version: "1.3.2",
    defaultConfig: {
      searchService: "",
      indexName: "documents",
      apiKey: "",
      includeSuggestions: true
    },
    created: "2024-01-30T16:10:00Z",
    updated: "2024-02-12T13:55:00Z"
  }
];

const Steps = () => {
  const [steps, setSteps] = useState<StepDefinition[]>(mockSteps);
  const [selectedStep, setSelectedStep] = useState<StepDefinition | undefined>();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredAndGroupedSteps = useMemo(() => {
    const filtered = steps.filter(step => 
      step.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      step.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      step.type.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const grouped = filtered.reduce((acc, step) => {
      const type = step.type;
      if (!acc[type]) {
        acc[type] = [];
      }
      acc[type].push(step);
      return acc;
    }, {} as Record<string, StepDefinition[]>);

    return grouped;
  }, [steps, searchQuery]);

  const getTypeDisplayName = (type: string) => {
    switch (type) {
      case 'connector': return 'Data Connectors';
      case 'extractor': return 'Text Extractors';
      case 'image-extractor': return 'Image Processing';
      case 'ai-prompt': return 'AI Processing';
      case 'output': return 'Output Connectors';
      default: return type;
    }
  };

  const handleCreateStep = () => {
    setSelectedStep(undefined);
    setIsDialogOpen(true);
  };

  const handleEditStep = (step: StepDefinition) => {
    setSelectedStep(step);
    setIsDialogOpen(true);
  };

  const handleDeleteStep = (stepId: string) => {
    setSteps(prev => prev.filter(step => step.id !== stepId));
  };

  const handleSaveStep = (stepData: Partial<StepDefinition>) => {
    if (selectedStep) {
      // Edit existing step
      setSteps(prev => prev.map(step => 
        step.id === selectedStep.id 
          ? { ...step, ...stepData }
          : step
      ));
    } else {
      // Create new step
      setSteps(prev => [...prev, stepData as StepDefinition]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Step Definitions</h1>
          <p className="text-muted-foreground">Manage reusable step definitions for your pipelines</p>
        </div>
        <Button onClick={handleCreateStep}>
          <Plus className="h-4 w-4 mr-2" />
          New Step Definition
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search steps..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      <div className="space-y-8">
        {Object.entries(filteredAndGroupedSteps).map(([type, typeSteps]) => (
          <div key={type} className="space-y-4">
            <h2 className="text-xl font-semibold text-foreground">
              {getTypeDisplayName(type)} ({typeSteps.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {typeSteps.map((step) => (
                <StepDefinitionCard
                  key={step.id}
                  step={step}
                  onEdit={handleEditStep}
                  onDelete={handleDeleteStep}
                />
              ))}
            </div>
          </div>
        ))}
        
        {Object.keys(filteredAndGroupedSteps).length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No steps found matching your search.</p>
          </div>
        )}
      </div>

      <StepDefinitionDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        step={selectedStep}
        onSave={handleSaveStep}
      />
    </div>
  );
};

export default Steps;