// useConfigLoader.ts - React hook for managing pipeline configuration

import { useState, useCallback, useEffect } from 'react';
import { ConfigLoader, StepCatalogItem, StepInstance, Pipeline, Service } from '../lib/configLoader';

interface UseConfigLoaderReturn {
  // State
  stepCatalog: StepCatalogItem[];
  services: Service[];
  pipelines: Pipeline[];
  loading: boolean;
  error: string | null;
  
  // Actions
  loadStepCatalog: (yamlContent: string) => Promise<void>;
  loadPipelineConfig: (yamlContent: string) => Promise<void>;
  createStepInstance: (stepId: string, instanceName: string, customSettings?: Record<string, any>) => StepInstance | null;
  validateStepInstance: (stepInstance: StepInstance) => { valid: boolean; errors: string[] };
  filterSteps: (options: { category?: string; tags?: string[]; searchTerm?: string }) => StepCatalogItem[];
  addStepToPipeline: (pipelineName: string, stepInstance: StepInstance) => void;
  removeStepFromPipeline: (pipelineName: string, stepName: string) => void;
  updateStepInPipeline: (pipelineName: string, stepName: string, updates: Partial<StepInstance>) => void;
  reorderStepsInPipeline: (pipelineName: string, fromIndex: number, toIndex: number) => void;
  exportConfig: () => { yaml: string; json: string };
  
  // Computed values
  categories: string[];
  allTags: string[];
}

export const useConfigLoader = (): UseConfigLoaderReturn => {
  const [configLoader] = useState(() => new ConfigLoader());
  const [stepCatalog, setStepCatalog] = useState<StepCatalogItem[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load step catalog
  const loadStepCatalog = useCallback(async (yamlContent: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const catalog = await configLoader.loadStepCatalog(yamlContent);
      setStepCatalog(catalog);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load step catalog');
    } finally {
      setLoading(false);
    }
  }, [configLoader]);

  // Load pipeline configuration
  const loadPipelineConfig = useCallback(async (yamlContent: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const config = await configLoader.loadPipelineConfig(yamlContent);
      setServices(config.services);
      setPipelines(config.pipelines);
      
      // Update step catalog if it's inline
      if (config.step_catalog) {
        setStepCatalog(config.step_catalog);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load pipeline configuration');
    } finally {
      setLoading(false);
    }
  }, [configLoader]);

  // Create step instance
  const createStepInstance = useCallback((
    stepId: string, 
    instanceName: string, 
    customSettings: Record<string, any> = {}
  ) => {
    return configLoader.createStepInstance(stepId, instanceName, customSettings);
  }, [configLoader]);

  // Validate step instance
  const validateStepInstance = useCallback((stepInstance: StepInstance) => {
    return configLoader.validateStepInstance(stepInstance);
  }, [configLoader]);

  // Filter steps
  const filterSteps = useCallback((options: { 
    category?: string; 
    tags?: string[]; 
    searchTerm?: string;
  }) => {
    return configLoader.filterSteps(options);
  }, [configLoader]);

  // Add step to pipeline
  const addStepToPipeline = useCallback((pipelineName: string, stepInstance: StepInstance) => {
    setPipelines(prev => prev.map(pipeline => {
      if (pipeline.name === pipelineName) {
        return {
          ...pipeline,
          steps: [...pipeline.steps, stepInstance],
          execution_sequence: [...pipeline.execution_sequence, stepInstance.name]
        };
      }
      return pipeline;
    }));
  }, []);

  // Remove step from pipeline
  const removeStepFromPipeline = useCallback((pipelineName: string, stepName: string) => {
    setPipelines(prev => prev.map(pipeline => {
      if (pipeline.name === pipelineName) {
        return {
          ...pipeline,
          steps: pipeline.steps.filter(step => step.name !== stepName),
          execution_sequence: pipeline.execution_sequence.filter(name => name !== stepName)
        };
      }
      return pipeline;
    }));
  }, []);

  // Update step in pipeline
  const updateStepInPipeline = useCallback((
    pipelineName: string, 
    stepName: string, 
    updates: Partial<StepInstance>
  ) => {
    setPipelines(prev => prev.map(pipeline => {
      if (pipeline.name === pipelineName) {
        const updatedSteps = pipeline.steps.map(step => {
          if (step.name === stepName) {
            const updatedStep = { ...step, ...updates };
            
            // If name changed, update execution sequence
            if (updates.name && updates.name !== stepName) {
              const executionSequence = pipeline.execution_sequence.map(name => 
                name === stepName ? updates.name! : name
              );
              return { step: updatedStep, executionSequence };
            }
            
            return { step: updatedStep, executionSequence: pipeline.execution_sequence };
          }
          return { step, executionSequence: pipeline.execution_sequence };
        });
        
        // Extract the updated execution sequence (it might have changed if name was updated)
        const newExecutionSequence = updatedSteps[0]?.executionSequence || pipeline.execution_sequence;
        
        return {
          ...pipeline,
          steps: updatedSteps.map(item => item.step),
          execution_sequence: newExecutionSequence
        };
      }
      return pipeline;
    }));
  }, []);

  // Reorder steps in pipeline
  const reorderStepsInPipeline = useCallback((
    pipelineName: string, 
    fromIndex: number, 
    toIndex: number
  ) => {
    setPipelines(prev => prev.map(pipeline => {
      if (pipeline.name === pipelineName) {
        const newExecutionSequence = [...pipeline.execution_sequence];
        const [removed] = newExecutionSequence.splice(fromIndex, 1);
        newExecutionSequence.splice(toIndex, 0, removed);
        
        return {
          ...pipeline,
          execution_sequence: newExecutionSequence
        };
      }
      return pipeline;
    }));
  }, []);

  // Export configuration
  const exportConfig = useCallback(() => {
    return {
      yaml: configLoader.generateYAML(),
      json: configLoader.exportAsJSON()
    };
  }, [configLoader]);

  // Computed values
  const categories = configLoader.getCategories();
  const allTags = configLoader.getAllTags();

  // Update internal loader state when React state changes
  useEffect(() => {
    // This is a bit of a workaround since we can't easily sync the loader's internal state
    // In a real implementation, you might want to refactor this to use a more reactive approach
  }, [stepCatalog, services, pipelines]);

  return {
    // State
    stepCatalog,
    services,
    pipelines,
    loading,
    error,
    
    // Actions
    loadStepCatalog,
    loadPipelineConfig,
    createStepInstance,
    validateStepInstance,
    filterSteps,
    addStepToPipeline,
    removeStepFromPipeline,
    updateStepInPipeline,
    reorderStepsInPipeline,
    exportConfig,
    
    // Computed values
    categories,
    allTags
  };
};
