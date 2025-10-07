/**
 * Shared crawler settings schema for source instance configuration
 * Based on the backend SourceInstanceCrawlerSettings model
 */

export interface CrawlerSettingSchema {
  type: 'integer' | 'number' | 'boolean' | 'string';
  title: string;
  description: string;
  default?: any;
  minimum?: number;
  maximum?: number;
}

export const CRAWLER_SETTINGS_SCHEMA: Record<string, CrawlerSettingSchema> = {
  crawl_interval_minutes: { 
    type: 'integer', 
    title: 'Crawl Interval (minutes)', 
    description: 'Interval in minutes between crawls',
    default: 60,
    minimum: 1
  },
  max_documents: { 
    type: 'integer', 
    title: 'Max Documents', 
    description: 'Maximum number of documents to crawl per run',
    default: 100,
    minimum: 1
  },
  processing_batch_size: { 
    type: 'integer', 
    title: 'Processing Batch Size', 
    description: 'Number of documents in a batch to submit for processing',
    default: 10,
    minimum: 1
  },
  file_filters: { 
    type: 'string', 
    title: 'File Filters', 
    description: 'List of file patterns to include when crawling (comma-separated)',
    default: ''
  },
  incremental: { 
    type: 'boolean', 
    title: 'Incremental Crawling', 
    description: 'Whether to perform incremental crawling',
    default: true
  },
  crawl_depth: { 
    type: 'integer', 
    title: 'Crawl Depth', 
    description: 'Depth of crawling (for web sources)',
    default: 3,
    minimum: 1,
    maximum: 10
  },
  check_for_updates: { 
    type: 'boolean', 
    title: 'Check for Updates', 
    description: 'Whether to check for updates in previously crawled documents',
    default: false
  },
  checkpoint_time: { 
    type: 'string', 
    title: 'Checkpoint Time', 
    description: 'Last checkpoint time for incremental crawling (in UTC tz ISO 8601 format)',
    default: ''
  },
  pause_on_error: { 
    type: 'boolean', 
    title: 'Pause on Error', 
    description: 'Whether to pause crawling on errors',
    default: false
  },
  skip_failed_documents: { 
    type: 'boolean', 
    title: 'Skip Failed Documents', 
    description: 'Whether to skip documents that fail retrieval',
    default: true
  }
};