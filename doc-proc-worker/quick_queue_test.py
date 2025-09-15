#!/usr/bin/env python3
"""
Quick test script to send a few sample messages to the Azure Storage Queue.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.dependencies import get_queue_service
from app.services.queue_service import AzureStorageQueueService
from app.models.queue_models import QueueBatchExecutionRequest
from app.logging import setup_logger


async def quick_test():
    """Send a few test messages quickly"""
    print("🚀 Quick Queue Test - Sending sample messages...\n")
    print("-" * 30)
    
    # Setup logging
    setup_logger()
    
    # Create queue service
    queue_service = get_queue_service()
    
    try:
        # Connect to queue
        print("📡 Connecting to Azure Storage Queue...")
        await queue_service.connect()
        print("✅ Connected successfully!\n")
        print("-" * 30)
        
        # Create sample documents
        documents = [
            {
                "id": "doc1",
                "file_path": "/Users/nadeemis/temp/Lorem Ipsum Sample Document.pdf"
            },
            {
                "id": "doc2",
                "file_path": "/Users/nadeemis/temp/Lorem Ipsum Presentation.pptx"
            },
            {
                "id": "doc3",
                "blob_details": {"container": "documents", "blob": "Lorem Ipsum Sample Document.docx"}
            },
            {
                "id": "doc4",
                "blob_details": {"container": "documents", "blob": "retail_store_data.xlsx"}
            }
        ]
        
        # Create and send test messages
        test_messages = [
            {
                "pipeline": "pipeline_1",
                "name": "Entity Extraction Test",
                "priority": 1
            },
            {
                "pipeline": "pipeline_1",
                "name": "Document Classification Test",
                "priority": 2
            },
            {
                "pipeline": "pipeline_1",
                "name": "Content Summarization Test", 
                "priority": 0
            },
            {
                "pipeline": "pipeline_1",
                "name": "Content Summarization Test 2", 
                "priority": 0
            }
        ]
        
        sent_messages = []
        
        for i, test_msg in enumerate(test_messages):
            print(f"📤 Sending message {i+1}/{len(test_messages)}: {test_msg['name']}")

            # Create batch execution request
            request = QueueBatchExecutionRequest(
                pipeline_name=test_msg["pipeline"],
                documents=documents,
                batch_name=test_msg["name"],
                priority=test_msg["priority"],
                metadata={
                    "test": True,
                    "sender": "quick_test_script",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                sent_at=datetime.now(timezone.utc).isoformat(),
                requested_by="test_user",
                correlation_id=f"quick_test_{i+1}_{datetime.now(timezone.utc).strftime('%H%M%S')}"
            )
            
            # Send message
            message_id = await queue_service.send_message(request.model_dump())
            sent_messages.append(message_id)
            print(f"   ✅ Message sent with ID: {message_id}")
            print("-" * 20)
        
        print(f"\n🎉 Successfully sent {len(sent_messages)} test messages!")
        print("📊 Queue status:")
        
        # Get queue stats
        try:
            props = await queue_service.get_queue_properties()
            print(f"   📈 Approximate message count: {props.get('approximate_message_count', 'unknown')}")
        except Exception as e:
            print(f"   ⚠️  Could not get queue stats: {e}")
        
        # Peek at messages
        print("\n👀 Peeking at queue messages:")
        try:
            messages = await queue_service.peek_messages(max_messages=5)
            if messages:
                for i, msg in enumerate(messages):
                    content = msg.content
                    msg_type = content.get("message_type", "unknown")
                    pipeline = content.get("pipeline_instance_id", "unknown")
                    print(f"   {i+1}. ID: {msg.id[:8]}... Type: {msg_type} Pipeline: {pipeline}")
            else:
                print("   📭 No messages visible in queue")
        except Exception as e:
            print(f"   ⚠️  Could not peek messages: {e}")
        
        print("\n✨ Test completed! The queue worker should now process these messages.")
        print("   💡 Run the queue worker with: python run_queue_worker.py")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return 1
    
    finally:
        # Disconnect
        await queue_service.disconnect()
        print("📡 Disconnected from queue")
    
    return 0


if __name__ == "__main__":
    print("Azure Storage Queue - Quick Test")
    print("=" * 40)
    exit_code = asyncio.run(quick_test())
    sys.exit(exit_code)
