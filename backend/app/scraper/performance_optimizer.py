"""
Performance optimization and timeout handling
"""
import asyncio
import time
from typing import Dict, Any, Optional
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Optimize scraping performance and handle timeouts"""
    
    def __init__(self, max_total_time: int = 120000):  # 2 minutes
        self.max_total_time = max_total_time
        self.start_time = None
        self.timeout_occurred = False
        
    @asynccontextmanager
    async def timeout_context(self, phase: str, timeout_ms: int = 30000):
        """Context manager for timeout handling"""
        self.timeout_occurred = False
        
        try:
            # Start timeout task
            timeout_task = asyncio.create_task(self._timeout_watcher(timeout_ms, phase))
            yield
            timeout_task.cancel()
            
        except asyncio.TimeoutError:
            self.timeout_occurred = True
            logger.warning(f"Timeout in {phase} after {timeout_ms}ms")
            raise
        except Exception as e:
            logger.error(f"Error in {phase}: {e}")
            raise
    
    async def _timeout_watcher(self, timeout_ms: int, phase: str):
        """Watch for timeouts"""
        await asyncio.sleep(timeout_ms / 1000)
        raise asyncio.TimeoutError(f"{phase} timeout after {timeout_ms}ms")
    
    def check_total_time(self) -> bool:
        """Check if total time exceeded"""
        if not self.start_time:
            self.start_time = time.time()
            return False
        
        elapsed = (time.time() - self.start_time) * 1000
        if elapsed > self.max_total_time:
            self.timeout_occurred = True
            logger.warning(f"Total time exceeded: {elapsed:.0f}ms > {self.max_total_time}ms")
            return True
        
        return False
    
    def get_time_remaining(self) -> float:
        """Get remaining time in milliseconds"""
        if not self.start_time:
            return self.max_total_time
        
        elapsed = (time.time() - self.start_time) * 1000
        return max(0, self.max_total_time - elapsed)
    
    def should_continue(self) -> bool:
        """Check if should continue scraping"""
        return not self.timeout_occurred and not self.check_total_time()
    
    @staticmethod
    async def smart_wait(page, wait_type: str = "networkidle", timeout: int = 10000):
        """Smart waiting strategy"""
        try:
            if wait_type == "networkidle":
                await page.wait_for_load_state('networkidle', timeout=timeout)
            elif wait_type == "domcontentloaded":
                await page.wait_for_load_state('domcontentloaded', timeout=timeout)
            elif wait_type == "load":
                await page.wait_for_load_state('load', timeout=timeout)
            elif wait_type == "selector":
                # Wait for any content selector
                selectors = ['body', 'main', 'article', '[class*="content"]']
                for selector in selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=timeout//len(selectors))
                        break
                    except:
                        continue
            else:
                await asyncio.sleep(2000)  # Default 2-second wait
                
        except Exception as e:
            logger.warning(f"Smart wait failed: {e}")
            # Fallback to short wait
            await asyncio.sleep(1000)
    
    @staticmethod
    def optimize_selectors(selectors: list) -> list:
        """Optimize CSS selectors for performance"""
        optimized = []
        seen = set()
        
        for selector in selectors:
            # Remove duplicate selectors
            if selector not in seen:
                seen.add(selector)
                optimized.append(selector)
        
        # Sort by specificity (simple heuristics)
        optimized.sort(key=lambda s: (
            s.count('#'),  # IDs are most specific
            s.count('.'),  # Classes next
            len(s)         # Shorter selectors are generally faster
        ), reverse=True)
        
        return optimized