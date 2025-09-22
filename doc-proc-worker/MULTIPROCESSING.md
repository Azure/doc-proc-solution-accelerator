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

## Configuration and Tuning

### Environment Variables

```bash
# Core multiprocessing settings
WORKER_POOL_SIZE=0                    # 0 = auto-detect CPU count, >0 = specific count
WORKER_AUTO_RESTART=true              # Automatically restart failed workers
WORKER_SHUTDOWN_TIMEOUT=30            # Seconds to wait for graceful shutdown
WORKER_HEALTH_CHECK_INTERVAL=10       # Health check frequency (seconds)

# Performance tuning
WORKER_STARTUP_DELAY=2                # Delay between worker startups (seconds)
WORKER_MAX_RESTART_ATTEMPTS=5         # Max restart attempts before giving up
WORKER_RESTART_BACKOFF=5              # Exponential backoff for restart attempts

# Resource management
WORKER_MEMORY_LIMIT=2048              # Memory limit per worker (MB)  
WORKER_CPU_AFFINITY=auto              # CPU affinity settings (auto/manual)
```

### Optimal Pool Sizing

#### CPU-Bound Workloads
For pipelines with intensive document processing:
```bash
# Start with CPU core count
WORKER_POOL_SIZE=0  # Auto-detect

# Or specify based on cores
WORKER_POOL_SIZE=8  # For 8-core system
```

#### I/O-Bound Workloads  
For pipelines with heavy Azure service calls:
```bash
# Use 2-3x CPU count for I/O wait
WORKER_POOL_SIZE=16  # For 8-core system with I/O waits
```

#### Memory-Constrained Environments
```bash
# Reduce workers to fit memory constraints
WORKER_POOL_SIZE=4   # Conservative approach
WORKER_MEMORY_LIMIT=1024  # 1GB per worker
```

#### Queue Throughput Matching
```bash
# Match processing capacity to message arrival rate
# If queue receives 100 msg/min, and each worker processes 2 msg/min:
WORKER_POOL_SIZE=50  # 100 ÷ 2 = 50 workers needed
```

## Advanced Usage Patterns

### Command Line Interface

#### Basic Operations
```bash
# Single worker (development/testing)
python run_queue_worker.py

# Multiprocessing pool with auto-detected workers
python run_queue_worker.py --pool

# Custom worker count
python run_queue_worker.py --pool --workers 6

# Disable auto-restart for debugging
python run_queue_worker.py --pool --no-restart --workers 2

# Alternative dedicated script
python run_worker_pool.py
```

#### Development and Debugging
```bash
# Debug mode with verbose logging
LOG_LEVEL=DEBUG python run_queue_worker.py --pool --workers 2

# Single worker for debugging specific issues
LOG_LEVEL=DEBUG python run_queue_worker.py

# Monitor mode (extensive logging)
WORKER_HEALTH_CHECK_INTERVAL=5 LOG_LEVEL=DEBUG python run_queue_worker.py --pool
```

### Container Deployment

#### Docker Compose Configuration
```yaml
version: '3.8'
services:
  doc-proc-worker-pool:
    build: .
    command: python run_queue_worker.py --pool
    environment:
      # Multiprocessing Configuration
      - WORKER_POOL_SIZE=4
      - WORKER_AUTO_RESTART=true
      - WORKER_SHUTDOWN_TIMEOUT=45
      - WORKER_HEALTH_CHECK_INTERVAL=15
      
      # Azure Service Configuration
      - COSMOS_DB_ENDPOINT=${COSMOS_DB_ENDPOINT}
      - STORAGE_ACCOUNT_WORKER_QUEUE_URL=${STORAGE_ACCOUNT_WORKER_QUEUE_URL}
      - STORAGE_WORKER_QUEUE_NAME=docproc-execution-requests
      
      # Performance Tuning
      - POLL_INTERVAL_SECONDS=3
      - MAX_MESSAGES_PER_POLL=8
      - MESSAGE_VISIBILITY_TIMEOUT=600
      
    # Resource constraints for container
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    
    # Health check configuration
    healthcheck:
      test: ["CMD", "python", "-c", "import os; exit(0 if os.path.exists('/tmp/workers-healthy') else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
      
    restart: unless-stopped
    
    volumes:
      # Optional: Mount logs directory
      - ./logs:/app/logs
      
    # Optional: Bind to specific CPU cores
    cpuset: "0-3"  # Use first 4 CPU cores
```

#### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: doc-proc-worker-pool
  labels:
    app: doc-proc-worker
    mode: multiprocessing
spec:
  replicas: 2  # Two pods, each running multiprocessing pool
  selector:
    matchLabels:
      app: doc-proc-worker
  template:
    metadata:
      labels:
        app: doc-proc-worker
        mode: multiprocessing
    spec:
      containers:
      - name: doc-proc-worker
        image: doc-proc-worker:latest
        command: ["python", "run_queue_worker.py", "--pool"]
        
        env:
        # Multiprocessing settings
        - name: WORKER_POOL_SIZE
          value: "3"  # 3 workers per pod
        - name: WORKER_AUTO_RESTART
          value: "true"
        - name: WORKER_SHUTDOWN_TIMEOUT
          value: "60"
          
        # Azure service configuration
        - name: COSMOS_DB_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: cosmos-endpoint
        - name: STORAGE_ACCOUNT_WORKER_QUEUE_URL
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: storage-queue-url
        
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
            
        # Probes for Kubernetes
        livenessProbe:
          exec:
            command: ["python", "-c", "from app.health_check import check_pool_health; exit(0 if check_pool_health() else 1)"]
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
          
        readinessProbe:
          exec:
            command: ["python", "-c", "from app.health_check import check_pool_ready; exit(0 if check_pool_ready() else 1)"]
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 2
      
      # Graceful shutdown configuration
      terminationGracePeriodSeconds: 90
```

## Performance Analysis and Optimization

### Monitoring Worker Pool Performance

#### Built-in Statistics Collection
```python
# Statistics tracking in WorkerPoolManager
@dataclass
class PoolStatistics:
    """Comprehensive pool performance statistics"""
    started_at: datetime
    total_workers: int
    active_workers: int
    failed_workers: int
    total_restarts: int
    
    # Performance metrics
    total_messages_processed: int = 0
    average_processing_time: float = 0.0
    messages_per_second: float = 0.0
    
    # Resource utilization
    memory_usage_mb: float = 0.0
    cpu_utilization: float = 0.0
    
    # Health indicators
    last_health_check: datetime = None
    unhealthy_workers: List[str] = field(default_factory=list)
```

#### Performance Monitoring Commands
```bash
# Real-time pool statistics
python -c "
from app.worker_pool import WorkerPoolManager
import time
manager = WorkerPoolManager(num_workers=4)
while True:
    stats = manager.get_pool_statistics()
    print(f'Workers: {stats.active_workers}/{stats.total_workers} | '
          f'Processed: {stats.total_messages_processed} | '
          f'Rate: {stats.messages_per_second:.1f} msg/s')
    time.sleep(5)
"

# Memory usage per worker process
python -c "
import psutil
import os
for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
    if 'python' in proc.info['name'] and 'run_queue_worker' in ' '.join(proc.cmdline()):
        print(f'Worker PID {proc.info[\"pid\"]}: '
              f'{proc.info[\"memory_info\"].rss / 1024 / 1024:.1f}MB, '
              f'CPU: {proc.info[\"cpu_percent\"]:.1f}%')
"
```

### Performance Optimization Strategies

#### Message Processing Optimization
```python
# Configure for high-throughput scenarios
OPTIMAL_HIGH_THROUGHPUT = {
    'WORKER_POOL_SIZE': 8,                    # Match or exceed CPU cores
    'MAX_MESSAGES_PER_POLL': 10,              # Higher batch sizes
    'POLL_INTERVAL_SECONDS': 1,               # Aggressive polling
    'MESSAGE_VISIBILITY_TIMEOUT': 300,        # 5 minute processing window
    'WORKER_HEALTH_CHECK_INTERVAL': 30,       # Less frequent health checks
}

# Configure for memory-constrained environments  
OPTIMAL_LOW_MEMORY = {
    'WORKER_POOL_SIZE': 2,                    # Fewer concurrent workers
    'MAX_MESSAGES_PER_POLL': 3,               # Smaller batches
    'POLL_INTERVAL_SECONDS': 5,               # Less aggressive polling
    'WORKER_RESTART_BACKOFF': 10,             # Slower restart cycle
}

# Configure for I/O intensive workloads
OPTIMAL_IO_INTENSIVE = {
    'WORKER_POOL_SIZE': 12,                   # More workers for I/O wait
    'MAX_MESSAGES_PER_POLL': 5,               # Moderate batch sizes
    'POLL_INTERVAL_SECONDS': 2,               # Balanced polling
    'MESSAGE_VISIBILITY_TIMEOUT': 600,        # Longer timeout for I/O
}
```

#### Resource Management Patterns
```python
# CPU affinity for worker processes
import os
import psutil

def set_worker_cpu_affinity(worker_id: str, cpu_cores: List[int]):
    """Bind worker process to specific CPU cores"""
    try:
        process = psutil.Process(os.getpid())
        process.cpu_affinity(cpu_cores)
        logger.info(f"Worker {worker_id} bound to CPU cores: {cpu_cores}")
    except Exception as e:
        logger.warning(f"Failed to set CPU affinity for worker {worker_id}: {e}")

# Memory management
def configure_worker_memory_limits(worker_id: str, memory_limit_mb: int):
    """Configure memory limits for worker process"""
    import resource
    
    # Set memory limit (in bytes)
    memory_limit_bytes = memory_limit_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
    logger.info(f"Worker {worker_id} memory limit set to {memory_limit_mb}MB")
```

## Advanced Error Handling and Resilience

### Error Classification and Response

#### Transient Errors (Recoverable)
- Network timeouts to Azure services
- Temporary service unavailability  
- Queue message visibility timeout

**Response Strategy**: Retry with exponential backoff
```python
async def handle_transient_error(self, error: Exception, retry_count: int):
    """Handle recoverable errors with backoff"""
    backoff_seconds = min(300, (2 ** retry_count) + random.uniform(0, 1))
    self.logger.warning(f"Transient error (attempt {retry_count}): {error}")
    await asyncio.sleep(backoff_seconds)
```

#### Fatal Errors (Non-recoverable)
- Invalid message format
- Missing pipeline configuration
- Authentication failures

**Response Strategy**: Log error and move message to poison queue
```python
async def handle_fatal_error(self, message: QueueMessage, error: Exception):
    """Handle non-recoverable errors"""
    self.logger.error(f"Fatal error processing message {message.id}: {error}")
    await self._move_to_poison_queue(message, str(error))
    await self.queue_proxy.delete_message(message)
```

#### Process-Level Errors
- Out of memory conditions
- Segmentation faults
- Unhandled exceptions

**Response Strategy**: Process restart with failure tracking
```python
def handle_worker_crash(self, worker_id: str, exit_code: int):
    """Handle unexpected worker process termination"""
    self.failure_counts[worker_id] = self.failure_counts.get(worker_id, 0) + 1
    
    if self.failure_counts[worker_id] > MAX_FAILURE_THRESHOLD:
        self.logger.error(f"Worker {worker_id} exceeded failure threshold, not restarting")
        return False
        
    self.logger.warning(f"Worker {worker_id} crashed (exit code: {exit_code}), restarting...")
    return self._restart_worker(worker_id)
```

### Circuit Breaker Pattern Implementation

```python
class WorkerCircuitBreaker:
    """Circuit breaker pattern for worker reliability"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call_with_circuit_breaker(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerException("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                
            raise e
```

## Troubleshooting and Diagnostics

### Common Issues and Solutions

#### Worker Startup Failures
**Symptoms**: Workers fail to start, immediate process exits
```bash
# Diagnosis commands
LOG_LEVEL=DEBUG python run_queue_worker.py --pool --workers 1

# Check environment configuration
python -c "from app.settings import app_settings; print(vars(app_settings))"

# Verify Azure service connectivity
python -c "
import asyncio
from app.dependencies import get_queue_proxy, get_cosmos_db
async def test_connections():
    queue = get_queue_proxy()
    await queue.connect()
    print('Queue connection: OK')
    
    db = get_cosmos_db()
    print('Cosmos DB connection: OK')

asyncio.run(test_connections())
"
```

**Solutions**:
- Verify environment variables are set correctly
- Check Azure service authentication (credentials, network access)
- Ensure required Python dependencies are installed
- Validate container resource limits

#### Worker Process Deaths
**Symptoms**: Workers unexpectedly terminate during operation
```bash
# Monitor worker processes in real-time
watch -n 2 'ps aux | grep run_queue_worker | grep -v grep'

# Check system resources
top -p $(pgrep -f run_queue_worker | tr '\n' ',')

# Monitor memory usage
python -c "
import psutil
import time
while True:
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        if 'run_queue_worker' in proc.info.get('name', ''):
            memory_mb = proc.info['memory_info'].rss / 1024 / 1024
            print(f'PID {proc.info[\"pid\"]}: {memory_mb:.1f}MB')
    time.sleep(5)
"
```

**Solutions**:
- Increase container memory limits
- Implement memory monitoring and cleanup in workers
- Check for memory leaks in pipeline processing
- Reduce worker pool size to lower memory pressure

#### High CPU Usage
**Symptoms**: System CPU usage consistently above 80%
```bash
# CPU usage per worker
python -c "
import psutil
for proc in psutil.process_iter(['pid', 'cpu_percent', 'name']):
    if 'run_queue_worker' in proc.info.get('name', ''):
        print(f'Worker PID {proc.info[\"pid\"]}: {proc.info[\"cpu_percent\"]:.1f}%')
"

# Profile CPU usage
python -m cProfile -o profile_output.prof run_queue_worker.py --pool
python -c "import pstats; pstats.Stats('profile_output.prof').sort_stats('cumulative').print_stats(20)"
```

**Solutions**:
- Reduce worker pool size to match available CPU cores
- Optimize pipeline processing algorithms
- Implement CPU affinity to prevent context switching
- Add processing delays in tight loops

#### Queue Message Backlog
**Symptoms**: Messages accumulating in queue faster than processing
```bash
# Check queue depth
python -c "
import asyncio
from app.proxy.queue import StorageQueue
from app.settings import app_settings

async def check_queue():
    queue = StorageQueue(
        app_settings.STORAGE_ACCOUNT_WORKER_QUEUE_URL,
        app_settings.STORAGE_WORKER_QUEUE_NAME
    )
    await queue.connect()
    
    # Get approximate message count (if supported by Azure Storage Queue)
    print('Queue depth check - implement based on Azure Storage Queue API')

asyncio.run(check_queue())
"

# Monitor processing rate
python -c "
from app.worker_pool import WorkerPoolManager
import time

manager = WorkerPoolManager(num_workers=4)
start_time = time.time()
start_count = manager.get_total_processed()

time.sleep(60)  # Monitor for 1 minute

end_count = manager.get_total_processed()
end_time = time.time()

rate = (end_count - start_count) / (end_time - start_time)
print(f'Processing rate: {rate:.1f} messages/second')
"
```

**Solutions**:
- Increase worker pool size
- Scale horizontally (more container instances)
- Optimize pipeline processing performance
- Implement message prioritization

### Debug Mode Operations

#### Verbose Logging Configuration
```python
# app/debug_logging.py
import logging
import sys

def setup_debug_logging():
    """Configure comprehensive debug logging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(processName)s:%(process)d] - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug_multiprocessing.log'),
        ]
    )
    
    # Enable debug logging for specific modules
    logging.getLogger('app.worker_pool').setLevel(logging.DEBUG)
    logging.getLogger('app.queue_worker').setLevel(logging.DEBUG)
    logging.getLogger('app.execution_manager').setLevel(logging.DEBUG)
    
    # Azure SDK debug logging
    logging.getLogger('azure.core').setLevel(logging.DEBUG)
    logging.getLogger('azure.storage').setLevel(logging.DEBUG)
```

#### Interactive Debugging
```bash
# Debug single worker process
python -c "
import pdb
pdb.set_trace()
from run_queue_worker import run_single_worker
import asyncio
asyncio.run(run_single_worker())
"

# Remote debugging setup (for container environments)
pip install debugpy

# Add to worker code:
# import debugpy
# debugpy.listen(('0.0.0.0', 5678))
# debugpy.wait_for_client()  # Blocks until debugger attaches
```

## Security and Production Considerations

### Resource Limits and Isolation

#### Container Security
```dockerfile
# Dockerfile security enhancements
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r worker && useradd -r -g worker worker

# Set resource limits
RUN echo "worker soft memlock 2097152" >> /etc/security/limits.conf
RUN echo "worker hard memlock 2097152" >> /etc/security/limits.conf

# Switch to non-root user
USER worker

# Set working directory with proper permissions
WORKDIR /app
COPY --chown=worker:worker . /app

# Set secure environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
```

#### Process Isolation
```bash
# Run with additional security constraints
docker run --security-opt=no-new-privileges \
           --cap-drop=ALL \
           --read-only \
           --tmpfs /tmp:rw,noexec,nosuid,size=100m \
           -e WORKER_POOL_SIZE=4 \
           doc-proc-worker:latest python run_queue_worker.py --pool
```

### Monitoring and Alerting

#### Health Check Endpoints
```python
# app/health_monitor.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

@dataclass
class HealthStatus:
    """Comprehensive health status"""
    healthy: bool
    checks: Dict[str, bool]
    details: Dict[str, any]
    timestamp: datetime

class HealthMonitor:
    """Health monitoring for multiprocessing worker pool"""
    
    def __init__(self, pool_manager):
        self.pool_manager = pool_manager
    
    def get_health_status(self) -> HealthStatus:
        """Get comprehensive health status"""
        checks = {
            'workers_alive': self._check_workers_alive(),
            'azure_connectivity': self._check_azure_services(),
            'memory_usage': self._check_memory_usage(),
            'processing_rate': self._check_processing_rate()
        }
        
        return HealthStatus(
            healthy=all(checks.values()),
            checks=checks,
            details=self._get_detailed_metrics(),
            timestamp=datetime.utcnow()
        )
    
    def _check_workers_alive(self) -> bool:
        """Check if all workers are alive and responsive"""
        alive_count = sum(1 for w in self.pool_manager.workers.values() 
                         if w.process.is_alive())
        return alive_count >= self.pool_manager.num_workers * 0.8  # 80% threshold
```

#### Prometheus Metrics Integration
```python
# app/prometheus_metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
MESSAGES_PROCESSED = Counter('worker_messages_processed_total', 
                           'Total processed messages', 
                           ['worker_id', 'status'])

PROCESSING_TIME = Histogram('worker_message_processing_seconds',
                          'Message processing time',
                          ['worker_id', 'pipeline'])

ACTIVE_WORKERS = Gauge('worker_pool_active_workers',
                      'Number of active worker processes')

QUEUE_DEPTH = Gauge('worker_queue_depth_messages',
                   'Number of messages in queue')

def start_metrics_server(port: int = 8000):
    """Start Prometheus metrics server"""
    start_http_server(port)
```

## Best Practices and Patterns

### Development Workflow

#### Testing Multiprocessing Code
```python
# tests/test_multiprocessing.py
import asyncio
import time
from unittest.mock import patch, MagicMock
from app.worker_pool import WorkerPoolManager

class TestWorkerPool:
    """Comprehensive multiprocessing tests"""
    
    def test_worker_startup_sequence(self):
        """Test worker pool startup process"""
        manager = WorkerPoolManager(num_workers=2, worker_restart=False)
        
        # Mock external dependencies
        with patch('app.dependencies.get_queue_proxy'), \
             patch('app.dependencies.get_cosmos_db'):
            
            # Test startup
            manager._spawn_all_workers()
            assert len(manager.workers) == 2
            
            # Verify all workers are alive
            time.sleep(2)  # Allow startup time
            for worker in manager.workers.values():
                assert worker.process.is_alive()
    
    def test_graceful_shutdown(self):
        """Test coordinated shutdown process"""
        manager = WorkerPoolManager(num_workers=2, shutdown_timeout=10)
        
        with patch('app.dependencies.get_queue_proxy'), \
             patch('app.dependencies.get_cosmos_db'):
            
            manager._spawn_all_workers()
            time.sleep(1)
            
            # Trigger shutdown
            manager.shutdown_event.set()
            
            # Verify graceful shutdown
            start_time = time.time()
            manager._wait_for_workers()
            shutdown_time = time.time() - start_time
            
            assert shutdown_time < manager.shutdown_timeout
            assert all(not w.process.is_alive() for w in manager.workers.values())
```

#### Load Testing Framework
```python
# tests/load_test.py
import asyncio
import concurrent.futures
from typing import List
from dataclasses import dataclass

@dataclass
class LoadTestResult:
    total_messages: int
    processing_time: float
    messages_per_second: float
    success_rate: float
    error_count: int

async def run_load_test(
    num_messages: int,
    concurrent_workers: int,
    message_generator: callable
) -> LoadTestResult:
    """Execute load test against worker pool"""
    
    start_time = time.time()
    errors = 0
    
    # Generate test messages
    messages = [message_generator() for _ in range(num_messages)]
    
    # Submit messages to queue
    queue_proxy = get_queue_proxy()
    await queue_proxy.connect()
    
    for message in messages:
        try:
            await queue_proxy.send_message(message)
        except Exception as e:
            errors += 1
            logger.error(f"Failed to send message: {e}")
    
    # Wait for processing completion (implement monitoring logic)
    await wait_for_queue_empty(timeout=300)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    return LoadTestResult(
        total_messages=num_messages,
        processing_time=processing_time,
        messages_per_second=num_messages / processing_time,
        success_rate=(num_messages - errors) / num_messages,
        error_count=errors
    )
```

### Production Deployment Patterns

#### Blue-Green Deployment
```bash
#!/bin/bash
# deploy_worker_pool.sh - Blue-green deployment script

BLUE_SERVICE="doc-proc-worker-blue"
GREEN_SERVICE="doc-proc-worker-green"
CURRENT_SERVICE=$(kubectl get service doc-proc-worker -o jsonpath='{.spec.selector.version}')

if [ "$CURRENT_SERVICE" == "blue" ]; then
    TARGET_SERVICE="green"
    STANDBY_SERVICE="blue"
else
    TARGET_SERVICE="blue"
    STANDBY_SERVICE="green"
fi

echo "Deploying to $TARGET_SERVICE environment..."

# Deploy new version to standby environment
kubectl set image deployment/doc-proc-worker-$TARGET_SERVICE \
    worker=doc-proc-worker:$NEW_VERSION

# Wait for rollout completion
kubectl rollout status deployment/doc-proc-worker-$TARGET_SERVICE --timeout=300s

# Run health checks
kubectl exec deployment/doc-proc-worker-$TARGET_SERVICE -- \
    python -c "from app.health_check import comprehensive_health_check; exit(0 if comprehensive_health_check() else 1)"

# Switch traffic to new version
kubectl patch service doc-proc-worker \
    -p '{"spec":{"selector":{"version":"'$TARGET_SERVICE'"}}}'

echo "Traffic switched to $TARGET_SERVICE"
echo "Monitor the new deployment, then scale down $STANDBY_SERVICE when stable"
```

#### Canary Deployment  
```yaml
# canary-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: doc-proc-worker-canary
spec:
  replicas: 10
  strategy:
    canary:
      steps:
      - setWeight: 10    # 10% traffic to new version
      - pause: {duration: 300s}  # Wait 5 minutes
      - setWeight: 30    # 30% traffic
      - pause: {duration: 600s}  # Wait 10 minutes  
      - setWeight: 50    # 50% traffic
      - pause: {duration: 300s}
      - setWeight: 100   # Full deployment
      
      analysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: doc-proc-worker
      
      trafficRouting:
        nginx:
          stableService: doc-proc-worker-stable
          canaryService: doc-proc-worker-canary
          
  selector:
    matchLabels:
      app: doc-proc-worker
  template:
    metadata:
      labels:
        app: doc-proc-worker
    spec:
      containers:
      - name: worker
        image: doc-proc-worker:latest
        command: ["python", "run_queue_worker.py", "--pool"]
```

This comprehensive multiprocessing architecture enables the doc-proc-worker to achieve enterprise-grade scalability, reliability, and performance while maintaining operational simplicity and debugging capabilities.