import json
import httpx
import os

class SquadsAPI:
    def __init__(self, token=None, base_url=None, cookies=None):
        self.token = token or os.getenv("API_TOKEN", "")
        self.base_url = base_url or os.getenv("REMNAWAVE_BASE_URL", "")
        self.cookies = cookies or json.loads(os.getenv("COOKIES", "{}"))
        self._client = None
    
    def _get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.token
        }
    
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
    
    async def get_internal_squads(self):
        """
        Получает список внутренних сквадов.
        
        Returns:
            dict: Ответ API с информацией о сквадах.
        """
        return await self._make_request(
            "get",
            f"{self.base_url}/api/internal-squads"
        )
    
    async def get_squads_names_and_uuids(self):
        """
        Получает список сквадов, содержащий только их имена и UUID.
        
        Returns:
            list: Список словарей с ключами 'name' и 'uuid' для каждого сквада.
        """
        import logging
        
        logging.info("Запрашиваем внутренние сквады...")
        response_data = await self.get_internal_squads()
        logging.info(f"Получен ответ от API: {response_data}")
        
        # Проверяем структуру ответа и извлекаем сквады
        if isinstance(response_data, dict) and "response" in response_data:
            if "internalSquads" in response_data["response"]:
                squads = response_data["response"]["internalSquads"]
                logging.info(f"Найдено сквадов в ответе: {len(squads)}")
                result = [{'name': squad['name'], 'uuid': squad['uuid']} for squad in squads]
                logging.info(f"Обработанный список сквадов: {result}")
                return result
            else:
                logging.warning("Ключ 'internalSquads' не найден в ответе")
        else:
            logging.warning(f"Неожиданная структура ответа: {response_data}")
        
        logging.warning("Возвращаем пустой список сквадов")
        return []