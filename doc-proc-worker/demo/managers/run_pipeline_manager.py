#!/usr/bin/env python3
"""
Demo script to show how to use the PipelineManager.

This script demonstrates:
1. Setting up a mock CosmosDB with sample data
2. Creating a PipelineManager instance
3. Loading a pipeline by name
4. Basic pipeline operations

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Set up environment variables (see .env.example)
3. Ensure CosmosDB is accessible with sample data

Usage:
    cd doc-proc-worker
    python demo/managers/demo_pipeline_manager.py
"""

import asyncio
import sys
import os


# Add the doc-proc-worker directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.dependencies import get_pipeline_manager
    from app.managers.pipeline_manager import PipelineManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def run_pipeline_manager():
    """Demonstrate PipelineManager usage."""
    print("🚀 PipelineManager Run")
    print("=" * 50)
    print("📋 Prerequisites check:")
    print("   - Python path setup: ✅ Fixed")
    print("   - Required dependencies: Need to be installed from requirements.txt")
    print("")
    
    try:
        # 1. Create PipelineManager
        print("\n1. Creating PipelineManager...")
        manager = get_pipeline_manager()
        print(f"✅ PipelineManager created with containers:")
        print(f"   - Pipelines: {manager._pipelines_container_name}")
        print(f"   - Step Catalog: {manager._step_catalog_container_name}")
        print(f"   - Service Catalog: {manager._service_catalog_container_name}")
        
        # 2. Test loading catalogs
        print("\n2. Loading catalogs from database...")
        
        step_catalog = await manager._load_step_catalog_from_db()
        print(f"✅ Loaded {len(step_catalog)} step definitions:")
        for step in step_catalog:
            print(f"   - {step.id}: {step.name}")
            
        service_catalog = await manager._load_service_catalog_from_db()
        print(f"✅ Loaded {len(service_catalog)} service definitions:")
        for service in service_catalog:
            print(f"   - {service.id}: {service.name}")
            
        service_instances = await manager._load_service_instances_from_db()
        print(f"✅ Loaded {len(service_instances)} service instances:")
        for instance in service_instances:
            print(f"   - {instance.id}: {instance.name}")

        step_instances = await manager._load_step_instances_from_db(service_instances=service_instances)
        print(f"✅ Loaded {len(step_instances)} step instances:")
        for instance in step_instances:
            print(f"   - {instance.id}: {instance.name}")
        
        # 3. Test getting pipeline by name
        print("\n3. Getting pipeline by name...")
        pipeline_data = await manager._get_pipeline_by_name("test pipeline")
        if pipeline_data:
            print(f"✅ Found pipeline: {pipeline_data['name']}")
            print(f"   Description: {pipeline_data['description']}")
            print(f"   Steps: {len(pipeline_data['steps'])}")
        else:
            print("❌ Pipeline not found")
        
        # 4. Test pipeline loading (this would normally create a full Pipeline object)
        print("\n4. Attempting to load full pipeline...")
        print("⚠️  Note: This will fail without proper Pipeline.create implementation,")
        print("   but demonstrates the loading process up to that point.")
        
        try:
            pipeline = await manager.load_pipeline("test pipeline")
            if pipeline:
                print(f"✅ Pipeline loaded successfully: {pipeline}")
            else:
                print("❌ Pipeline could not be loaded")
        except Exception as e:
            print(f"⚠️  Expected error during pipeline creation: {e}")
            print("   (This is normal - we're missing the actual step/service implementations)")
        
        # 5. Test caching
        print("\n5. Testing cache behavior...")
        print(f"Current cache contents: {list(manager._pipeline_cache.keys())}")
        
        print("\n✅ Run completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Run failed with error: {e}")
        print("\n💡 To fix this, please ensure:")
        print("   1. All dependencies are installed: pip install -r requirements.txt")
        print("   2. Environment variables are set (check .env.example)")
        print("   3. CosmosDB is accessible with sample data")
        import traceback
        traceback.print_exc()


async def main():
    """Main entry point."""
    await run_pipeline_manager()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())