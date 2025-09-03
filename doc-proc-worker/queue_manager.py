#!/usr/bin/env python3
"""
Queue management utility script for Azure Storage Queue operations.
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.queue_service import AzureQueueService
from app.logging import setup_logger


class QueueManager:
    """Utility class for managing the Azure Storage Queue"""
    
    def __init__(self):
        self.queue_service = AzureQueueService()
    
    async def connect(self):
        """Connect to the queue service"""
        await self.queue_service.connect()
        print("✅ Connected to Azure Storage Queue")
    
    async def disconnect(self):
        """Disconnect from the queue service"""
        await self.queue_service.disconnect()
        print("📡 Disconnected from queue")
    
    async def peek_messages(self, count: int = 10):
        """Peek at messages in the queue"""
        print(f"👀 Peeking at up to {count} messages...")
        
        try:
            messages = await self.queue_service.peek_messages(max_messages=count)
            
            if not messages:
                print("📭 No messages in the queue")
                return
            
            print(f"📨 Found {len(messages)} messages:")
            print("-" * 80)
            
            for i, msg in enumerate(messages):
                try:
                    content = msg.content
                    msg_type = content.get("message_type", "unknown")
                    inserted = msg.inserted_on.strftime("%Y-%m-%d %H:%M:%S") if hasattr(msg, 'inserted_on') else "unknown"
                    
                    print(f"Message {i+1}:")
                    print(f"  ID: {msg.id}")
                    print(f"  Type: {msg_type}")
                    print(f"  Inserted: {inserted}")
                    
                    if msg_type == "batch_execution_request":
                        pipeline = content.get("pipeline_instance_id", "unknown")
                        doc_count = len(content.get("documents", []))
                        batch_name = content.get("batch_name", "unknown")
                        priority = content.get("priority", 0)
                        
                        print(f"  Pipeline: {pipeline}")
                        print(f"  Batch Name: {batch_name}")
                        print(f"  Documents: {doc_count}")
                        print(f"  Priority: {priority}")
                    
                    elif msg_type in ["batch_retry_request", "batch_cancel_request"]:
                        batch_id = content.get("batch_id", "unknown")
                        print(f"  Batch ID: {batch_id}")
                    
                    print("-" * 40)
                
                except Exception as e:
                    print(f"  ❌ Failed to parse message {i+1}: {e}")
                    print("-" * 40)
        
        except Exception as e:
            print(f"❌ Error peeking messages: {e}")
    
    async def get_stats(self):
        """Get queue statistics"""
        print("📊 Getting queue statistics...")
        
        try:
            props = await self.queue_service.get_queue_properties()
            count = props.get('approximate_message_count', 'unknown')
            metadata = props.get('metadata', {})
            
            print(f"📈 Queue Statistics:")
            print(f"  Queue Name: {self.queue_service.queue_name}")
            print(f"  Approximate Message Count: {count}")
            
            if metadata:
                print(f"  Metadata:")
                for key, value in metadata.items():
                    print(f"    {key}: {value}")
            else:
                print(f"  Metadata: None")
        
        except Exception as e:
            print(f"❌ Error getting queue stats: {e}")
    
    async def clear_queue(self):
        """Clear all messages from the queue"""
        print("🧹 Clearing all messages from the queue...")
        
        # Get confirmation
        response = input("⚠️  This will delete ALL messages in the queue. Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return
        
        try:
            await self.queue_service.clear_queue()
            print("✅ Queue cleared successfully")
        except Exception as e:
            print(f"❌ Error clearing queue: {e}")
    
    async def receive_and_delete(self, count: int = 1):
        """Receive and delete messages (for testing)"""
        print(f"🗑️  Receiving and deleting up to {count} messages...")
        
        try:
            deleted_count = 0
            
            while deleted_count < count:
                messages = await self.queue_service.receive_messages(
                    max_messages=min(count - deleted_count, 32),
                    visibility_timeout=30
                )
                
                if not messages:
                    print("📭 No more messages to delete")
                    break
                
                for msg in messages:
                    try:
                        content = msg.content
                        msg_type = content.get("message_type", "unknown")
                        
                        await self.queue_service.delete_message(msg)
                        deleted_count += 1
                        
                        print(f"  ✅ Deleted message {deleted_count}: {msg.id[:8]}... (Type: {msg_type})")
                        
                    except Exception as e:
                        print(f"  ❌ Failed to delete message {msg.id}: {e}")
            
            print(f"🗑️  Successfully deleted {deleted_count} messages")
        
        except Exception as e:
            print(f"❌ Error receiving/deleting messages: {e}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Azure Storage Queue Management Utility")
    parser.add_argument("command", choices=["peek", "stats", "clear", "delete"], 
                       help="Command to execute")
    parser.add_argument("--count", "-c", type=int, default=10,
                       help="Number of messages (for peek/delete operations)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger()
    
    manager = QueueManager()
    
    try:
        await manager.connect()
        
        if args.command == "peek":
            await manager.peek_messages(args.count)
        
        elif args.command == "stats":
            await manager.get_stats()
        
        elif args.command == "clear":
            await manager.clear_queue()
        
        elif args.command == "delete":
            await manager.receive_and_delete(args.count)
    
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    finally:
        await manager.disconnect()
    
    return 0


if __name__ == "__main__":
    print("Azure Storage Queue Management Utility")
    print("=" * 50)
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
