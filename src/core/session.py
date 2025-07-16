"""
HTTP session management and configuration.

This module provides enhanced HTTP session configuration with retry logic,
timeout handling, and connection pooling for robust load testing.
"""

import requests
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Optional


class EnhancedHTTPSession:
    """Enhanced HTTP session with retry logic and optimized settings."""
    
    def __init__(self, 
                 max_retries: int = 3,
                 backoff_factor: float = 0.3,
                 timeout: int = 30,
                 pool_connections: int = 10,
                 pool_maxsize: int = 10):
        """
        Initialize enhanced HTTP session.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            timeout: Request timeout in seconds
            pool_connections: Number of connection pools to cache
            pool_maxsize: Maximum number of connections per pool
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
        
        # Disable SSL warnings for testing environments
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def create_session(self) -> requests.Session:
        """
        Create and configure a requests session.
        
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Enable automatic redirect following
        session.max_redirects = 10  # Allow up to 10 redirects
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=self.backoff_factor,
            raise_on_status=False,
            redirect=5  # Allow redirects in retry strategy
        )
        
        # Configure HTTP adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.pool_connections,
            pool_maxsize=self.pool_maxsize
        )
        
        # Mount adapter for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default timeout
        session.timeout = self.timeout
        
        # Set realistic browser headers to avoid blocking
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    def get_session_config(self) -> dict:
        """
        Get current session configuration.
        
        Returns:
            Dictionary containing session configuration
        """
        return {
            'max_retries': self.max_retries,
            'backoff_factor': self.backoff_factor,
            'timeout': self.timeout,
            'pool_connections': self.pool_connections,
            'pool_maxsize': self.pool_maxsize
        }


class SessionManager:
    """Manages HTTP sessions for load testing users."""
    
    def __init__(self):
        """Initialize session manager."""
        self._session_factory = EnhancedHTTPSession()
        self._sessions = {}
    
    def get_session(self, user_id: str) -> requests.Session:
        """
        Get or create a session for a specific user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Configured requests session
        """
        if user_id not in self._sessions:
            self._sessions[user_id] = self._session_factory.create_session()
        
        return self._sessions[user_id]
    
    def close_session(self, user_id: str) -> None:
        """
        Close and remove a user's session.
        
        Args:
            user_id: Unique identifier for the user
        """
        if user_id in self._sessions:
            self._sessions[user_id].close()
            del self._sessions[user_id]
    
    def close_all_sessions(self) -> None:
        """Close all active sessions."""
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
    
    def get_session_count(self) -> int:
        """
        Get the number of active sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self._sessions)
    
    def configure_session_factory(self, **kwargs) -> None:
        """
        Configure the session factory with new parameters.
        
        Args:
            **kwargs: Session configuration parameters
        """
        self._session_factory = EnhancedHTTPSession(**kwargs)
        # Close existing sessions to force recreation with new config
        self.close_all_sessions()


# Global session manager instance
session_manager = SessionManager()
