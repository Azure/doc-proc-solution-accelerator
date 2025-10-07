# Doc-Proc-Crawler - Distributed Architecture Overview

## Overview

The doc-proc-crawler now features a **distributed coordination system** that automatically manages crawler workers across multiple machines with intelligent load balancing and conflict prevention.

## Key Features

### 🔄 Automatic Source Discovery
- Periodically queries Cosmos DB for active source instances
- Detects additions, removals, and updates automatically  
- No manual configuration of source instance IDs required

### 🔒 Lease-Based Coordination
- Ensures only one worker per source instance across all machines
- Automatic lease renewal and cleanup
- Prevents duplicate crawling operations

### ⚖️ Intelligent Load Distribution  
- Configurable maximum workers per machine
- Automatic scaling based on available source instances
- Fair distribution across multiple deployment instances

### 🛠️ Self-Healing Operations
- Automatic restart of failed workers
- Lease expiration handling for crashed processes
- Graceful shutdown and error recovery

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Distributed Crawler System                       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ Source Discovery│  │  Lease Manager  │  │  Worker Manager     │  │
│  │ - Query Cosmos  │  │ - Acquire Lease │  │ - Start/Stop        │  │
│  │ - Detect Changes│  │ - Renew Lease   │  │ - Monitor Health    │  │
│  │ - Monitor Loop  │  │ - Release Lease │  │ - Handle Changes    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │        Cosmos DB            │
                    │  ┌─────────────────────┐    │
                    │  │ source_instances    │    │
                    │  │ worker_leases       │    │
                    │  │ crawl_executions    │    │
                    │  └─────────────────────┘    │
                    └─────────────────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  Machine A      │ │  Machine B      │ │  Machine N      │
    │                 │ │                 │ │                 │
    │ Crawler Worker 1│ │ Crawler Worker 3│ │ Crawler Worker X│
    │ Crawler Worker 2│ │ Crawler Worker 4│ │ Crawler Worker Y│
    │       ...       │ │       ...       │ │       ...       │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Usage

### Default Distributed Mode (Recommended)

```bash
# Start distributed crawler (discovers sources automatically)
python run_crawler.py

# With custom worker limit
python run_crawler.py --max-workers=5
```

The distributed mode:
- Automatically discovers source instances from Cosmos DB
- Acquires leases for available source instances
- Starts one worker per acquired source instance
- Monitors for source instance changes
- Coordinates with other machines to prevent conflicts

### Legacy Modes (Backward Compatibility)

```bash  
# Single worker for specific source (legacy)
python run_crawler.py --source-id=source-001

# Multiple workers for specific sources (legacy) 
python run_crawler.py --pool --source-ids source-001 source-002
```

## Configuration

Key settings in `app/settings.py`:

```python
# Maximum workers per machine
CRAWLER_MAX_WORKERS = 10

# How often to discover source instances (seconds)  
CRAWLER_DISCOVERY_POLL_INTERVAL = 30

# Worker lease duration (minutes)
CRAWLER_LEASE_DURATION_MINUTES = 5

# Lease renewal interval (minutes)
CRAWLER_LEASE_RENEWAL_INTERVAL_MINUTES = 2
```

## Cosmos DB Schema

### Worker Leases Container
```json
{
  "id": "source-123_worker-abc",
  "partition_key": "source-123", 
  "source_instance_id": "source-123",
  "worker_id": "machine-A_12345_abc123",
  "machine_id": "machine-A",
  "process_id": "12345",
  "acquired_at": "2024-01-01T10:00:00Z",
  "expires_at": "2024-01-01T10:05:00Z", 
  "renewed_at": "2024-01-01T10:02:00Z",
  "status": "active",
  "type": "worker_lease"
}
```

## Operational Benefits

### Multi-Machine Deployment
- Deploy multiple crawler instances across different machines
- Each instance automatically coordinates to prevent conflicts
- Load naturally distributes across available machines
- No manual partition management required

### Fault Tolerance
- If a machine fails, its leases expire automatically
- Other machines can acquire expired leases and take over
- Self-healing system with no manual intervention

### Elastic Scaling
- Add new crawler machines anytime
- They automatically participate in work distribution
- Remove machines gracefully with automatic lease cleanup

### Source Instance Lifecycle
- Add new source instances to Cosmos DB
- Crawlers automatically detect and start processing
- Disable/delete source instances to stop crawling
- Changes propagate to all machines automatically

## Monitoring

The distributed manager provides status information:

```python
# Get worker status across all machines
manager.get_worker_status()

# Get manager statistics  
manager.get_manager_stats()
```

Logs include:
- Source instance discovery events
- Lease acquisition/renewal/release
- Worker start/stop operations  
- Coordination conflicts and resolutions

## Migration from Legacy

Existing deployments can migrate seamlessly:

1. **Phase 1**: Deploy new distributed crawler alongside existing
2. **Phase 2**: Monitor both systems running in parallel  
3. **Phase 3**: Gradually redirect source instances to new system
4. **Phase 4**: Decommission legacy crawler workers

The distributed system is backward compatible and can run in legacy modes if needed.