"""
Source Instance Discovery System

This module handles automatic discovery of source instances from Cosmos DB
and manages their lifecycle for distributed crawler workers.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set

from app.discovery.source_discovery import SourceInstanceDiscovery, SourceInstanceChange


logger = logging.getLogger(f"doc-proc-crawler.source_monitor")


class SourceInstanceMonitor:
    """
    Continuously monitors source instances and triggers callbacks on changes.
    """
    
    def __init__(self, discovery: SourceInstanceDiscovery,
                 poll_interval: int):
        self.discovery = discovery
        self.poll_interval = poll_interval
        
        # Callbacks
        self._on_added_callbacks = []
        self._on_removed_callbacks = []
        self._on_updated_callbacks = []
        
        # Control flags
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
    def on_instance_added(self, callback):
        """Register callback for when source instances are added"""
        self._on_added_callbacks.append(callback)
        
    def on_instance_removed(self, callback):
        """Register callback for when source instances are removed"""  
        self._on_removed_callbacks.append(callback)
        
    def on_instance_updated(self, callback):
        """Register callback for when source instances are updated"""
        self._on_updated_callbacks.append(callback)
        
    async def start(self):
        """Start monitoring source instances"""
        if self._running:
            logger.warning("Monitor is already running")
            return
            
        logger.info(f"Starting source instance monitor (poll interval: {self.poll_interval}s)")
        self._running = True
        
        # Initial discovery
        try:
            await self.discovery.detect_changes()
            logger.info("Initial source instance discovery completed")
        except Exception as e:
            logger.error(f"Initial source instance discovery failed: {e}")
            
        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
    async def stop(self):
        """Stop monitoring"""
        if not self._running:
            return
            
        logger.info("Stopping source instance monitor")
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
            
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                await asyncio.sleep(self.poll_interval)
                
                if not self._running:
                    break
                    
                # Detect changes
                changes = await self.discovery.detect_changes()
                
                # Process changes
                for change in changes:
                    await self._process_change(change)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                # Continue monitoring despite errors
                await asyncio.sleep(5)  # Brief pause before retrying
                
    async def _process_change(self, change: SourceInstanceChange):
        """Process a single source instance change"""
        try:
            if change.change_type == 'added':
                for callback in self._on_added_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(change.instance)
                        else:
                            callback(change.instance)
                    except Exception as e:
                        logger.error(f"Error in added callback: {e}")
                        
            elif change.change_type == 'removed':
                for callback in self._on_removed_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(change.instance_id)
                        else:
                            callback(change.instance_id)
                    except Exception as e:
                        logger.error(f"Error in removed callback: {e}")
                        
            elif change.change_type == 'updated':
                for callback in self._on_updated_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(change.instance)
                        else:
                            callback(change.instance)
                    except Exception as e:
                        logger.error(f"Error in updated callback: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing change for {change.instance_id}: {e}")