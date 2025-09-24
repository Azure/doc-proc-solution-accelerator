
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  TrendingUp,
  Activity,
  RefreshCw,
  Loader2,
  Download
} from "lucide-react";
import { pipelineExecutionStatusApi, PipelineExecutionResult, PipelineExecutionStats, ErrorWithData } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface PipelineMetricsProps {
  pipeline_name: string;
}

const PipelineMetrics = ({ pipeline_name }: PipelineMetricsProps) => {
  const [timeRange, setTimeRange] = useState("4h");
  const [executions, setExecutions] = useState<PipelineExecutionResult[]>([]);
  const [stats, setStats] = useState<PipelineExecutionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  // Helper function to get time cutoff based on selected range
  const getTimeCutoff = (range: string): Date => {
    const now = new Date();
    switch (range) {
      case '1h':
        return new Date(now.getTime() - 1 * 60 * 60 * 1000); // 1 hour ago
      case '4h':
        return new Date(now.getTime() - 4 * 60 * 60 * 1000); // 4 hours ago
      case '24h':
        return new Date(now.getTime() - 24 * 60 * 60 * 1000); // 24 hours ago
      case '7d':
        return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000); // 7 days ago
      case '30d':
        return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000); // 30 days ago
      default:
        return new Date(now.getTime() - 4 * 60 * 60 * 1000); // Default to 4 hours ago
    }
  };

  const loadMetrics = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get higher limit to ensure we have enough data for filtering
      const limit = timeRange === '30d' ? 200 : timeRange === '7d' ? 100 : 50;

      // Load recent executions and stats in parallel
      const [allExecutions, executionStats] = await Promise.all([
        pipelineExecutionStatusApi.getRecentExecutions(pipeline_name, limit, timeRange),
        pipelineExecutionStatusApi.getStats(pipeline_name)
      ]);

      
      setExecutions(allExecutions);
      setStats(executionStats);

    } catch (err) {
      console.error('Error loading pipeline metrics:', err);
      setError(err instanceof ErrorWithData ? err.details || err.message : 'Failed to load pipeline metrics');
      
      toast({
        title: "Failed to load pipeline metrics",
        description: "Please try refreshing the page or check your connection.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Load metrics on component mount and when time range or pipeline changes
  useEffect(() => {
    loadMetrics();
  }, [timeRange, pipeline_name]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'succeeded':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'partialsucceeded':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'succeeded':
        return <Badge className="bg-green-100 text-green-800">Success</Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
      case 'partialsucceeded':
        return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  // Function to download execution data as JSON
  const downloadExecutionJson = async (executionId: string, pipelineName: string, timestamp: string) => {
    try {
      setError(null);
      
      // Fetch the full execution data
      const executionData = await pipelineExecutionStatusApi.getExecution(executionId);
      
      // Create a filename with pipeline name and timestamp
      const date = new Date(timestamp).toISOString().split('T')[0];
      const time = new Date(timestamp).toTimeString().split(' ')[0].replace(/:/g, '-');
      const filename = `${pipelineName}_execution_${date}_${time}.json`;
      
      // Create blob and download
      const blob = new Blob([JSON.stringify(executionData, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast({
        title: "Download started",
        description: `Pipeline execution data downloaded as ${filename}`,
      });
      
    } catch (err) {
      console.error('Error downloading execution data:', err);
      const errorMessage = err instanceof ErrorWithData ? err.details || err.message : 'Failed to download execution data';
      setError(errorMessage);
      
      toast({
        title: "Download failed",
        description: "Failed to download pipeline execution data. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Calculate summary metrics from filtered executions for accurate time-based stats
  const totalExecutions = executions.length;
  const successfulExecutions = executions.filter(e => e.result.toLowerCase() === 'succeeded').length;
  const failedExecutions = executions.filter(e => e.result.toLowerCase() !== 'succeeded').length;
  const averageDuration = executions.length > 0 ? executions.reduce((acc, e) => acc + e.elapsed_time_secs, 0) / executions.length : 0;
  const totalDocuments = executions.reduce((acc, e) => acc + (e.document_results?.length || 0), 0);
  const successRate = totalExecutions > 0 ? Math.round((successfulExecutions / totalExecutions) * 100) : 0;

  if (loading) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
              <p className="text-center text-muted-foreground">Loading pipeline metrics...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="py-8">
            <p className="text-center text-red-600">Error: {error}</p>
            <div className="text-center mt-4">
              <Button onClick={loadMetrics} variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalExecutions}</div>
            <p className="text-xs text-muted-foreground">
              {timeRange === '1h' ? 'Last hour' : 
               timeRange === '4h' ? 'Last 4 hours' :
               timeRange === '24h' ? 'Last 24 hours' :
               timeRange === '7d' ? 'Last 7 days' :
               timeRange === '30d' ? 'Last 30 days' : 'Selected period'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{successRate}%</div>
            <p className="text-xs text-muted-foreground">{successfulExecutions}/{totalExecutions} successful</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDuration(Math.round(averageDuration))}</div>
            <p className="text-xs text-muted-foreground">Per execution</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents Processed</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalDocuments}</div>
            <p className="text-xs text-muted-foreground">Total documents</p>
          </CardContent>
        </Card>
      </div>

      {/* Execution History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Execution History</CardTitle>
              <CardDescription>
                {pipeline_name 
                  ? `Recent execution results for ${pipeline_name}` 
                  : 'Recent pipeline execution results'}
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">Last Hour</SelectItem>
                  <SelectItem value="4h">Last 4 Hours</SelectItem>
                  <SelectItem value="24h">Last 24h</SelectItem>
                  <SelectItem value="7d">Last 7 days</SelectItem>
                  <SelectItem value="30d">Last 30 days</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="sm" onClick={loadMetrics} disabled={loading}>
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {executions.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">
                  {pipeline_name 
                    ? `No execution data available for ${pipeline_name}` 
                    : 'No execution data available'}
                </p>
              </div>
            ) : (
              executions.map((execution) => (
                <div key={execution.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(execution.result.toLowerCase())}
                      <div>
                        <p className="font-medium">{formatTimestamp(execution.started_at || execution.created_at)}</p>
                        <p className="text-sm text-muted-foreground flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <span className="font-medium">{execution.document_results?.length || 0}</span> docs
                          </span>
                          <span className="flex items-center gap-1">
                            <CheckCircle className="h-3 w-3 text-green-500" />
                            {execution.document_results?.filter(d => d.result.toLowerCase() === 'succeeded').length || 0}
                          </span>
                          <span className="flex items-center gap-1">
                            <XCircle className="h-3 w-3 text-red-500" />
                            {execution.document_results?.filter(d => d.result.toLowerCase() === 'failed').length || 0}
                          </span>
                          <span className="flex items-center gap-1">
                            <AlertTriangle className="h-3 w-3 text-yellow-500" />
                            {execution.document_results?.filter(d => d.result.toLowerCase() === 'partialsucceeded').length || 0}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            {formatDuration(Math.round(execution.elapsed_time_secs))}
                          </span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(execution.result.toLowerCase())}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadExecutionJson(
                          execution.id,
                          execution.pipeline_name,
                          execution.started_at || execution.created_at
                        )}
                        className="h-8 w-8 p-0"
                        title="Download execution data as JSON"
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PipelineMetrics;