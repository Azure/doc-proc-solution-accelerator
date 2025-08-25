// Azure AI Search Index configuration for vaults
export interface AzureAISearchConfig {
  endpoint: string;
  apiKey: string;
  indexName: string;
  apiVersion?: string;
}

export interface VaultConfig {
  azureSearch: AzureAISearchConfig;
  // Add other vault-related config here if needed
}

// Example default config (replace with real values or load from env)
const vaultConfig: VaultConfig = {
  azureSearch: {
    endpoint: "https://<your-search-service>.search.windows.net",
    apiKey: "<your-api-key>",
    indexName: "<your-index-name>",
    apiVersion: "2023-11-01",
  },
};

export default vaultConfig;
