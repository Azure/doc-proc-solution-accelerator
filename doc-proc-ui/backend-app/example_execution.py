#!/usr/bin/env python3
"""
Example script demonstrating the Document Processing Pipeline Execution API.

This script shows how to:
1. Create a batch execution
2. Start the execution
3. Monitor progress
4. Retrieve results

Requirements:
    pip install httpx

Usage:
    python example_execution.py
"""

import time
import json
import asyncio
import httpx


API_BASE_URL = "http://localhost:8000/api"


async def main():
    """Main example function."""
    
    async with httpx.AsyncClient() as client:
        
        print("🚀 Document Processing Pipeline Execution Example")
        print("=" * 60)
        
        # Step 1: Check if API is available
        try:
            response = await client.get(f"{API_BASE_URL}/../health")
            if response.status_code != 200:
                print("❌ API server is not running. Please start it first.")
                return
            print("✅ API server is running")
        except httpx.ConnectError:
            print("❌ Cannot connect to API server. Please start it first.")
            return
        
        # Step 2: List available pipelines
        print("\n📋 Available pipeline instances:")
        try:
            response = await client.get(f"{API_BASE_URL}/pipelines/")
            if response.status_code == 200:
                pipelines = response.json()
                if pipelines:
                    for pipeline in pipelines[:3]:  # Show first 3
                        print(f"  - {pipeline['id']}: {pipeline['name']}")
                    
                    # Use the first pipeline for the example
                    pipeline_id = pipelines[0]["id"]
                    print(f"\n🎯 Using pipeline: {pipeline_id}")
                else:
                    print("  No pipelines found. Creating a sample pipeline reference...")
                    pipeline_id = "sample_pipeline_01"
            else:
                print("  Could not fetch pipelines. Using sample ID...")
                pipeline_id = "sample_pipeline_01"
        except Exception as e:
            print(f"  Error fetching pipelines: {e}")
            pipeline_id = "sample_pipeline_01"
        
        # Step 3: Create sample documents
        sample_documents = [
            {
                "container_name": "documents",
                "blob_name": "sample_document_1.pdf",
                "url": "https://example-storage.blob.core.windows.net/documents/sample_document_1.pdf",
                "content_type": "application/pdf",
                "size_bytes": 1024000
            },
            {
                "container_name": "documents",
                "blob_name": "sample_document_2.pdf", 
                "url": "https://example-storage.blob.core.windows.net/documents/sample_document_2.pdf",
                "content_type": "application/pdf",
                "size_bytes": 2048000
            }
        ]
        
        # Step 4: Create batch execution
        print("\n📄 Creating batch execution...")
        batch_request = {
            "pipeline_instance_id": pipeline_id,
            "documents": sample_documents,
            "batch_name": "Example Document Processing Batch",
            "priority": 1,
            "metadata": {
                "example": True,
                "created_by": "example_script",
                "department": "engineering"
            }
        }
        
        try:
            response = await client.post(
                f"{API_BASE_URL}/executions/",
                json=batch_request
            )
            
            if response.status_code == 200:
                batch = response.json()
                batch_id = batch["id"]
                print(f"✅ Batch created: {batch_id}")
                print(f"   Name: {batch['name']}")
                print(f"   Documents: {batch['total_documents']}")
            else:
                print(f"❌ Failed to create batch: {response.status_code}")
                print(f"   Error: {response.text}")
                return
                
        except Exception as e:
            print(f"❌ Error creating batch: {e}")
            return
        
        # Step 5: Start execution
        print(f"\n▶️ Starting batch execution...")
        try:
            response = await client.post(f"{API_BASE_URL}/executions/{batch_id}/start")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Execution started")
                print(f"   Task ID: {result['task_id']}")
            else:
                print(f"❌ Failed to start execution: {response.status_code}")
                print(f"   Error: {response.text}")
                return
                
        except Exception as e:
            print(f"❌ Error starting execution: {e}")
            return
        
        # Step 6: Monitor progress
        print(f"\n📊 Monitoring execution progress...")
        print("=" * 60)
        
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = await client.get(f"{API_BASE_URL}/executions/{batch_id}/status")
                
                if response.status_code == 200:
                    status = response.json()
                    
                    print(f"\r📈 Status: {status['status']} | "
                          f"Progress: {status['progress']:.1f}% | "
                          f"Completed: {status['completed_documents']}/{status['total_documents']} | "
                          f"Failed: {status['failed_documents']}", end="")
                    
                    if status["current_step"]:
                        print(f" | Current: {status['current_step']}", end="")
                    
                    # Check if completed
                    if status["status"] in ["completed", "failed", "cancelled"]:
                        print(f"\n\n🏁 Execution {status['status']}")
                        break
                        
                else:
                    print(f"\n❌ Error getting status: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"\n❌ Error monitoring progress: {e}")
                break
            
            await asyncio.sleep(2)  # Check every 2 seconds
        else:
            print(f"\n⏰ Timeout waiting for execution to complete")
        
        # Step 7: Get final results
        print(f"\n📋 Retrieving execution results...")
        
        try:
            # Get final batch details
            response = await client.get(f"{API_BASE_URL}/executions/{batch_id}")
            if response.status_code == 200:
                batch = response.json()
                print(f"✅ Final batch status: {batch['status']}")
                print(f"   Total documents: {batch['total_documents']}")
                print(f"   Completed: {batch['completed_documents']}")
                print(f"   Failed: {batch['failed_documents']}")
                
                if batch['started_at']:
                    print(f"   Started: {batch['started_at']}")
                if batch['completed_at']:
                    print(f"   Completed: {batch['completed_at']}")
            
            # Get recent activities
            response = await client.get(f"{API_BASE_URL}/executions/{batch_id}/activities?limit=10")
            if response.status_code == 200:
                activities = response.json()
                print(f"\n📝 Recent activities ({len(activities)}):")
                for activity in activities[:5]:  # Show last 5
                    print(f"   • {activity['activity_type']}: {activity['message']}")
                    if activity.get('error_message'):
                        print(f"     Error: {activity['error_message']}")
            
            # Get step outputs
            response = await client.get(f"{API_BASE_URL}/executions/{batch_id}/step-outputs")
            if response.status_code == 200:
                outputs = response.json()
                print(f"\n📊 Step outputs ({len(outputs)}):")
                for output in outputs[:3]:  # Show first 3
                    print(f"   • Step: {output['step_name']}")
                    print(f"     Document: {output['document_id']}")
                    print(f"     Status: {output['status']}")
                    print(f"     Duration: {output['execution_time_ms']}ms")
                    if output.get('error_message'):
                        print(f"     Error: {output['error_message']}")
                    print()
            
        except Exception as e:
            print(f"❌ Error retrieving results: {e}")
        
        print("=" * 60)
        print("🎉 Example completed!")
        print(f"\n💡 You can now:")
        print(f"   • View execution details: GET {API_BASE_URL}/executions/{batch_id}")
        print(f"   • Monitor via Flower: http://localhost:5555 (if running)")
        print(f"   • Check API docs: http://localhost:8000/docs")


def print_json(data, title="JSON Data"):
    """Pretty print JSON data."""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
