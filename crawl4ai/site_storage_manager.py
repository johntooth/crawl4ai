#!/usr/bin/env python3
"""
Site Storage Manager

Manages dual storage architecture for the Domain Intelligence Crawler:
- Downloaded files: E:\\filefinder\\{domain}\\
- Analysis outputs: D:\\Repo\\FileFinder-a Crawl4AI mod\\sites\\{domain}\\
"""

import os
import asyncio
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class StorageType(Enum):
    """Types of storage locations."""
    FILES = "files"          # Downloaded files storage
    ANALYSIS = "analysis"    # Analysis outputs storage


@dataclass
class StorageConfig:
    """Configuration for site storage paths."""
    files_root: str = r"E:\filefinder"
    analysis_root: str = r"D:\Repo\FileFinder-a Crawl4AI mod\sites"
    
    # Subdirectory structure for analysis outputs
    analysis_subdirs: Dict[str, str] = field(default_factory=lambda: {
        'graphs': 'graphs',
        'reports': 'reports', 
        'databases': 'databases',
        'exports': 'exports',
        'visualizations': 'visualizations',
        'logs': 'logs',
        'cache': 'cache',
        'metadata': 'metadata'
    })
    
    # File organization for downloaded files
    files_subdirs: Dict[str, str] = field(default_factory=lambda: {
        'documents': 'documents',
        'images': 'images',
        'archives': 'archives',
        'data': 'data',
        'other': 'other'
    })


@dataclass
class SiteStorageInfo:
    """Information about a site's storage locations."""
    domain: str
    files_path: Path
    analysis_path: Path
    created_at: datetime
    last_accessed: datetime
    total_files: int = 0
    total_size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SiteStorageManager:
    """Manages dual storage architecture for site crawling and analysis."""
    
    def __init__(self, config: Optional[StorageConfig] = None):
        """Initialize storage manager with configuration."""
        self.config = config or StorageConfig()
        self._site_registry: Dict[str, SiteStorageInfo] = {}
        self._ensure_root_directories()
    
    def _ensure_root_directories(self):
        """Ensure root storage directories exist."""
        try:
            Path(self.config.files_root).mkdir(parents=True, exist_ok=True)
            Path(self.config.analysis_root).mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage roots initialized: {self.config.files_root}, {self.config.analysis_root}")
        except Exception as e:
            logger.error(f"Failed to create root directories: {e}")
            raise
    
    def _normalize_domain(self, url_or_domain: str) -> str:
        """Extract and normalize domain name from URL or domain string."""
        if url_or_domain.startswith(('http://', 'https://')):
            parsed = urlparse(url_or_domain)
            domain = parsed.netloc
        else:
            domain = url_or_domain
        
        # Remove www. prefix and normalize
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Ensure domain is valid for filesystem
        domain = domain.replace(':', '_').replace('/', '_')
        return domain.lower()
    
    async def initialize_site_storage(self, url_or_domain: str) -> SiteStorageInfo:
        """Initialize storage directories for a new site."""
        domain = self._normalize_domain(url_or_domain)
        
        if domain in self._site_registry:
            logger.info(f"Site storage already exists for {domain}")
            return self._site_registry[domain]
        
        # Create storage paths
        files_path = Path(self.config.files_root) / domain
        analysis_path = Path(self.config.analysis_root) / domain
        
        try:
            # Create main directories
            await aiofiles.os.makedirs(files_path, exist_ok=True)
            await aiofiles.os.makedirs(analysis_path, exist_ok=True)
            
            # Create file subdirectories
            for subdir_name, subdir_path in self.config.files_subdirs.items():
                subdir_full_path = files_path / subdir_path
                await aiofiles.os.makedirs(subdir_full_path, exist_ok=True)
            
            # Create analysis subdirectories
            for subdir_name, subdir_path in self.config.analysis_subdirs.items():
                subdir_full_path = analysis_path / subdir_path
                await aiofiles.os.makedirs(subdir_full_path, exist_ok=True)
            
            # Create site info
            site_info = SiteStorageInfo(
                domain=domain,
                files_path=files_path,
                analysis_path=analysis_path,
                created_at=datetime.now(),
                last_accessed=datetime.now()
            )
            
            # Save site metadata
            await self._save_site_metadata(site_info)
            
            # Register site
            self._site_registry[domain] = site_info
            
            logger.info(f"Initialized storage for {domain}")
            logger.info(f"  Files: {files_path}")
            logger.info(f"  Analysis: {analysis_path}")
            
            return site_info
            
        except Exception as e:
            logger.error(f"Failed to initialize storage for {domain}: {e}")
            raise
    
    async def get_site_storage(self, url_or_domain: str) -> Optional[SiteStorageInfo]:
        """Get storage information for a site."""
        domain = self._normalize_domain(url_or_domain)
        
        if domain in self._site_registry:
            return self._site_registry[domain]
        
        # Try to load from existing directories
        files_path = Path(self.config.files_root) / domain
        analysis_path = Path(self.config.analysis_root) / domain
        
        if files_path.exists() or analysis_path.exists():
            site_info = await self._load_site_metadata(domain)
            if site_info:
                self._site_registry[domain] = site_info
                return site_info
        
        return None
    
    async def get_file_storage_path(self, url_or_domain: str, 
                                   file_type: str = "other",
                                   create_if_missing: bool = True) -> Path:
        """Get the storage path for downloaded files."""
        domain = self._normalize_domain(url_or_domain)
        
        # Initialize storage if needed
        if create_if_missing:
            site_info = await self.initialize_site_storage(domain)
        else:
            site_info = await self.get_site_storage(domain)
            if not site_info:
                raise ValueError(f"No storage found for domain: {domain}")
        
        # Determine subdirectory based on file type
        subdir = self.config.files_subdirs.get(file_type, "other")
        return site_info.files_path / subdir
    
    async def get_analysis_storage_path(self, url_or_domain: str,
                                       analysis_type: str = "metadata",
                                       create_if_missing: bool = True) -> Path:
        """Get the storage path for analysis outputs."""
        domain = self._normalize_domain(url_or_domain)
        
        # Initialize storage if needed
        if create_if_missing:
            site_info = await self.initialize_site_storage(domain)
        else:
            site_info = await self.get_site_storage(domain)
            if not site_info:
                raise ValueError(f"No storage found for domain: {domain}")
        
        # Determine subdirectory based on analysis type
        subdir = self.config.analysis_subdirs.get(analysis_type, "metadata")
        return site_info.analysis_path / subdir
    
    async def store_downloaded_file(self, url_or_domain: str, 
                                   file_url: str,
                                   file_content: bytes,
                                   file_type: str = "other",
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a downloaded file and return the storage path."""
        domain = self._normalize_domain(url_or_domain)
        
        # Get storage path
        storage_path = await self.get_file_storage_path(domain, file_type)
        
        # Generate filename from URL
        parsed_url = urlparse(file_url)
        filename = Path(parsed_url.path).name
        if not filename:
            filename = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure unique filename
        file_path = storage_path / filename
        counter = 1
        while file_path.exists():
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                new_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                new_filename = f"{filename}_{counter}"
            file_path = storage_path / new_filename
            counter += 1
        
        try:
            # Write file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Store metadata if provided
            if metadata:
                metadata_path = file_path.with_suffix(file_path.suffix + '.meta.json')
                metadata_with_info = {
                    **metadata,
                    'original_url': file_url,
                    'downloaded_at': datetime.now().isoformat(),
                    'file_size': len(file_content),
                    'storage_path': str(file_path)
                }
                
                async with aiofiles.open(metadata_path, 'w') as f:
                    await f.write(json.dumps(metadata_with_info, indent=2))
            
            # Update site statistics
            await self._update_site_stats(domain, file_size=len(file_content))
            
            logger.info(f"Stored file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to store file {file_url}: {e}")
            raise
    
    async def store_analysis_output(self, url_or_domain: str,
                                   output_name: str,
                                   content: Union[str, bytes, Dict[str, Any]],
                                   analysis_type: str = "metadata",
                                   file_extension: str = ".json") -> str:
        """Store analysis output and return the storage path."""
        domain = self._normalize_domain(url_or_domain)
        
        # Get storage path
        storage_path = await self.get_analysis_storage_path(domain, analysis_type)
        
        # Create filename
        if not output_name.endswith(file_extension):
            output_name += file_extension
        
        file_path = storage_path / output_name
        
        try:
            # Handle different content types
            if isinstance(content, dict):
                # JSON content
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(content, indent=2, default=str))
            elif isinstance(content, str):
                # Text content
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            elif isinstance(content, bytes):
                # Binary content
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
            else:
                raise ValueError(f"Unsupported content type: {type(content)}")
            
            logger.info(f"Stored analysis output: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to store analysis output {output_name}: {e}")
            raise
    
    async def get_site_file_list(self, url_or_domain: str, 
                                file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of files stored for a site."""
        domain = self._normalize_domain(url_or_domain)
        site_info = await self.get_site_storage(domain)
        
        if not site_info:
            return []
        
        files = []
        
        # Determine which directories to scan
        if file_type and file_type in self.config.files_subdirs:
            scan_dirs = [site_info.files_path / self.config.files_subdirs[file_type]]
        else:
            scan_dirs = [site_info.files_path / subdir 
                        for subdir in self.config.files_subdirs.values()]
        
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
                
            for file_path in scan_dir.rglob('*'):
                if file_path.is_file() and not file_path.name.endswith('.meta.json'):
                    file_info = {
                        'path': str(file_path),
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'type': file_path.suffix.lower(),
                        'relative_path': str(file_path.relative_to(site_info.files_path))
                    }
                    
                    # Load metadata if available
                    metadata_path = file_path.with_suffix(file_path.suffix + '.meta.json')
                    if metadata_path.exists():
                        try:
                            async with aiofiles.open(metadata_path, 'r') as f:
                                metadata_content = await f.read()
                                file_info['metadata'] = json.loads(metadata_content)
                        except Exception as e:
                            logger.warning(f"Failed to load metadata for {file_path}: {e}")
                    
                    files.append(file_info)
        
        return sorted(files, key=lambda x: x['modified'], reverse=True)
    
    async def get_site_analysis_outputs(self, url_or_domain: str,
                                       analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of analysis outputs for a site."""
        domain = self._normalize_domain(url_or_domain)
        site_info = await self.get_site_storage(domain)
        
        if not site_info:
            return []
        
        outputs = []
        
        # Determine which directories to scan
        if analysis_type and analysis_type in self.config.analysis_subdirs:
            scan_dirs = [site_info.analysis_path / self.config.analysis_subdirs[analysis_type]]
        else:
            scan_dirs = [site_info.analysis_path / subdir 
                        for subdir in self.config.analysis_subdirs.values()]
        
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
                
            for file_path in scan_dir.rglob('*'):
                if file_path.is_file():
                    output_info = {
                        'path': str(file_path),
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'type': file_path.suffix.lower(),
                        'analysis_type': scan_dir.name,
                        'relative_path': str(file_path.relative_to(site_info.analysis_path))
                    }
                    outputs.append(output_info)
        
        return sorted(outputs, key=lambda x: x['modified'], reverse=True)
    
    async def get_storage_statistics(self, url_or_domain: Optional[str] = None) -> Dict[str, Any]:
        """Get storage statistics for a site or all sites."""
        if url_or_domain:
            # Single site statistics
            domain = self._normalize_domain(url_or_domain)
            site_info = await self.get_site_storage(domain)
            
            if not site_info:
                return {}
            
            files = await self.get_site_file_list(domain)
            outputs = await self.get_site_analysis_outputs(domain)
            
            return {
                'domain': domain,
                'files_count': len(files),
                'total_file_size': sum(f['size'] for f in files),
                'analysis_outputs_count': len(outputs),
                'total_analysis_size': sum(o['size'] for o in outputs),
                'created_at': site_info.created_at.isoformat(),
                'last_accessed': site_info.last_accessed.isoformat(),
                'files_path': str(site_info.files_path),
                'analysis_path': str(site_info.analysis_path)
            }
        else:
            # All sites statistics
            all_stats = []
            total_files = 0
            total_size = 0
            
            # Scan for all site directories
            files_root = Path(self.config.files_root)
            if files_root.exists():
                for site_dir in files_root.iterdir():
                    if site_dir.is_dir():
                        try:
                            site_stats = await self.get_storage_statistics(site_dir.name)
                            if site_stats:
                                all_stats.append(site_stats)
                                total_files += site_stats['files_count']
                                total_size += site_stats['total_file_size']
                        except Exception as e:
                            logger.warning(f"Failed to get stats for {site_dir.name}: {e}")
            
            return {
                'total_sites': len(all_stats),
                'total_files': total_files,
                'total_size': total_size,
                'sites': all_stats
            }
    
    async def cleanup_site_storage(self, url_or_domain: str, 
                                  older_than_days: Optional[int] = None) -> Dict[str, int]:
        """Clean up old files for a site."""
        domain = self._normalize_domain(url_or_domain)
        site_info = await self.get_site_storage(domain)
        
        if not site_info:
            return {'files_removed': 0, 'bytes_freed': 0}
        
        files_removed = 0
        bytes_freed = 0
        cutoff_date = None
        
        if older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        # Clean up files
        for file_type_dir in site_info.files_path.rglob('*'):
            if file_type_dir.is_file():
                file_modified = datetime.fromtimestamp(file_type_dir.stat().st_mtime)
                
                if cutoff_date and file_modified > cutoff_date:
                    continue
                
                try:
                    file_size = file_type_dir.stat().st_size
                    await aiofiles.os.remove(file_type_dir)
                    files_removed += 1
                    bytes_freed += file_size
                    
                    # Remove metadata file if exists
                    metadata_path = file_type_dir.with_suffix(file_type_dir.suffix + '.meta.json')
                    if metadata_path.exists():
                        await aiofiles.os.remove(metadata_path)
                        
                except Exception as e:
                    logger.warning(f"Failed to remove {file_type_dir}: {e}")
        
        logger.info(f"Cleanup completed for {domain}: {files_removed} files, {bytes_freed} bytes")
        return {'files_removed': files_removed, 'bytes_freed': bytes_freed}
    
    async def _save_site_metadata(self, site_info: SiteStorageInfo):
        """Save site metadata to disk."""
        metadata_path = site_info.analysis_path / "metadata" / "site_info.json"
        
        metadata = {
            'domain': site_info.domain,
            'files_path': str(site_info.files_path),
            'analysis_path': str(site_info.analysis_path),
            'created_at': site_info.created_at.isoformat(),
            'last_accessed': site_info.last_accessed.isoformat(),
            'total_files': site_info.total_files,
            'total_size_bytes': site_info.total_size_bytes,
            'metadata': site_info.metadata
        }
        
        try:
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save metadata for {site_info.domain}: {e}")
    
    async def _load_site_metadata(self, domain: str) -> Optional[SiteStorageInfo]:
        """Load site metadata from disk."""
        analysis_path = Path(self.config.analysis_root) / domain
        metadata_path = analysis_path / "metadata" / "site_info.json"
        
        if not metadata_path.exists():
            # Create default metadata for existing directories
            files_path = Path(self.config.files_root) / domain
            if files_path.exists() or analysis_path.exists():
                return SiteStorageInfo(
                    domain=domain,
                    files_path=files_path,
                    analysis_path=analysis_path,
                    created_at=datetime.now(),
                    last_accessed=datetime.now()
                )
            return None
        
        try:
            async with aiofiles.open(metadata_path, 'r') as f:
                content = await f.read()
                metadata = json.loads(content)
            
            return SiteStorageInfo(
                domain=metadata['domain'],
                files_path=Path(metadata['files_path']),
                analysis_path=Path(metadata['analysis_path']),
                created_at=datetime.fromisoformat(metadata['created_at']),
                last_accessed=datetime.fromisoformat(metadata['last_accessed']),
                total_files=metadata.get('total_files', 0),
                total_size_bytes=metadata.get('total_size_bytes', 0),
                metadata=metadata.get('metadata', {})
            )
        except Exception as e:
            logger.warning(f"Failed to load metadata for {domain}: {e}")
            return None
    
    async def _update_site_stats(self, domain: str, file_size: int = 0):
        """Update site statistics."""
        if domain in self._site_registry:
            site_info = self._site_registry[domain]
            site_info.total_files += 1
            site_info.total_size_bytes += file_size
            site_info.last_accessed = datetime.now()
            
            # Save updated metadata
            await self._save_site_metadata(site_info)


# Utility functions for easy integration
async def get_site_storage_manager(config: Optional[StorageConfig] = None) -> SiteStorageManager:
    """Get a configured site storage manager instance."""
    return SiteStorageManager(config)


async def initialize_site_for_crawling(url: str, 
                                     config: Optional[StorageConfig] = None) -> Tuple[Path, Path]:
    """Initialize storage for a site and return file and analysis paths."""
    manager = await get_site_storage_manager(config)
    site_info = await manager.initialize_site_storage(url)
    return site_info.files_path, site_info.analysis_path


async def store_crawl_file(url: str, file_url: str, content: bytes,
                          file_type: str = "documents",
                          metadata: Optional[Dict[str, Any]] = None,
                          config: Optional[StorageConfig] = None) -> str:
    """Convenience function to store a crawled file."""
    manager = await get_site_storage_manager(config)
    return await manager.store_downloaded_file(url, file_url, content, file_type, metadata)


async def store_analysis_result(url: str, analysis_name: str, 
                               result: Any, analysis_type: str = "reports",
                               config: Optional[StorageConfig] = None) -> str:
    """Convenience function to store analysis results."""
    manager = await get_site_storage_manager(config)
    return await manager.store_analysis_output(url, analysis_name, result, analysis_type)