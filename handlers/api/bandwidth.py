import json
import httpx
import os

class BandwidthAPI:
    def __init__(self, token=None, base_url=None, cookies=None):
        self.token = token or os.getenv("API_TOKEN", "")
        self.base_url = base_url or os.getenv("REMNAWAVE_BASE_URL", "")
        self.cookies = cookies or json.loads(os.getenv("COOKIES", "{}"))
        self.is_local = os.getenv("IS_LOCAL_NETWORK", "false").lower() == "true"
        self._client = None
    
    def _get_headers(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.token
        }
        
        # Добавляем заголовки для локальной сети
        if self.is_local:
            headers.update({
                "X-Forwarded-Proto": "https",
                "X-Forwarded-For": "127.0.0.1"
            })
        
        return headers
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(cookies=self.cookies)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def _get_client(self):
        """Возвращает HTTP-клиент, создавая новый если необходимо"""
        if not self._client:
            return httpx.AsyncClient(cookies=self.cookies)
        return self._client
    
    async def _make_request(self, method, url, **kwargs):
        """Выполняет HTTP-запрос и обрабатывает закрытие клиента"""
        client = await self._get_client()
        created_new = client != self._client
        
        try:
            response = await getattr(client, method)(
                url, 
                headers=self._get_headers(),
                **kwargs
            )
            return response.json()
        finally:
            if created_new:
                await client.aclose()
                
    async def get_nodes_rt_usage(self):
        """
        Получает текущую статистику использования трафика по узлам.
        
        Returns:
            dict: Ответ API с информацией о трафике.
        """
        return await self._make_request(
            "get",
            f"{self.base_url}/api/nodes/usage/realtime"
        )

    async def get_nodes_usage_by_range(self, start_time, end_time):
        """
        Получает статистику использования трафика по узлам за указанный период времени.
        
        Args:
            start_time (str): Время начала периода.
            end_time (str): Время окончания периода.
            
        Returns:
            dict: Ответ API с информацией о трафике.
        """
        return await self._make_request(
            "get",
            f"{self.base_url}/api/nodes/usage/range",
            params={"start": start_time, "end": end_time}
        )
        