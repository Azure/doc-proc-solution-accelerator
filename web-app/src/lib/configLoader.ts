// configLoader.ts - Logic for loading and managing pipeline configurations

import yaml from 'js-yaml';

export interface StepCatalogItem {
  id: string;
  name: string;
  description: string;
  type: string;
  module_name: string;
  module_path: string;
  class_name: string;
  tags: string[];
  category: string;
  version: string;
  default_settings: Record<string, any>;
  ui_metadata: {
    icon: string;
    color: string;
    description_long: string;
  };
  config_schema: {
    properties: Record<string, ConfigProperty>;
  };
}

export interface ConfigProperty {
  type: string;
  title: string;
  description: string;
  default?: any;
  required?: boolean;
  minimum?: number;
  maximum?: number;
  multipleOf?: number;
  enum?: string[];
  pattern?: string;
  ui_component?: string;
  service_type?: string;
  properties?: Record<string, ConfigProperty>;
}

export interface Service {
  name: string;
  type: string;
  test_connection: boolean;
  settings: Record<string, any>;
}

export interface StepInstance {
  name: string;
  step_catalog_id?: string; // For catalog-based approach
  template_id?: string; // For template-based approach
  enabled: boolean;
  settings: Record<string, any>;
}

export interface Pipeline {
  name: string;
  description: string;
  updated_at: string;
  version: string;
  steps: StepInstance[];
  execution_sequence: string[];
  settings: {
    enabled: boolean;
    retries: number;
    retry_delay: number;
    timeout: number;
    max_concurrent_runs: number;
    logging: {
      enabled: boolean;
      level: string;
      format: string;
      handlers: Array<{
        type: string;
        level: string;
        filename?: string;
      }>;
    };
  };
}

export interface PipelineConfig {
  step_catalog_path?: string;
  services: Service[];
  pipelines: Pipeline[];
  step_catalog?: StepCatalogItem[]; // For inline catalog
}

export class ConfigLoader {
  private stepCatalog: StepCatalogItem[] = [];
  private services: Service[] = [];
  private pipelines: Pipeline[] = [];

  /**
   * Load step catalog from YAML file
   */
  async loadStepCatalog(yamlContent: string): Promise<StepCatalogItem[]> {
    try {
      const data = yaml.load(yamlContent) as { step_catalog: StepCatalogItem[] };
      this.stepCatalog = data.step_catalog || [];
      return this.stepCatalog;
    } catch (error) {
      console.error('Error loading step catalog:', error);
      throw new Error('Failed to load step catalog');
    }
  }

  /**
   * Load pipeline configuration from YAML file
   */
  async loadPipelineConfig(yamlContent: string): Promise<PipelineConfig> {
    try {
      const config = yaml.load(yamlContent) as PipelineConfig;
      
      this.services = config.services || [];
      this.pipelines = config.pipelines || [];
      
      // If step catalog is inline, load it
      if (config.step_catalog) {
        this.stepCatalog = config.step_catalog;
      }
      
      return config;
    } catch (error) {
      console.error('Error loading pipeline config:', error);
      throw new Error('Failed to load pipeline configuration');
    }
  }

  /**
   * Get step catalog
   */
  getStepCatalog(): StepCatalogItem[] {
    return this.stepCatalog;
  }

  /**
   * Get step by ID from catalog
   */
  getStepById(id: string): StepCatalogItem | undefined {
    return this.stepCatalog.find(step => step.id === id);
  }

  /**
   * Get services
   */
  getServices(): Service[] {
    return this.services;
  }

  /**
   * Get services by type
   */
  getServicesByType(type: string): Service[] {
    return this.services.filter(service => service.type === type);
  }

  /**
   * Get pipelines
   */
  getPipelines(): Pipeline[] {
    return this.pipelines;
  }

  /**
   * Create a new step instance from catalog
   */
  createStepInstance(
    stepId: string, 
    instanceName: string, 
    customSettings: Record<string, any> = {}
  ): StepInstance | null {
    const catalogStep = this.getStepById(stepId);
    if (!catalogStep) {
      console.error(`Step with ID ${stepId} not found in catalog`);
      return null;
    }

    // Merge default settings with custom settings
    const mergedSettings = {
      ...catalogStep.default_settings,
      ...this.getDefaultValuesFromSchema(catalogStep.config_schema),
      ...customSettings
    };

    return {
      name: instanceName,
      step_catalog_id: stepId,
      enabled: true,
      settings: mergedSettings
    };
  }

  /**
   * Extract default values from config schema
   */
  private getDefaultValuesFromSchema(schema: { properties: Record<string, ConfigProperty> }): Record<string, any> {
    const defaults: Record<string, any> = {};
    
    Object.entries(schema.properties).forEach(([key, property]) => {
      if (property.default !== undefined) {
        defaults[key] = property.default;
      }
      
      // Handle nested objects
      if (property.type === 'object' && property.properties) {
        defaults[key] = this.getDefaultValuesFromSchema({ properties: property.properties });
      }
    });
    
    return defaults;
  }

  /**
   * Validate step instance against schema
   */
  validateStepInstance(stepInstance: StepInstance): { valid: boolean; errors: string[] } {
    const catalogStep = this.getStepById(stepInstance.step_catalog_id || '');
    if (!catalogStep) {
      return { valid: false, errors: ['Step not found in catalog'] };
    }

    const errors: string[] = [];
    
    // Validate required fields
    Object.entries(catalogStep.config_schema.properties).forEach(([key, property]) => {
      if (property.required && (stepInstance.settings[key] === undefined || stepInstance.settings[key] === '')) {
        errors.push(`Required field '${property.title || key}' is missing`);
      }
      
      // Validate data types and ranges
      const value = stepInstance.settings[key];
      if (value !== undefined) {
        errors.push(...this.validatePropertyValue(key, property, value));
      }
    });

    return { valid: errors.length === 0, errors };
  }

  /**
   * Validate individual property value
   */
  private validatePropertyValue(key: string, property: ConfigProperty, value: any): string[] {
    const errors: string[] = [];
    
    switch (property.type) {
      case 'integer':
        if (!Number.isInteger(Number(value))) {
          errors.push(`${property.title || key} must be an integer`);
        } else {
          const numValue = Number(value);
          if (property.minimum !== undefined && numValue < property.minimum) {
            errors.push(`${property.title || key} must be at least ${property.minimum}`);
          }
          if (property.maximum !== undefined && numValue > property.maximum) {
            errors.push(`${property.title || key} must be at most ${property.maximum}`);
          }
        }
        break;
        
      case 'number':
        if (isNaN(Number(value))) {
          errors.push(`${property.title || key} must be a number`);
        } else {
          const numValue = Number(value);
          if (property.minimum !== undefined && numValue < property.minimum) {
            errors.push(`${property.title || key} must be at least ${property.minimum}`);
          }
          if (property.maximum !== undefined && numValue > property.maximum) {
            errors.push(`${property.title || key} must be at most ${property.maximum}`);
          }
        }
        break;
        
      case 'string':
        if (typeof value !== 'string') {
          errors.push(`${property.title || key} must be a string`);
        } else {
          if (property.pattern && !new RegExp(property.pattern).test(value)) {
            errors.push(`${property.title || key} does not match required pattern`);
          }
          if (property.enum && !property.enum.includes(value)) {
            errors.push(`${property.title || key} must be one of: ${property.enum.join(', ')}`);
          }
        }
        break;
        
      case 'boolean':
        if (typeof value !== 'boolean') {
          errors.push(`${property.title || key} must be a boolean`);
        }
        break;
    }
    
    return errors;
  }

  /**
   * Generate YAML from current configuration
   */
  generateYAML(): string {
    const config: PipelineConfig = {
      services: this.services,
      pipelines: this.pipelines
    };
    
    // Add step catalog if it exists
    if (this.stepCatalog.length > 0) {
      config.step_catalog = this.stepCatalog;
    }
    
    return yaml.dump(config, { 
      indent: 2,
      lineWidth: -1, // Prevent line wrapping
      noRefs: true // Avoid YAML references
    });
  }

  /**
   * Export pipeline configuration as JSON
   */
  exportAsJSON(): string {
    const config: PipelineConfig = {
      services: this.services,
      pipelines: this.pipelines,
      step_catalog: this.stepCatalog
    };
    
    return JSON.stringify(config, null, 2);
  }

  /**
   * Filter steps by category, tags, or search term
   */
  filterSteps(options: {
    category?: string;
    tags?: string[];
    searchTerm?: string;
  }): StepCatalogItem[] {
    let filtered = [...this.stepCatalog];
    
    if (options.category) {
      filtered = filtered.filter(step => step.category === options.category);
    }
    
    if (options.tags && options.tags.length > 0) {
      filtered = filtered.filter(step => 
        options.tags!.some(tag => step.tags.includes(tag))
      );
    }
    
    if (options.searchTerm) {
      const term = options.searchTerm.toLowerCase();
      filtered = filtered.filter(step =>
        step.name.toLowerCase().includes(term) ||
        step.description.toLowerCase().includes(term) ||
        step.tags.some(tag => tag.toLowerCase().includes(term))
      );
    }
    
    return filtered;
  }

  /**
   * Get available categories
   */
  getCategories(): string[] {
    return Array.from(new Set(this.stepCatalog.map(step => step.category)));
  }

  /**
   * Get all available tags
   */
  getAllTags(): string[] {
    const allTags = this.stepCatalog.flatMap(step => step.tags);
    return Array.from(new Set(allTags));
  }
}
