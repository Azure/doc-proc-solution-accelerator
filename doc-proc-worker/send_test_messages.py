#!/usr/bin/env python3
"""
Simple script to send test messages to the Azure Storage Queue for testing the queue worker.

This script demonstrates how to send different types of messages to the queue:
- Batch execution requests
- Batch retry requests
- Batch cancel requests
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import List

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.queue_service import AzureQueueService
from app.models.queue_models import (
    QueueBatchExecutionRequest, QueueBatchRetryRequest, QueueBatchCancelRequest,
    QueueMessageType
)
from app.models.execution import DocumentReference
from app.logging import setup_logger


class QueueTestSender:
    """Test client for sending messages to the Azure Storage Queue"""
    
    def __init__(self):
        self.queue_service = AzureQueueService()
        self.logger = logging.getLogger("doc-proc-worker.queue_test_sender")
    
    async def connect(self):
        """Connect to the queue service"""
        await self.queue_service.connect()
        self.logger.info("Connected to Azure Storage Queue")
    
    async def disconnect(self):
        """Disconnect from the queue service"""
        await self.queue_service.disconnect()
        self.logger.info("Disconnected from Azure Storage Queue")
    
    async def send_batch_execution_request(self, pipeline_id: str, documents: List[DocumentReference], 
                                         batch_name: str = None, priority: int = 0) -> str:
        """Send a batch execution request to the queue"""
        request = QueueBatchExecutionRequest(
            pipeline_instance_id=pipeline_id,
            documents=documents,
            batch_name=batch_name or f"Test batch {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            priority=priority,
            metadata={
                "test_run": True,
                "sent_by": "queue_test_sender",
                "sent_at": datetime.utcnow().isoformat()
            },
            submitted_at=datetime.utcnow(),
            requested_by="test_user",
            correlation_id=f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        )
        
        message_id = await self.queue_service.send_message(request.model_dump())
        self.logger.info(f"Sent batch execution request with message ID: {message_id}")
        return message_id
    
    async def send_batch_retry_request(self, batch_id: str, retry_attempt: int = 1) -> str:
        """Send a batch retry request to the queue"""
        request = QueueBatchRetryRequest(
            batch_id=batch_id,
            retry_attempt=retry_attempt,
            original_error="Test retry scenario",
            submitted_at=datetime.utcnow(),
            requested_by="test_user",
            correlation_id=f"retry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        )
        
        message_id = await self.queue_service.send_message(request.model_dump())
        self.logger.info(f"Sent batch retry request with message ID: {message_id}")
        return message_id
    
    async def send_batch_cancel_request(self, batch_id: str, reason: str = "Test cancellation") -> str:
        """Send a batch cancel request to the queue"""
        request = QueueBatchCancelRequest(
            batch_id=batch_id,
            reason=reason,
            submitted_at=datetime.utcnow(),
            requested_by="test_user",
            correlation_id=f"cancel_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        )
        
        message_id = await self.queue_service.send_message(request.model_dump())
        self.logger.info(f"Sent batch cancel request with message ID: {message_id}")
        return message_id
    
    async def peek_queue_messages(self, max_messages: int = 10):
        """Peek at messages in the queue without removing them"""
        messages = await self.queue_service.peek_messages(max_messages=max_messages)
        
        if not messages:
            self.logger.info("No messages in the queue")
            return
        
        self.logger.info(f"Found {len(messages)} messages in the queue:")
        for i, msg in enumerate(messages):
            try:
                content = msg.content
                msg_type = content.get("message_type", "unknown")
                self.logger.info(f"  Message {i+1}: ID={msg.id}, Type={msg_type}")
                if msg_type == QueueMessageType.BATCH_EXECUTION_REQUEST:
                    pipeline_id = content.get("pipeline_instance_id", "unknown")
                    doc_count = len(content.get("documents", []))
                    self.logger.info(f"    Pipeline: {pipeline_id}, Documents: {doc_count}")
                elif msg_type in [QueueMessageType.BATCH_RETRY_REQUEST, QueueMessageType.BATCH_CANCEL_REQUEST]:
                    batch_id = content.get("batch_id", "unknown")
                    self.logger.info(f"    Batch ID: {batch_id}")
            except Exception as e:
                self.logger.error(f"  Message {i+1}: Failed to parse - {e}")
    
    async def get_queue_stats(self):
        """Get queue statistics"""
        try:
            props = await self.queue_service.get_queue_properties()
            self.logger.info(f"Queue statistics:")
            self.logger.info(f"  Approximate message count: {props.get('approximate_message_count', 'unknown')}")
            self.logger.info(f"  Metadata: {props.get('metadata', {})}")
        except Exception as e:
            self.logger.error(f"Failed to get queue stats: {e}")


def create_sample_documents(count: int = 3) -> List[DocumentReference]:
    """Create sample document references for testing"""
    documents = []
    for i in range(count):
        doc = DocumentReference(
            container_name="test-documents",
            blob_name=f"test_document_{i+1}.pdf",
            url=f"https://teststorage.blob.core.windows.net/test-documents/test_document_{i+1}.pdf",
            content_type="application/pdf",
            size_bytes=1024 * (i + 1)  # Varying sizes
        )
        documents.append(doc)
    
    return documents


async def run_interactive_mode():
    """Run in interactive mode allowing user to choose actions"""
    sender = QueueTestSender()
    
    try:
        await sender.connect()
        
        while True:
            print("\n" + "="*50)
            print("Azure Storage Queue Test Sender")
            print("="*50)
            print("1. Send batch execution request")
            print("2. Send batch retry request")
            print("3. Send batch cancel request")
            print("4. Peek queue messages")
            print("5. Get queue statistics")
            print("6. Send multiple test requests")
            print("0. Exit")
            print("="*50)
            
            choice = input("Enter your choice: ").strip()
            
            try:
                if choice == "1":
                    pipeline_id = input("Enter pipeline instance ID (or press Enter for default): ").strip()
                    if not pipeline_id:
                        pipeline_id = "test_pipeline_001"
                    
                    doc_count = input("Enter number of documents (default: 3): ").strip()
                    try:
                        doc_count = int(doc_count) if doc_count else 3
                    except ValueError:
                        doc_count = 3
                    
                    documents = create_sample_documents(doc_count)
                    batch_name = f"Test batch {datetime.now().strftime('%H:%M:%S')}"
                    
                    message_id = await sender.send_batch_execution_request(
                        pipeline_id=pipeline_id,
                        documents=documents,
                        batch_name=batch_name
                    )
                    print(f"✅ Sent batch execution request: {message_id}")
                
                elif choice == "2":
                    batch_id = input("Enter batch ID to retry: ").strip()
                    if not batch_id:
                        print("❌ Batch ID is required")
                        continue
                    
                    message_id = await sender.send_batch_retry_request(batch_id)
                    print(f"✅ Sent batch retry request: {message_id}")
                
                elif choice == "3":
                    batch_id = input("Enter batch ID to cancel: ").strip()
                    if not batch_id:
                        print("❌ Batch ID is required")
                        continue
                    
                    reason = input("Enter cancellation reason (optional): ").strip()
                    if not reason:
                        reason = "Manual cancellation via test script"
                    
                    message_id = await sender.send_batch_cancel_request(batch_id, reason)
                    print(f"✅ Sent batch cancel request: {message_id}")
                
                elif choice == "4":
                    max_msgs = input("Enter max messages to peek (default: 10): ").strip()
                    try:
                        max_msgs = int(max_msgs) if max_msgs else 10
                    except ValueError:
                        max_msgs = 10
                    
                    await sender.peek_queue_messages(max_msgs)
                
                elif choice == "5":
                    await sender.get_queue_stats()
                
                elif choice == "6":
                    count = input("Enter number of test requests to send (default: 5): ").strip()
                    try:
                        count = int(count) if count else 5
                    except ValueError:
                        count = 5
                    
                    print(f"Sending {count} test batch execution requests...")
                    for i in range(count):
                        documents = create_sample_documents(3)
                        message_id = await sender.send_batch_execution_request(
                            pipeline_id=f"test_pipeline_{i+1:03d}",
                            documents=documents,
                            batch_name=f"Bulk test batch {i+1}",
                            priority=i % 3  # Varying priorities
                        )
                        print(f"  ✅ Sent request {i+1}: {message_id}")
                    
                    print(f"✅ Successfully sent {count} test requests")
                
                elif choice == "0":
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    finally:
        await sender.disconnect()


async def run_batch_mode(args):
    """Run in batch mode with command line arguments"""
    sender = QueueTestSender()
    
    try:
        await sender.connect()
        
        if args[0] == "send":
            count = int(args[1]) if len(args) > 1 else 1
            print(f"Sending {count} test batch execution requests...")
            
            for i in range(count):
                documents = create_sample_documents(3)
                message_id = await sender.send_batch_execution_request(
                    pipeline_id=f"test_pipeline_{i+1:03d}",
                    documents=documents,
                    batch_name=f"Batch test {i+1}"
                )
                print(f"Sent request {i+1}: {message_id}")
        
        elif args[0] == "peek":
            max_msgs = int(args[1]) if len(args) > 1 else 10
            await sender.peek_queue_messages(max_msgs)
        
        elif args[0] == "stats":
            await sender.get_queue_stats()
        
        else:
            print("Unknown command. Use: send [count], peek [max], or stats")
    
    finally:
        await sender.disconnect()


async def main():
    """Main entry point"""
    setup_logger()
    logger = logging.getLogger("doc-proc-worker.queue_test_sender")
    
    logger.info("Starting Azure Storage Queue Test Sender...")
    
    try:
        if len(sys.argv) > 1:
            # Batch mode
            await run_batch_mode(sys.argv[1:])
        else:
            # Interactive mode
            await run_interactive_mode()
    
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        logger.error(f"Test sender failed: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
