"""
Retry utilities with exponential backoff for ETL operations
"""
import asyncio
import httpx
import logging
from typing import Callable, Any, Optional, List, Type
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_status_codes: Optional[List[int]] = None,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        """
        Initialize retry configuration
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff calculation
            retryable_status_codes: HTTP status codes that should trigger a retry
            retryable_exceptions: Exception types that should trigger a retry
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        
        # Default retryable status codes (5xx errors, 429 rate limit, 408 timeout)
        self.retryable_status_codes = retryable_status_codes or [
            408,  # Request Timeout
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        ]
        
        # Default retryable exceptions (network errors, timeouts)
        self.retryable_exceptions = retryable_exceptions or [
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.RemoteProtocolError,
            httpx.ConnectError,
            asyncio.TimeoutError,
        ]
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt using exponential backoff"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, attempt: int, error: Exception = None, status_code: int = None) -> bool:
        """Determine if we should retry based on the error or status code"""
        if attempt >= self.max_attempts:
            return False
        
        # Check HTTP status codes
        if status_code is not None:
            return status_code in self.retryable_status_codes
        
        # Check exception types
        if error is not None:
            return any(isinstance(error, exc_type) for exc_type in self.retryable_exceptions)
        
        return False


def retry_with_backoff(config: Optional[RetryConfig] = None):
    """
    Decorator for async functions to add retry logic with exponential backoff
    
    Usage:
        @retry_with_backoff(RetryConfig(max_attempts=3))
        async def my_function():
            # Your code here
            pass
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            last_error = None
            
            while attempt < config.max_attempts:
                try:
                    # Attempt the function call
                    result = await func(*args, **kwargs)
                    
                    # If it's an HTTP response, check status code
                    if hasattr(result, 'status_code'):
                        status_code = result.status_code
                        if config.should_retry(attempt, status_code=status_code):
                            delay = config.calculate_delay(attempt)
                            logger.warning(
                                f"📡 {func.__name__}: HTTP {status_code} on attempt {attempt + 1}/{config.max_attempts}. "
                                f"Retrying in {delay:.1f}s..."
                            )
                            await asyncio.sleep(delay)
                            attempt += 1
                            continue
                    
                    # Success!
                    if attempt > 0:
                        logger.info(f"✅ {func.__name__}: Succeeded on attempt {attempt + 1}")
                    return result
                
                except Exception as e:
                    last_error = e
                    
                    # Check if this error is retryable
                    if config.should_retry(attempt, error=e):
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"⚠️  {func.__name__}: {type(e).__name__} on attempt {attempt + 1}/{config.max_attempts}. "
                            f"Retrying in {delay:.1f}s... Error: {str(e)}"
                        )
                        await asyncio.sleep(delay)
                        attempt += 1
                    else:
                        # Non-retryable error, fail immediately
                        logger.error(f"❌ {func.__name__}: Non-retryable error: {type(e).__name__}: {str(e)}")
                        raise
            
            # All attempts exhausted
            logger.error(
                f"❌ {func.__name__}: Failed after {config.max_attempts} attempts. "
                f"Last error: {type(last_error).__name__}: {str(last_error)}"
            )
            raise last_error
        
        return wrapper
    return decorator


class ProgressTracker:
    """Track and log progress of long-running operations"""
    
    def __init__(self, total: int, operation_name: str = "Operation", log_interval: int = 10):
        """
        Initialize progress tracker
        
        Args:
            total: Total number of items to process
            operation_name: Name of the operation for logging
            log_interval: Log progress every N percent
        """
        self.total = total
        self.current = 0
        self.operation_name = operation_name
        self.log_interval = log_interval
        self.start_time = datetime.now()
        self.last_logged_percent = 0
    
    def update(self, increment: int = 1):
        """Update progress and log if threshold reached"""
        self.current += increment
        
        if self.total == 0:
            return
        
        percent = (self.current / self.total) * 100
        
        # Log every log_interval percent
        if percent - self.last_logged_percent >= self.log_interval or self.current >= self.total:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            if self.current > 0:
                avg_time_per_item = elapsed / self.current
                remaining_items = self.total - self.current
                eta_seconds = avg_time_per_item * remaining_items
                eta_minutes = eta_seconds / 60
                
                logger.info(
                    f"📊 {self.operation_name}: {self.current}/{self.total} ({percent:.1f}%) | "
                    f"Elapsed: {elapsed/60:.1f}min | ETA: {eta_minutes:.1f}min"
                )
            else:
                logger.info(f"📊 {self.operation_name}: Starting...")
            
            self.last_logged_percent = int(percent / self.log_interval) * self.log_interval
    
    def complete(self):
        """Mark operation as complete and log final stats"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        logger.info(
            f"✅ {self.operation_name}: Complete! {self.total} items in {elapsed/60:.1f}min "
            f"({elapsed/self.total:.2f}s per item)"
        )


async def retry_http_call(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> httpx.Response:
    """
    Make an HTTP call with retry logic
    
    Args:
        client: httpx.AsyncClient instance
        method: HTTP method (GET, POST, etc.)
        url: URL to call
        config: RetryConfig instance
        **kwargs: Additional arguments to pass to the HTTP call
    
    Returns:
        httpx.Response object
    """
    if config is None:
        config = RetryConfig()
    
    @retry_with_backoff(config)
    async def _make_request():
        return await client.request(method, url, **kwargs)
    
    return await _make_request()

