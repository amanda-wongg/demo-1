"""
State Management for Cash Completeness Monitor
Handles persistence of known variances and system state to avoid duplicate alerts.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class StateManager:
    """Manages persistent state for the monitoring system."""
    
    def __init__(self, storage_path: str = "state.json"):
        """
        Initialize state manager.
        
        Args:
            storage_path: Path to the state storage file
        """
        self.storage_path = Path(storage_path)
        self.state_data = self._load_state()
        
        logger.info(f"State manager initialized with storage: {self.storage_path}")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from storage file."""
        if not self.storage_path.exists():
            logger.info("No existing state file found, creating new state")
            return self._create_initial_state()
        
        try:
            with open(self.storage_path, 'r') as f:
                state = json.load(f)
            
            logger.info(f"Loaded state with {len(state.get('known_variances', {}))} known variances")
            return state
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load state file: {str(e)}")
            logger.info("Creating new state file")
            return self._create_initial_state()
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """Create initial state structure."""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "last_check_time": None,
            "known_variances": {},
            "system_metrics": {
                "total_checks_performed": 0,
                "total_variances_detected": 0,
                "total_alerts_sent": 0
            }
        }
    
    def _save_state(self):
        """Save current state to storage file."""
        try:
            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Update timestamp
            self.state_data["last_updated"] = datetime.now().isoformat()
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = self.storage_path.with_suffix('.tmp')
            
            with open(temp_path, 'w') as f:
                json.dump(self.state_data, f, indent=2, sort_keys=True)
            
            # Atomic rename
            temp_path.rename(self.storage_path)
            
            logger.debug("State saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save state: {str(e)}")
            raise
    
    def get_known_variances(self) -> Dict[str, Dict[str, Any]]:
        """Get all known variances."""
        return self.state_data.get("known_variances", {})
    
    def add_known_variance(self, variance_id: str, variance_data: Dict[str, Any]):
        """
        Add a variance to the known variances list.
        
        Args:
            variance_id: Unique identifier for the variance
            variance_data: Variance details
        """
        self.state_data["known_variances"][variance_id] = {
            **variance_data,
            "first_detected": datetime.now().isoformat(),
            "times_seen": 1
        }
        
        # Update metrics
        self.state_data["system_metrics"]["total_variances_detected"] += 1
        
        self._save_state()
        logger.info(f"Added known variance: {variance_id}")
    
    def update_variance_seen_count(self, variance_id: str):
        """Update the seen count for a known variance."""
        if variance_id in self.state_data["known_variances"]:
            self.state_data["known_variances"][variance_id]["times_seen"] += 1
            self.state_data["known_variances"][variance_id]["last_seen"] = datetime.now().isoformat()
            self._save_state()
            logger.debug(f"Updated seen count for variance: {variance_id}")
    
    def is_variance_known(self, variance_id: str) -> bool:
        """Check if a variance is already known."""
        return variance_id in self.state_data.get("known_variances", {})
    
    def remove_known_variance(self, variance_id: str) -> bool:
        """
        Remove a variance from known variances (for manual cleanup).
        
        Args:
            variance_id: Variance ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if variance_id in self.state_data.get("known_variances", {}):
            del self.state_data["known_variances"][variance_id]
            self._save_state()
            logger.info(f"Removed known variance: {variance_id}")
            return True
        
        return False
    
    def get_last_check_time(self) -> Optional[str]:
        """Get the timestamp of the last check."""
        return self.state_data.get("last_check_time")
    
    def update_last_check_time(self, timestamp: Optional[str] = None):
        """Update the last check timestamp."""
        self.state_data["last_check_time"] = timestamp or datetime.now().isoformat()
        self.state_data["system_metrics"]["total_checks_performed"] += 1
        self._save_state()
    
    def increment_alerts_sent(self, count: int = 1):
        """Increment the alerts sent counter."""
        self.state_data["system_metrics"]["total_alerts_sent"] += count
        self._save_state()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        return self.state_data.get("system_metrics", {})
    
    def cleanup_old_variances(self, days_threshold: int = 90):
        """
        Clean up variances older than the specified threshold.
        
        Args:
            days_threshold: Remove variances older than this many days
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        variances_to_remove = []
        
        for variance_id, variance_data in self.state_data.get("known_variances", {}).items():
            try:
                first_detected = datetime.fromisoformat(variance_data["first_detected"])
                if first_detected < cutoff_date:
                    variances_to_remove.append(variance_id)
            except (KeyError, ValueError):
                # Remove variances with invalid dates
                variances_to_remove.append(variance_id)
        
        # Remove old variances
        for variance_id in variances_to_remove:
            del self.state_data["known_variances"][variance_id]
        
        if variances_to_remove:
            self._save_state()
            logger.info(f"Cleaned up {len(variances_to_remove)} old variances")
        
        return len(variances_to_remove)
    
    def export_state(self, export_path: str) -> bool:
        """
        Export current state to a different file.
        
        Args:
            export_path: Path to export the state to
            
        Returns:
            True if successful
        """
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w') as f:
                json.dump(self.state_data, f, indent=2, sort_keys=True)
            
            logger.info(f"State exported to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export state: {str(e)}")
            return False
    
    def get_variance_summary(self) -> Dict[str, Any]:
        """Get a summary of known variances."""
        known_variances = self.get_known_variances()
        
        if not known_variances:
            return {"total": 0, "summary": "No known variances"}
        
        # Calculate summary statistics
        total_count = len(known_variances)
        accounts = set()
        check_types = set()
        total_amount = 0
        
        for variance_data in known_variances.values():
            accounts.add(variance_data.get("account", "Unknown"))
            check_types.add(variance_data.get("check_type", "Unknown"))
            total_amount += abs(variance_data.get("delta_amount", 0))
        
        return {
            "total": total_count,
            "unique_accounts": len(accounts),
            "unique_check_types": len(check_types),
            "total_amount": total_amount,
            "accounts": sorted(list(accounts)),
            "check_types": sorted(list(check_types))
        }