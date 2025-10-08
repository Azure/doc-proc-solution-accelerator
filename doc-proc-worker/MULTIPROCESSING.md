# Multiprocessing Architecture for Document Processing Workers

This document provides a comprehensive guide to the multiprocessing worker pool architecture implemented in the doc-proc-worker service. The multiprocessing approach enables high-throughput document processing by distributing workload across multiple concurrent worker processes.

## Executive Summary

The multiprocessing worker pool transforms the doc-proc-worker from a single-threaded async service into a scalable, fault-tolerant system capable of processing thousands of documents concurrently. Each worker process operates independently with its own event loop, memory space, and queue connections, providing superior performance and reliability for production workloads.

### Key Benefits

- **Horizontal Scaling**: Utilize all available CPU cores effectively
- **Fault Isolation**: Process failures don't affect other workers
- **Memory Isolation**: Each worker has independent memory space, preventing memory leaks from cascading
- **Load Distribution**: Automatic workload balancing across worker processes
- **High Availability**: Automatic restart of failed workers maintains system uptime
- **Graceful Operations**: Coordinated startup, shutdown, and maintenance operations

## Architecture Deep Dive

### System Components

#### WorkerPoolManager
The central orchestrator that manages the lifecycle of all worker processes:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WorkerPoolManager                             │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  Signal Handler │  │ Health Monitor  │  │ Process Lifecycle   │  │
│  │  - SIGTERM      │  │ - Process Alive │  │ - Spawn Workers     │  │
│  │  - SIGINT       │  │ - Health Checks │  │ - Restart Failed    │  │
│  │  - Graceful     │  │ - Performance   │  │ - Coordinate Exit   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────────┐
        │             Multiprocessing.Event               │
        │           (Shutdown Coordination)               │
        └─────────────────────────────────────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ Worker Process 1│ │ Worker Process 2│ │ Worker Process N│
    │                 │ │                 │ │                 │
    │ ┌─────────────┐ │ │ ┌─────────────┐ │ │ ┌─────────────┐ │
    │ │QueueWorker  │ │ │ │QueueWorker  │ │ │ │QueueWorker  │ │
    │ │- Event Loop │ │ │ │- Event Loop │ │ │ │- Event Loop │ │
    │ │- Queue Conn │ │ │ │- Queue Conn │ │ │ │- Queue Conn │ │
    │ │- Cosmos DB  │ │ │ │- Cosmos DB  │ │ │ │- Cosmos DB  │ │
    │ └─────────────┘ │ │ └─────────────┘ │ │ └─────────────┘ │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

#### Individual Worker Processes
Each worker process operates as an independent service:

- **Async Event Loop**: Handles concurrent I/O operations within the process
- **QueueWorker Instance**: Core logic for message processing and pipeline execution  
- **Azure Service Connections**: Independent connections to Cosmos DB and Storage Queue
- **Signal Handling**: Responds to shutdown signals from the manager
- **Error Handling**: Local error recovery and reporting

### Inter-Process Communication

#### Multiprocessing Events
The system uses `multiprocessing.Event` objects for coordination:

```python
# Shutdown coordination
self.shutdown_event = mp.Event()

# Worker process monitors this event
while not self.shutdown_event.is_set():
    # Continue processing messages
    await self._process_messages()
```

#### Process Health Monitoring
The manager continuously monitors worker health:

```python
def _monitor_workers(self):
    """Continuous health monitoring loop"""
    while not self.shutdown_event.is_set():
        for worker_id, worker_info in self.workers.items():
            if not worker_info.process.is_alive():
                self.logger.warning(f"Worker {worker_id} died, restarting...")
                self._restart_worker(worker_id)
        
        time.sleep(self.health_check_interval)
```

## Process Lifecycle Management

### Worker Startup Sequence

1. **Manager Initialization**
   - Parse configuration parameters
   - Set up signal handlers for graceful shutdown
   - Initialize shared coordination primitives (Events, Queues)

2. **Worker Process Spawning**
   ```python
   def _spawn_worker(self, worker_id: str) -> WorkerInfo:
       """Spawn a new worker process"""
       process = Process(target=self._worker_main, args=(worker_id, self.shutdown_event))
       process.start()
       
       worker_info = WorkerInfo(
           process=process,
           worker_id=worker_id,
           started_at=datetime.now(timezone.utc),
           pid=process.pid
       )
       
       return worker_info
   ```

3. **Worker Process Initialization**
   - Set up independent logging context
   - Initialize Azure service connections
   - Start async event loop
   - Begin message processing loop

### Graceful Shutdown Protocol

The shutdown process ensures no data loss and proper resource cleanup:

```
Manager receives SIGTERM/SIGINT
           │
           ▼
Set shutdown_event (signals all workers)
           │
           ▼
Workers detect shutdown_event.is_set()
           │
           ▼
Workers complete current message processing
           │
           ▼  
Workers clean up resources (connections, files)
           │
           ▼
Workers exit gracefully
           │
           ▼
Manager waits for all processes (with timeout)
           │
           ▼
Force terminate if timeout exceeded
           │
           ▼
Manager cleanup and exit
```

### Failure Recovery Mechanisms

#### Worker Process Failure
When a worker process crashes or becomes unresponsive:

1. **Detection**: Health monitor detects process death via `process.is_alive()`
2. **Logging**: Record failure details including exit code and timestamp  
3. **Cleanup**: Clean up process resources and remove from active worker list
4. **Restart**: Spawn new worker process with same configuration (if auto-restart enabled)
5. **Notification**: Log restart event with worker identification

```python
def _restart_worker(self, worker_id: str):
    """Restart a failed worker process"""
    old_worker = self.workers.pop(worker_id, None)
    if old_worker:
        # Clean up old process
        old_worker.process.join(timeout=5)
        if old_worker.process.is_alive():
            old_worker.process.terminate()
    
    # Spawn new worker
    new_worker = self._spawn_worker(worker_id)
    self.workers[worker_id] = new_worker
    
    self.logger.info(f"Restarted worker {worker_id} (PID: {new_worker.pid})")
```


This comprehensive multiprocessing architecture enables the doc-proc-worker to achieve enterprise-grade scalability, reliability, and performance while maintaining operational simplicity and debugging capabilities.