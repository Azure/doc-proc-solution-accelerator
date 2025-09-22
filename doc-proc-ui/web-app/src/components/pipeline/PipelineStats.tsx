import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Loader2,
  Activity,
  TrendingUp,
  BarChart3,
  FileText
} from "lucide-react";
import { pipelineExecutionsApi, PipelineExecutionStats, ErrorWithData } from "@/lib/api";

interface ExecutionStats {
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  partialSuccessExecutions: number;
  successRate: number;
}

interface DocumentStats {
  succeeded: number;
  failed: number;
  partiallySucceeded: number;
  total: number;
}

interface CombinedStats {
  executions: ExecutionStats;
  documents: DocumentStats;
}

interface PipelineStatsProps {
  pipelineName: string;
  className?: string;
}

const PipelineStats = ({ pipelineName, className = "" }: PipelineStatsProps) => {
  const [stats, setStats] = useState<CombinedStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadStats = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get recent executions to calculate both execution and document stats
        const executions = await pipelineExecutionsApi.getRecentExecutions(pipelineName, 100, "24h");
        
        if (!mounted) return;

        // // Filter executions to last 24 hours
        // const now = new Date();
        // const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        
        // const recentExecutions = executions.filter(execution => {
        //   const executionTime = new Date(execution.started_at || execution.created_at);
        //   return executionTime >= twentyFourHoursAgo;
        // });

        // Calculate execution statistics
        const executionStats = executions.reduce((acc, execution) => {
          acc.totalExecutions++;
          const result = execution.result.toLowerCase();
          if (result === 'succeeded') {
            acc.successfulExecutions++;
          } else if (result === 'partialsucceeded' || result === 'partial' || result === 'partiallysuccessful') {
            acc.partialSuccessExecutions++;
          } else {
            acc.failedExecutions++;
          }
          return acc;
        }, {
          totalExecutions: 0,
          successfulExecutions: 0,
          failedExecutions: 0,
          partialSuccessExecutions: 0,
          successRate: 0
        });

        // Calculate success rate
        if (executionStats.totalExecutions > 0) {
          executionStats.successRate = Math.round(
            ((executionStats.successfulExecutions + executionStats.partialSuccessExecutions) / executionStats.totalExecutions) * 100
          );
        }

        // Calculate document processing statistics
        const documentStats = executions.reduce((acc, execution) => {
          if (execution.document_results) {
            execution.document_results.forEach(docResult => {
              acc.total++;
              const result = docResult.result.toLowerCase();
              if (result === 'succeeded') {
                acc.succeeded++;
              } else if (result === 'partialsucceeded' || result === 'partial' || result === 'partiallysuccessful') {
                acc.partiallySucceeded++;
              } else {
                acc.failed++;
              }
            });
          }
          return acc;
        }, {
          succeeded: 0,
          failed: 0,
          partiallySucceeded: 0,
          total: 0
        });

        setStats({
          executions: executionStats,
          documents: documentStats
        });
      } catch (err) {
        console.error('Error loading pipeline stats:', err);
        if (mounted) {
          setError(err instanceof ErrorWithData ? err.details || err.message : 'Failed to load stats');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadStats();

    return () => {
      mounted = false;
    };
  }, [pipelineName]);

  if (loading) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Loading stats...</span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className={`text-sm text-muted-foreground ${className}`}>
        No data available
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      <div className="flex items-center justify-between gap-3 text-sm">
        {/* Execution Statistics - Left side */}
        <div className="flex items-center space-x-2">
          <Activity className="h-3 w-3 text-muted-foreground" />
          <span className="text-muted-foreground">{stats.executions.totalExecutions} runs</span>
          {stats.executions.totalExecutions > 0 && (
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-sm px-1.5 py-0.5">
              {stats.executions.successRate}%
            </Badge>
          )}
        </div>

        {/* Document Statistics - Right side */}
        <div className="flex items-center space-x-2">
          <FileText className="h-3 w-3 text-muted-foreground" />
          {stats.documents.total === 0 ? (
            <span className="text-muted-foreground">No docs</span>
          ) : (
            <div className="flex items-center space-x-1">
              {stats.documents.succeeded > 0 && (
                <div className="flex items-center space-x-0.5">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  <span className="text-green-700 font-medium">{stats.documents.succeeded}</span>
                </div>
              )}
              
              {stats.documents.partiallySucceeded > 0 && (
                <div className="flex items-center space-x-0.5">
                  <AlertTriangle className="h-3 w-3 text-yellow-500" />
                  <span className="text-yellow-700 font-medium">{stats.documents.partiallySucceeded}</span>
                </div>
              )}
              
              {stats.documents.failed > 0 && (
                <div className="flex items-center space-x-0.5">
                  <XCircle className="h-3 w-3 text-red-500" />
                  <span className="text-red-700 font-medium">{stats.documents.failed}</span>
                </div>
              )}

              <span className="text-muted-foreground">/{stats.documents.total}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PipelineStats;