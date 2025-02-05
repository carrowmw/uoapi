# src/async_api_client.py
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import psutil
import os
from .api_client import APIConfig, APIError


@dataclass
class AsyncAPIConfig:
    base_url: str = "https://newcastle.urbanobservatory.ac.uk/api/v1.1"
    timeout: int = 30
    max_concurrent_requests: int = 3
    retry_attempts: int = 3
    retry_delay: int = 1
    memory_threshold_mb: int = 500


class AsyncAPIClient:
    def __init__(self, config: Optional[AsyncAPIConfig] = None):
        self.config = config or AsyncAPIConfig()
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.memory_threshold = self.config.memory_threshold_mb * 1024 * 1024

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _check_memory(self):
        process = psutil.Process(os.getpid())
        if process.memory_info().rss > self.memory_threshold:
            self.logger.warning(
                "Memory threshold exceeded, waiting for memory to free up"
            )
            await asyncio.sleep(5)

    async def _make_request(
        self, url: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        await self._check_memory()
        async with self.semaphore:
            for attempt in range(self.config.retry_attempts):
                try:
                    async with self.session.get(url, params=params) as response:
                        response.raise_for_status()
                        return await response.json()
                except Exception as e:
                    if attempt == self.config.retry_attempts - 1:
                        self.logger.error(
                            f"Failed after {self.config.retry_attempts} attempts: {str(e)}"
                        )
                        raise APIError(f"Async request failed: {str(e)}")
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))

    async def get_sensor_data_batch(
        self, sensor_names: List[str], last_n_days: int = 1
    ) -> Dict[str, Any]:
        tasks = []
        for sensor_name in sensor_names:
            url = f"{self.config.base_url}/sensors/{sensor_name}/data/json/"
            params = {"last_n_days": last_n_days}
            tasks.append(self._make_request(url, params))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            sensor_name: result if not isinstance(result, Exception) else None
            for sensor_name, result in zip(sensor_names, results)
        }
