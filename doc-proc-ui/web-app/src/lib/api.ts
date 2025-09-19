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

// Vault types based on backend models
export interface VaultStats {
  total_documents: number;
  processed_documents: number;
  pending_documents: number;
  failed_documents: number;
  total_size_bytes: number;
  last_activity?: string;
}

export interface DocumentProcessingConfig {
  auto_process_documents: boolean;
  supported_formats: string[];
}

export interface StorageConfig {
  account_name: string;
  container_name: string;
  credential_type: string;
  connection_string?: string;
}

export interface Vault {
  id: string;
  name: string;
  description?: string;
  status: 'active' | 'inactive' | 'error';
  pipeline_name?: string;
  processing_config: DocumentProcessingConfig;
  storage_config: StorageConfig;
  stats: VaultStats;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// Vault request types
export interface VaultCreateRequest {
  name: string;
  description?: string;
  pipeline_name: string;
  document_processing_config?: DocumentProcessingConfig;
  storage_config?: StorageConfig;
  metadata?: Record<string, any>;
}

export interface VaultUpdateRequest {
  name?: string;
  description?: string;
  pipeline_name?: string;
  document_processing_config?: DocumentProcessingConfig;
  storage_config?: StorageConfig;
  metadata?: Record<string, any>;
}

export interface DocumentInfo {
  id: string;
  name: string;
  size_bytes: number;
  content_type: string;
  upload_date: string;
  processed_date?: string;
  status: string;
  metadata: Record<string, any>;
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

// Pipeline types based on backend models
export interface PipelineSettings {
  enabled: boolean;
  retry_delay: number;
  timeout: number;
  retries: number;
  max_concurrent_runs: number;
}

export interface Pipeline {
  id: string;
  name: string;
  description?: string;
  steps: string[];
  execution_sequence: string[];
  version?: string;
  settings?: PipelineSettings;
  created_at?: string;
  updated_at?: string;
}

export interface CreatePipelineRequest {
  id?: string;
  name: string;
  description?: string;
  steps?: string[];
  execution_sequence?: string[];
  version?: string;
  settings?: PipelineSettings;
}

export interface PipelineUpdateRequest {
  description?: string;
  steps?: string[];
  execution_sequence?: string[];
  version?: string;
  settings?: PipelineSettings;
}


export interface ApiError {
  message: string;
  status_code: number;
  details?: string;
}

export class ErrorWithData extends Error {
  error?: string;
  details?: any;
  data?: any;
  status_code?: number;

  constructor(message: string, status_code?: number, data?: any) {
    super(message);
    this.error = data?.error;
    this.details = data?.details;
    this.status_code = status_code;
    this.data = data;
  }
}

export interface UploadDocumentResponse {
  filename: string;
  document?: DocumentInfo;
  error?: string;
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

    // If body is FormData, browser will set the Content-Type including boundary.
    // Remove any explicit Content-Type so fetch can set the correct multipart header.
    if (config.body instanceof FormData) {
      const headers = config.headers as Record<string, any>;
      if (headers) {
        delete headers['Content-Type'];
        delete headers['content-type'];
      }
    }

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
        throw new ErrorWithData(errorData.message || `Request failed with status ${response.status}`, response.status, errorData);
      }

      // Handle empty responses
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return {} as T;
      }

      return await response.json();
    } catch (error: any) {
      clearTimeout(timeoutId);
      
      if (error && error.name === 'AbortError') {
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

  /**
   * POST FormData request helper
   */
  private async postForm<T = any>(endpoint: string, formData: FormData): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
    });
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

  // ##################################
  // Pipeline Methods
  async getPipelines(): Promise<Pipeline[]> {
    return this.get('/api/pipelines');
  }

  async getPipeline(idOrName: string): Promise<Pipeline> {
    return this.get(`/api/pipelines/${idOrName}`);
  }

  async createPipeline(pipelineData: CreatePipelineRequest): Promise<Pipeline> {
    return this.post('/api/pipelines', pipelineData);
  }

  async updatePipeline(id: string, pipelineData: Pipeline): Promise<Pipeline> {
    return this.put(`/api/pipelines/${id}`, pipelineData);
  }

  async deletePipeline(id: string): Promise<{ message: string }> {
    return this.delete(`/api/pipelines/${id}`);
  }

  // Vault methods
  async getVaults(): Promise<Vault[]> {
    return this.get('/api/vaults');
  }

  async getVault(id: string): Promise<Vault> {
    return this.get(`/api/vaults/${id}`);
  }

  async createVault(vaultData: VaultCreateRequest): Promise<Vault> {
    return this.post('/api/vaults', vaultData);
  }

  async updateVault(id: string, vaultData: VaultUpdateRequest): Promise<Vault> {
    return this.put(`/api/vaults/${id}`, vaultData);
  }

  async deleteVault(id: string): Promise<{ message: string }> {
    return this.delete(`/api/vaults/${id}`);
  }

  async getVaultDocuments(vaultId: string): Promise<DocumentInfo[]> {
    return this.get(`/api/vaults/${vaultId}/documents`);
  }

  async uploadVaultDocuments(vaultId: string, files: File[], overwrite: boolean = false): Promise<UploadDocumentResponse[]> {
    const formData = new FormData();
    // Backend expects the field name 'files' for multiple uploads
    files.forEach((file) => formData.append('files', file));
    formData.append('overwrite', overwrite.toString());
    return this.postForm(`/api/vaults/${vaultId}/upload`, formData);
  }

  /**
   * Upload a single document with progress callback using XMLHttpRequest
   * Returns the server response for the single-file upload (the backend returns an array; we resolve the first item)
   */
  async uploadVaultDocumentWithProgress(
    vaultId: string,
    file: File,
    onProgress?: (percent: number) => void
  ): Promise<UploadDocumentResponse> {
    return new Promise((resolve) => {
      const url = `${this.baseUrl}/api/vaults/${vaultId}/upload`;
      const xhr = new XMLHttpRequest();

      xhr.open('POST', url);

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const json = JSON.parse(xhr.responseText);
            // Backend returns a list of results for files; return the first entry when uploading one file
            if (Array.isArray(json) && json.length > 0) {
              resolve(json[0]);
              return;
            }
            resolve(json as UploadDocumentResponse);
          } catch (e) {
            resolve({ filename: file.name, error: 'Invalid server response' });
          }
        } else {
          let message = `HTTP ${xhr.status}: ${xhr.statusText}`;
          try {
            const err = JSON.parse(xhr.responseText);
            if (err && err.message) message = err.message;
          } catch {}
          resolve({ filename: file.name, error: message });
        }
      };

      xhr.onerror = () => {
        resolve({ filename: file.name, error: 'Network error' });
      };

      xhr.upload.onprogress = (event: ProgressEvent<EventTarget>) => {
        if (event.lengthComputable && onProgress) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      };

      const formData = new FormData();
      formData.append('files', file);
      xhr.send(formData);
    });
  }

  async processVault(id: string, documentIds?: string[], forceReprocess = false): Promise<any> {
    return this.post(`/api/vaults/${id}/process`, { 
      document_ids: documentIds, 
      force_reprocess: forceReprocess 
    });
  }
}

// Create singleton instance
const apiManager = new ApiManager(
  (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8010'
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

export const pipelinesApi = {
  // Pipeline Methods
  getPipelines: () => apiManager.getPipelines(),
  getPipeline: (idOrName: string) => apiManager.getPipeline(idOrName),
  createPipeline: (data: CreatePipelineRequest) => apiManager.createPipeline(data),
  updatePipeline: (id: string, data: Pipeline) => apiManager.updatePipeline(id, data),
  deletePipeline: (id: string) => apiManager.deletePipeline(id),
};

export const vaultsApi = {
  // Vault Methods
  getVaults: () => apiManager.getVaults(),
  getVault: (id: string) => apiManager.getVault(id),
  createVault: (data: VaultCreateRequest) => apiManager.createVault(data),
  updateVault: (id: string, data: VaultUpdateRequest) => apiManager.updateVault(id, data),
  deleteVault: (id: string) => apiManager.deleteVault(id),
  getVaultDocuments: (vaultId: string) => apiManager.getVaultDocuments(vaultId),
  uploadVaultDocuments: (vaultId: string, files: File[], overwrite?: boolean) => apiManager.uploadVaultDocuments(vaultId, files, overwrite),
  uploadVaultDocumentWithProgress: (vaultId: string, file: File, onProgress?: (p:number)=>void) => apiManager.uploadVaultDocumentWithProgress(vaultId, file, onProgress),
  processVault: (id: string, documentIds?: string[], forceReprocess?: boolean) => apiManager.processVault(id, documentIds, forceReprocess),
};

// Export the manager instance for advanced usage
export default apiManager;
