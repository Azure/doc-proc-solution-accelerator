/**
 * API Manager for communicating with the backend services
 */

// Types based on backend models


export interface ServiceHealth {
  name: string;
  status: 'connected' | 'error';
  message?: string;
  error?: string;
  details?: Record<string, any>;
  response_time_ms?: number;
  last_checked: string;
  endpoint?: string;
}

export interface SystemHealth {
  status: 'connected' | 'error' | 'degraded';
  services: Record<string, ServiceHealth>;
  checked_at: string;
  summary: {
    connected: number;
    failed: number;
    total: number;
  };
}

export interface ServiceCatalogDefinition {
  id: string;
  name: string;
  description: string;
  type: string;
  module_name: string;
  module_path: string;
  class_name: string;
  test_connection?: boolean;
  category?: string;
  version?: string;
  tags?: string[];
  settings_schema?: Record<string, any>;
  ui_metadata?: {
    icon?: string;
    color?: string;
    description_short?: string;
    description_long?: string;
  };
}

export interface ServiceInstanceStatus {
  status: 'connected' | 'error' | 'testing' | 'unknown';
  last_tested?: string;
  error_message?: string;
  test_duration_ms?: number;
}

export interface ServiceInstance {
  id: string;
  name: string;
  description?: string;
  service_catalog_id: string;
  type: string;
  settings: Record<string, any>;
  catalog_definition?: ServiceCatalogDefinition;
  status: string;
  connection_status?: ServiceInstanceStatus;
  category?: string;
  version?: string;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface ServiceCreateRequest {
  name: string;
  description?: string;
  service_catalog_id: string;
  settings: Record<string, any>;
}

export interface ServiceUpdateRequest {
  description?: string;
  settings?: Record<string, any>;
}

export interface ServiceTestConnectionResponse {
  success: boolean;
  status: string;
  message?: string;
  duration_ms?: number;
  tested_at: string;
}

// Step types based on backend models
export interface StepSettingsSchema {
  type: string;
  title?: string;
  description?: string;
  required?: boolean;
  default?: string | number | boolean;
  ui_component?: string;
  service_type?: string;
  enum?: string[];
  min?: number;
  max?: number;
  multipleOf?: number;
  pattern?: string;
}

export interface StepUIMetadata {
  icon?: string;
  description_short?: string;
  description_long?: string;
}

export interface StepCatalogDefinition {
  id: string;
  name: string;
  description: string;
  module_name: string;
  module_path: string;
  class_name: string;
  category?: string;
  version?: string;
  tags?: string[];
  settings_schema?: Record<string, StepSettingsSchema>;
  ui_metadata?: StepUIMetadata;
}

export interface StepInstance {
  id: string;
  name: string;
  description?: string;
  step_catalog_id: string;
  enabled: boolean;
  fail_pipeline_on_error: boolean;
  timeout: number;
  services: string[];
  condition?: string;
  debug_mode: boolean;
  settings: Record<string, any>;
  catalog_definition?: StepCatalogDefinition;
  category?: string;
  version?: string;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface StepInstanceCreateRequest {
  name: string;
  description?: string;
  step_catalog_id: string;
  settings?: Record<string, any>;
  enabled?: boolean;
  fail_pipeline_on_error?: boolean;
  timeout?: number;
  services?: string[];
  condition?: string;
  debug_mode?: boolean;
}

export interface StepInstanceUpdateRequest {
  description?: string;
  settings?: Record<string, any>;
  enabled?: boolean;
  fail_pipeline_on_error?: boolean;
  timeout?: number;
  services?: string[];
  condition?: string;
  debug_mode?: boolean;
}

export interface ApiError {
  message: string;
  status_code: number;
  details?: string;
}

/**
 * API Manager class for handling all backend API communications
 */
export class ApiManager {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = 'http://localhost:8010', timeout: number = 30000) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = timeout;
  }

  /**
   * Generic HTTP request method
   */
  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);
    config.signal = controller.signal;

    try {
      const response = await fetch(url, config);
      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData: ApiError;
        try {
          errorData = await response.json();
        } catch {
          errorData = {
            message: `HTTP ${response.status}: ${response.statusText}`,
            status_code: response.status,
          };
        }
        throw new Error(errorData.message || `Request failed with status ${response.status}`);
      }

      // Handle empty responses
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return {} as T;
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout after ${this.timeout}ms`);
      }
      
      throw error;
    }
  }

  /**
   * GET request
   */
  private async get<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  /**
   * POST request
   */
  private async post<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * PUT request
   */
  private async put<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE request
   */
  private async delete<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // ##################################
  // Health check methods
  async healthCheck(): Promise<SystemHealth> {
    return this.get('/api/health');
  }

  // Service-specific health check
  async serviceHealthCheck(serviceName: string): Promise<ServiceHealth> {
    return this.get(`/api/health/${serviceName}`);
  }

  // ##################################
  // Service Catalog Methods
  async getServiceCatalog(): Promise<ServiceCatalogDefinition[]> {
    return this.get('/api/services/catalog');
  }

  async getCatalogService(serviceId: string): Promise<ServiceCatalogDefinition> {
    return this.get(`/api/services/catalog/${serviceId}`);
  }

  async initializeCatalogServices(): Promise<any> {
    return this.post('/api/services/initialize');
  }

  // Service Instance Methods
  async getServiceInstances(): Promise<ServiceInstance[]> {
    return this.get('/api/services/instances');
  }

  async getServiceInstance(id: string): Promise<ServiceInstance> {
    return this.get(`/api/services/instances/${id}`);
  }

  async createServiceInstance(serviceData: ServiceCreateRequest): Promise<ServiceInstance> {
    return this.post('/api/services/instances', serviceData);
  }

  async updateServiceInstance(id: string, serviceData: ServiceUpdateRequest): Promise<ServiceInstance> {
    return this.put(`/api/services/instances/${id}`, serviceData);
  }

  async deleteServiceInstance(id: string): Promise<{ message: string }> {
    return this.delete(`/api/services/instances/${id}`);
  }

  // Service Instance Connection Testing
  async testServiceConnection(id: string): Promise<ServiceTestConnectionResponse> {
    return this.post(`/api/services/instances/${id}/test-connection`);
  }

  // ##################################
  // Step Catalog Methods
  async getStepCatalog(): Promise<StepCatalogDefinition[]> {
    return this.get('/api/steps/catalog');
  }

  async getCatalogStep(stepId: string): Promise<StepCatalogDefinition> {
    return this.get(`/api/steps/catalog/${stepId}`);
  }

  async initializeCatalogSteps(): Promise<any> {
    return this.post('/api/steps/initialize');
  }

  // Step Instance Methods
  async getStepInstances(): Promise<StepInstance[]> {
    return this.get('/api/steps/instances');
  }

  async getStepInstance(id: string): Promise<StepInstance> {
    return this.get(`/api/steps/instances/${id}`);
  }

  async createStepInstance(stepData: StepInstanceCreateRequest): Promise<StepInstance> {
    return this.post('/api/steps/instances', stepData);
  }

  async updateStepInstance(id: string, stepData: StepInstanceUpdateRequest): Promise<StepInstance> {
    return this.put(`/api/steps/instances/${id}`, stepData);
  }

  async deleteStepInstance(id: string): Promise<{ message: string }> {
    return this.delete(`/api/steps/instances/${id}`);
  }
}

// Create singleton instance
const apiManager = new ApiManager(
  (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000'
);

// Export individual service functions for convenience

export const healthApi = {
  healthCheck: () => apiManager.healthCheck(),
  serviceHealthCheck: (serviceName: string) => apiManager.serviceHealthCheck(serviceName),
};

export const servicesApi = {

  // Service Catalog
  getCatalog: () => apiManager.getServiceCatalog(),
  getCatalogService: (id: string) => apiManager.getCatalogService(id),
  initializeCatalog: () => apiManager.initializeCatalogServices(),

  // Service Instances
  getInstances: () => apiManager.getServiceInstances(),
  getInstance: (id: string) => apiManager.getServiceInstance(id),
  createInstance: (data: ServiceCreateRequest) => apiManager.createServiceInstance(data),
  updateInstance: (id: string, data: ServiceUpdateRequest) => apiManager.updateServiceInstance(id, data),
  deleteInstance: (id: string) => apiManager.deleteServiceInstance(id),

  // Connection Testing
  testConnection: (id: string) => apiManager.testServiceConnection(id),
};

export const stepsApi = {
  // Step Catalog
  getCatalog: () => apiManager.getStepCatalog(),
  getCatalogStep: (id: string) => apiManager.getCatalogStep(id),
  initializeCatalog: () => apiManager.initializeCatalogSteps(),

  // Step Instances
  getInstances: () => apiManager.getStepInstances(),
  getInstance: (id: string) => apiManager.getStepInstance(id),
  createInstance: (data: StepInstanceCreateRequest) => apiManager.createStepInstance(data),
  updateInstance: (id: string, data: StepInstanceUpdateRequest) => apiManager.updateStepInstance(id, data),
  deleteInstance: (id: string) => apiManager.deleteStepInstance(id),
};

// Export the manager instance for advanced usage
export default apiManager;
