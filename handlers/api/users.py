import json
import httpx
import os
import uuid

class UsersAPI:
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
        import logging
        client = await self._get_client()
        created_new = client != self._client
        
        try:
            response = await getattr(client, method)(
                url, 
                headers=self._get_headers(),
                **kwargs
            )
            
            # Логируем статус ответа
            logging.info(f"HTTP {method.upper()} {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                # Логируем ошибку
                try:
                    error_data = response.json()
                    logging.error(f"API Error {response.status_code}: {error_data}")
                except:
                    logging.error(f"API Error {response.status_code}: {response.text}")
            
            return response.json()
        finally:
            if created_new:
                await client.aclose()
    
    async def create_new_user(self, user_data):
        """
        Создает нового пользователя с заданными данными.
        
        Args:
            user_data (dict): Данные пользователя для создания.
            
        Returns:
            dict: Ответ API с информацией о созданном пользователе.
        """
        import logging
        logging.info(f"Отправляем данные для создания пользователя: {user_data}")
        
        return await self._make_request(
            "post",
            f"{self.base_url}/api/users",
            json=user_data
        )
    
    async def prepare_and_create_user(
        self,
        username=None,
        expire_at=None,
        squad_uuid=None,
        traffic_limit_bytes=0,
        traffic_limit_strategy="NO_RESET",
        description=None,
        tag=None,
        email=None
    ):
        """
        Подготавливает данные пользователя и создает нового пользователя.
        
        Args:
            username (str, optional): Имя пользователя. Если не указано, генерируется случайное.
            expire_at (str, optional): Дата истечения в ISO формате (например "2025-08-01T02:53:55.802Z").
            squad_uuid (str, optional): UUID сквада для добавления пользователя.
            traffic_limit_bytes (int, optional): Лимит трафика в байтах. По умолчанию 0.
            traffic_limit_strategy (str, optional): Стратегия сброса лимита трафика. По умолчанию "NO_RESET".
            description (str, optional): Описание пользователя.
            tag (str, optional): Тег пользователя.
            email (str, optional): Email пользователя.
            
        Returns:
            dict: Ответ API с информацией о созданном пользователе.
        """
        # Генерируем случайное имя пользователя, если не указано
        if not username:
            username = f"user_{uuid.uuid4().hex[:8]}"
        
        # Если expire_at не указан, устанавливаем на 1 месяц вперед по умолчанию
        if not expire_at:
            from datetime import datetime, timedelta
            expire_date = datetime.now() + timedelta(days=30)
            expire_at = expire_date.isoformat() + "Z"
        
        # Подготавливаем данные пользователя
        user_data = {
            "username": username,
            "trafficLimitBytes": traffic_limit_bytes,
            "trafficLimitStrategy": traffic_limit_strategy,
            "expireAt": expire_at  # Обязательное поле согласно документации
        }
        
        # Добавляем опциональные поля, если они указаны
        if squad_uuid:
            user_data["activeInternalSquads"] = [squad_uuid]  # Массив строк UUID, а не объектов
        
        if description:
            user_data["description"] = description
        
        if tag:
            user_data["tag"] = tag
        
        if email:
            user_data["email"] = email
        
        # Вызываем существующую функцию для создания пользователя
        return await self.create_new_user(user_data)
    
    async def get_all_users(self):
        """
        Получает список всех пользователей.
        
        Returns:
            list: Список пользователей.
        """
        return await self._make_request(
            "get",
            f"{self.base_url}/api/users"
        )
    
    async def delete_user(self, user_uuid):
        """
        Удаляет пользователя по UUID.
        
        Args:
            user_uuid (str): UUID пользователя для удаления.
            
        Returns:
            dict: Ответ API с информацией об удалении.
        """
        return await self._make_request(
            "delete",
            f"{self.base_url}/api/users/{user_uuid}"
        )
    
    async def get_user_by_uuid(self, user_uuid):
        """
        Получает информацию о пользователе по UUID.
        
        Args:
            user_uuid (str): UUID пользователя.
            
        Returns:
            dict: Информация о пользователе.
        """
        return await self._make_request(
            "get",
            f"{self.base_url}/api/users/{user_uuid}"
        )
    
    async def get_sublink(self, user_info):
        """
        Получает ссылку подписки пользователя из информации о пользователе.
        
        Args:
            user_info (dict): Информация о пользователе, включая данные о подписке.
            
        Returns:
            str: Ссылка на подписку пользователя или None, если ссылка не найдена.
        """
        if not user_info or "response" not in user_info:
            return None
        
        user_data = user_info["response"]
        subscription_link = user_data.get("subscriptionUrl")
        
        return subscription_link
    
    async def enable_user(self, user_uuid):
        """
        Включает пользователя по UUID.
        
        Args:
            user_uuid (str): UUID пользователя для включения.
            
        Returns:
            dict: Ответ API с информацией о включении пользователя.
        """
        return await self._make_request(
            "post",
            f"{self.base_url}/api/users/{user_uuid}/actions/enable"
        )
    
    async def disable_user(self, user_uuid):
        """
        Отключает пользователя по UUID.
        
        Args:
            user_uuid (str): UUID пользователя для отключения.
            
        Returns:
            dict: Ответ API с информацией об отключении пользователя.
        """
        return await self._make_request(
            "post",
            f"{self.base_url}/api/users/{user_uuid}/actions/disable"
        )
    
    async def reset_user_traffic(self, user_uuid):
        """
        Сбрасывает трафик пользователя по UUID.
        
        Args:
            user_uuid (str): UUID пользователя для сброса трафика.
            
        Returns:
            dict: Ответ API с информацией о сбросе трафика.
        """
        return await self._make_request(
            "post",
            f"{self.base_url}/api/users/{user_uuid}/actions/reset-traffic"
        )
        
    async def get_subscription_info_by_suuid(self, short_uuid):
        """
        Получает информацию о подписке.

        Returns:
            dict: Ответ API с информацией о подписке.
        """
        return await self._make_request(
            "get",
            f"{self.base_url}/api/sub/{short_uuid}/info"
        )