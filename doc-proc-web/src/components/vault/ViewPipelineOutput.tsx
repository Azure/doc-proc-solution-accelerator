import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { 
  Workflow,
  Activity,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight,
  RefreshCw,
  Loader2,
  Download,
  ArrowDown
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { 
  type Pipeline,
  type PipelineExecutionResult,
  type DocumentExecutionStatus,
  type DocumentInfo,
  pipelineExecutionStatusApi,
  documentStatusApi,
  ErrorWithData
} from "@/lib/api";

// Simplified types for pipeline steps display
interface ProcessingStep {
  id: number;
  name: string;
  status: "succeeded" | "failed" | "skipped";
  startTime: string;
  endTime?: string;
  duration?: number;
  reason?: string;
  error?: string;
  errorTraceBack?: string;
}

interface ViewPipelineOutputProps {
  isOpen: boolean;
  onClose: () => void;
  selectedDocument: DocumentInfo | null;
  pipeline: Pipeline | null;
}

const ViewPipelineOutput = ({ 
  isOpen, 
  onClose, 
  selectedDocument, 
  pipeline,
}: ViewPipelineOutputProps) => {
  const { toast } = useToast();
  
  // State for API data
  const [documentExecution, setDocumentExecution] = useState<PipelineExecutionResult | null>(null);
  const [documentStatus, setDocumentStatus] = useState<DocumentExecutionStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch data when dialog opens
  useEffect(() => {
    if (isOpen && selectedDocument && pipeline) {
      fetchPipelineData();
    }
  }, [isOpen, selectedDocument, pipeline]);

  const fetchPipelineData = async () => {
    if (!selectedDocument || !pipeline) return;

    setLoading(true);
    setError(null);
    
    try {
      // Fetch document status to get batch execution information
      const statusResults = await documentStatusApi.getDocumentStatus([selectedDocument.id]);

      if (statusResults && statusResults.length > 0) {
        const docStatus = statusResults[0];
        setDocumentStatus(docStatus);

        // If we have a batch ID, fetch the pipeline execution for that batch
        if (docStatus.batch_id) {
          const executions = await pipelineExecutionStatusApi.getExecutionsByBatch(docStatus.batch_id);
          
          // Find the execution that matches our pipeline
          const relevantExecution = executions.find(exec => 
            exec.pipeline_name === pipeline.name
          ) || null;
          
          setDocumentExecution(relevantExecution);
        }
      }
    } catch (error) {
      console.error('Error fetching pipeline data:', error);
      const errorMessage = error instanceof ErrorWithData 
        ? error.details || error.message 
        : 'Failed to fetch pipeline execution data';
      
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadResults = async () => {
    if (!documentExecution || !selectedDocument) {
      toast({
        title: "Error",
        description: "No document execution data available to download",
        variant: "destructive",
      });
      return;
    }

    try {
      // Find the document result for our specific document
      const documentResult = documentExecution.document_results.find(
        (result: any) => result.document_id?.unique_id === selectedDocument.id
      );

      if (!documentResult) {
        toast({
          title: "Error",
          description: "No results found for this document",
          variant: "destructive",
        });
        return;
      }

      // Create the JSON data to download
      const downloadData = {
        pipeline_execution_id: documentExecution.id,
        pipeline_name: documentExecution.pipeline_name,
        document_id: selectedDocument.id,
        document_name: selectedDocument.name,
        execution_result: documentExecution.result,
        started_at: documentExecution.started_at,
        completed_at: documentExecution.completed_at,
        elapsed_time_secs: documentExecution.elapsed_time_secs,
        document_result: documentResult,
        downloaded_at: new Date().toISOString()
      };

      // Create and trigger download
      const blob = new Blob([JSON.stringify(downloadData, null, 2)], {
        type: 'application/json'
      });
      
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${selectedDocument.name.replace(/\.[^/.]+$/, "")}-pipeline-results.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast({
        title: "Download Started",
        description: "Document results have been downloaded as JSON",
      });
    } catch (error) {
      console.error('Error downloading results:', error);
      toast({
        title: "Download Failed",
        description: "Failed to download document results",
        variant: "destructive",
      });
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "processing":
        return <Activity className="h-4 w-4 text-blue-500" />;
      case "active":
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
      case "failed":
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

  // Transform pipeline steps for rendering
  const getPipelineSteps = (execution: PipelineExecutionResult): ProcessingStep[] => {
    if (!execution?.document_results || !pipeline) {
      return [];
    }

    // Find the document result for our specific document
    const documentResult = execution.document_results.find(
      (result: any) => result.document_id?.unique_id === selectedDocument.id
    );
    
    const stepResults = documentResult?.step_results || [];
    
    return stepResults.map((step: any, index: number) => {
     
      const status: ProcessingStep['status'] = step.result?.toLowerCase();
      
      return {
        id: index,
        name: step.step_name,
        status,
        startTime: step?.started_at || execution.started_at || '',
        endTime: step?.completed_at || execution.completed_at || '',
        duration: step?.elapsed_time_secs ? Math.round(step.elapsed_time_secs) : undefined,
        reason: step?.reason,
        error: step?.error,
        errorTraceBack: step?.error_traceback,
      };
    }) || [];
  };

  const pipelineSteps = documentExecution ? getPipelineSteps(documentExecution) : [];

  return (
    <>
      {/* Main Pipeline Dialog */}
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-6xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Workflow className="h-5 w-5" />
              Processing Pipeline
              {selectedDocument && (
                <Badge variant="outline">Document ID: {selectedDocument.id}</Badge>
              )}
            </DialogTitle>
            <DialogDescription>
              Detailed view of batch execution and pipeline processing results for this document.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            {loading ? (
              <div className="text-center py-12">
                <Loader2 className="h-8 w-8 mx-auto mb-4 animate-spin text-muted-foreground" />
                <p className="text-muted-foreground">Loading pipeline execution data...</p>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-500 opacity-50" />
                <p className="text-lg font-medium text-red-600 mb-2">Failed to Load Pipeline Data</p>
                <p className="text-sm text-muted-foreground mb-4">{error}</p>
                <Button variant="outline" onClick={fetchPipelineData}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry
                </Button>
              </div>
            ) : !documentExecution ? (
              <div className="text-center py-12 text-muted-foreground">
                <Workflow className="h-16 w-16 mx-auto mb-4 opacity-20" />
                <p className="text-lg font-medium mb-2">No Pipeline Executions Found</p>
                <p className="text-sm">This document has not been processed yet.</p>
                <p className="text-sm">Upload the document to a vault with a configured pipeline to begin processing.</p>
                <p className="text-sm">Ensure the processing worker is properly configured and running.</p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Pipeline Execution Results</h3>
                  <Badge variant="secondary">
                    Document: {selectedDocument.name}
                  </Badge>
                </div>
                
                <div className="border rounded-lg p-6 bg-card">
                      {/* Pipeline Header */}
                      <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center space-x-3">
                          {getStatusIcon(documentExecution.result)}
                          <div>
                            <h4 className="font-medium text-lg">
                              {pipeline?.name} - Document {selectedDocument.name}
                            </h4>
                            <p className="text-sm text-muted-foreground">
                              Pipeline Execution #{documentExecution.id}
                            </p>
                          </div>
                          <Badge 
                            variant={documentExecution.result?.toLowerCase() === "succeeded" ? "default" : 
                                    documentExecution.result?.toLowerCase() === "failed" ? "destructive" : "secondary"}
                            className="capitalize"
                          >
                            {documentExecution.result}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className="text-sm text-muted-foreground text-right">
                            <div>Started: {documentExecution.started_at || 'Unknown'}</div>
                            {documentExecution.completed_at && (
                              <div>Completed: {documentExecution.completed_at}</div>
                            )}
                            <div>Duration: {documentExecution.elapsed_time_secs}s</div>
                          </div>
                        </div>
                      </div>

                      {/* Pipeline Steps Visualization */}
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h5 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
                            Pipeline Steps
                          </h5>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={handleDownloadResults}
                            className="flex items-center gap-2"
                          >
                            <Download className="h-4 w-4" />
                            Download Results JSON
                          </Button>
                        </div>
                        <div className="space-y-3">
                          {pipelineSteps.map((step, index) => (
                            <div key={step.id}>
                              <div className="flex items-center space-x-3 p-3 rounded-lg border bg-background/50">
                                <div
                                  className={`w-10 h-10 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                                    step.status?.toLowerCase() === "succeeded"
                                      ? "border-green-500 bg-green-50"
                                      : step.status?.toLowerCase() === "failed"
                                      ? "border-red-500 bg-red-50"
                                      : step.status?.toLowerCase() === "running"
                                      ? "border-blue-500 bg-blue-50"
                                      : "border-gray-300 bg-gray-50"
                                  }`}
                                >
                                  {getStepStatusIcon(step.status)}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium truncate">{step.name}</p>
                                  <div className="flex items-center justify-between text-xs text-muted-foreground mt-1">
                                    <span className="capitalize">{step.status}</span>
                                    {step.duration !== undefined && (
                                      <div className="flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        <span>{step.duration}s</span>
                                      </div>
                                    )}
                                  </div>
                                  {/* Show additional details for failed or skipped steps */}
                                  {(step.status?.toLowerCase() === "failed" || step.status?.toLowerCase() === "skipped") && (
                                    <div className="mt-2 space-y-1">
                                      {step.reason && (
                                        <div className="text-xs text-muted-foreground">
                                          <span className="font-medium">Reason:</span> {step.reason}
                                        </div>
                                      )}
                                      {step.error && (
                                        <div className="text-xs text-red-600">
                                          <span className="font-medium">Error:</span> {step.error}
                                        </div>
                                      )}
                                      {step.errorTraceBack && (
                                        <div className="text-xs text-red-600 font-mono bg-red-50 p-2 rounded border max-h-32 overflow-y-auto">
                                          <span className="font-medium font-sans">Stack Trace:</span>
                                          <pre className="whitespace-pre-wrap mt-1">{step.errorTraceBack}</pre>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                              {index < pipelineSteps.length - 1 && (
                                <div className="flex justify-center py-2">
                                  <ArrowDown className="h-4 w-4 text-muted-foreground" />
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Pipeline Summary */}
                      <div className="mt-6 pt-4 border rounded-lg p-4">
                        <div className="grid grid-cols-4 gap-4 text-sm">
                          <div>
                            <Label className="text-xs font-medium text-muted-foreground">Total Steps</Label>
                            <p className="font-medium">{pipelineSteps.length}</p>
                          </div>
                          <div>
                            <Label className="text-xs font-medium text-muted-foreground">Succeeded</Label>
                            <p className="font-medium text-green-600">
                              {pipelineSteps.filter(s => s.status === "succeeded").length}
                            </p>
                          </div>
                          <div>
                            <Label className="text-xs font-medium text-muted-foreground">Skipped</Label>
                            <p className="font-medium text-gray-600">
                              {pipelineSteps.filter(s => s.status === "skipped").length}
                            </p>
                          </div>
                          <div>
                            <Label className="text-xs font-medium text-muted-foreground">Failed</Label>
                            <p className="font-medium text-red-600">
                              {pipelineSteps.filter(s => s.status === "failed").length}
                            </p>
                          </div>
                          <div>
                            <Label className="text-xs font-medium text-muted-foreground">Total Duration</Label>
                            <p className="font-medium">
                              {pipelineSteps.reduce((acc, step) => acc + (step.duration || 0), 0)}s
                            </p>
                          </div>
                        </div>
                        
                        
                      </div>
                </div>
                
                
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ViewPipelineOutput;