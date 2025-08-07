import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sys
import os
import uuid
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from api.users import UsersAPI
from api.squads import SquadsAPI


class UserManager:
    """Класс для управления пользователями и форматирования информации о них"""
    
    def __init__(self):
        self.current_users: List[dict] = []
        self.current_squads: List[dict] = []
        self.current_page: int = 0
        self.users_per_page: int = 4
        self.last_message_id: Optional[int] = None
        self.last_chat_id: Optional[int] = None
        self.selected_squad_uuid: Optional[str] = None
        self.selected_user: Optional[dict] = None  # Добавляем сохранение выбранного пользователя
        self.waiting_for_username: bool = False
        self.waiting_for_expire_days: bool = False
        self.waiting_for_traffic_limit: bool = False
        self.waiting_for_description: bool = False
        self.waiting_for_email: bool = False
        self.waiting_for_tag: bool = False
        self.creation_data: Dict = {}
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Форматирует размер в байтах в читаемый формат"""
        if bytes_value == 0:
            return "0 B"
        
        value = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if value < 1024.0:
                return f"{value:.1f} {unit}"
            value /= 1024.0
        return f"{value:.1f} PB"
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Экранирует специальные символы Markdown для безопасного отображения"""
        if not text or not isinstance(text, str):
            return str(text) if text is not None else ""
        
        # Список символов, которые нужно экранировать в MarkdownV2
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def format_user_info(self, user_data: dict) -> str:
        """Форматирует информацию о пользователе для отображения"""
        username = user_data.get('username', 'Unknown')
        uuid_str = user_data.get('uuid', 'N/A')
        short_uuid = user_data.get('shortUuid', 'N/A')
        
        # Статусы
        status = user_data.get('status', '')
        is_active = "✅ Активен" if status == 'ACTIVE' else "❌ Неактивен"
        
        # Проверяем онлайн статус по onlineAt (за последние 10 минут)
        online_at = user_data.get('onlineAt')
        is_online = "🔴 Оффлайн"  # по умолчанию
        if online_at:
            try:
                online_time = datetime.fromisoformat(online_at.replace('Z', '+00:00'))
                now = datetime.now(online_time.tzinfo)
                time_diff = now - online_time
                if time_diff.total_seconds() <= 600:  # 10 минут = 600 секунд
                    is_online = " Онлайн"
            except:
                pass
        
        # Трафик
        used_traffic = self.format_bytes(user_data.get('usedTrafficBytes', 0))
        traffic_limit = user_data.get('trafficLimitBytes', 0)
        traffic_limit_str = self.format_bytes(traffic_limit) if traffic_limit > 0 else "Без лимита"
        
        # Дата истечения
        expire_at = user_data.get('expireAt')
        if expire_at:
            try:
                expire_date = datetime.fromisoformat(expire_at.replace('Z', '+00:00'))
                expire_str = expire_date.strftime('%d.%m.%Y %H:%M')
                now = datetime.now(expire_date.tzinfo)
                if expire_date < now:
                    expire_str += " (истек)"
                else:
                    days_left = (expire_date - now).days
                    expire_str += f" ({days_left} дн.)"
            except:
                expire_str = "Некорректная дата"
        else:
            expire_str = "Без ограничений"
        
        # Дополнительная информация
        description = user_data.get('description', '')
        tag = user_data.get('tag', '')
        email = user_data.get('email', '')
        
        # Сквады
        squads = user_data.get('activeInternalSquads', [])
        squads_str = ", ".join([squad.get('name', 'Unknown') for squad in squads]) if squads else "Нет"
        
        # Экранируем имя пользователя для безопасного использования в Markdown
        escaped_username = self.escape_markdown(username)
        
        info = f"**👤 {escaped_username}**\n\n"
        info += f"🆔 UUID: `{short_uuid}`\n"
        info += f"📊 Статус: {is_active}\n"
        info += f"🌐 Онлайн: {is_online}\n"
        info += f"📈 Трафик: {used_traffic} / {traffic_limit_str}\n"
        info += f"⏰ Истекает: {expire_str}\n"
        info += f"👥 Сквады: {squads_str}\n"
        
        if description:
            escaped_description = self.escape_markdown(description)
            info += f"📝 Описание: {escaped_description}\n"
        if tag:
            escaped_tag = self.escape_markdown(tag)
            info += f"🏷️ Тег: {escaped_tag}\n"
        if email:
            escaped_email = self.escape_markdown(email)
            info += f"📧 Email: {escaped_email}\n"
        
        return info
    
    async def load_users_data(self) -> Tuple[bool, Optional[str]]:
        """Загружает данные о пользователях"""
        try:
            users_api = UsersAPI()
            async with users_api as users_api:
                response = await users_api.get_all_users()
                
                if isinstance(response, dict) and "response" in response:
                    if "users" in response["response"]:
                        self.current_users = response["response"]["users"]
                        return True, None
                    else:
                        return False, "Неверная структура ответа API"
                else:
                    return False, "Ошибка при получении данных пользователей"
                    
        except Exception as e:
            logging.error(f"Ошибка загрузки пользователей: {e}")
            return False, f"Ошибка загрузки: {str(e)}"
    
    async def load_squads_data(self) -> Tuple[bool, Optional[str]]:
        """Загружает данные о сквадах"""
        try:
            logging.info("Начинаем загрузку сквадов...")
            async with SquadsAPI() as squads_api:
                self.current_squads = await squads_api.get_squads_names_and_uuids()
                logging.info(f"Загружено сквадов: {len(self.current_squads)}")
                logging.info(f"Сквады: {self.current_squads}")
                return True, None
                    
        except Exception as e:
            logging.error(f"Ошибка загрузки сквадов: {e}")
            return False, f"Ошибка загрузки сквадов: {str(e)}"
    
    def get_users_summary(self) -> str:
        """Возвращает сводку по пользователям"""
        total_users = len(self.current_users)
        
        # Подсчитываем активных пользователей
        active_users = sum(1 for user in self.current_users if user.get('status') == 'ACTIVE')
        
        # Подсчитываем онлайн пользователей (за последние 10 минут)
        online_users = 0
        for user in self.current_users:
            online_at = user.get('onlineAt')
            if online_at:
                try:
                    online_time = datetime.fromisoformat(online_at.replace('Z', '+00:00'))
                    now = datetime.now(online_time.tzinfo)
                    time_diff = now - online_time
                    if time_diff.total_seconds() <= 600:  # 10 минут
                        online_users += 1
                except:
                    pass
        
        return (f"**📊 Сводка по пользователям**\n\n"
                f"👥 Всего пользователей: {total_users}\n"
                f"✅ Активных: {active_users}\n"
                f"🟢 Онлайн: {online_users}")
    
    def get_users_page_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру с пользователями для текущей страницы"""
        logging.info(f"Создание клавиатуры пользователей для страницы {self.current_page}")
        logging.info(f"Всего пользователей: {len(self.current_users)}")
        
        total_pages = (len(self.current_users) + self.users_per_page - 1) // self.users_per_page
        start_idx = self.current_page * self.users_per_page
        end_idx = min(start_idx + self.users_per_page, len(self.current_users))
        
        # Создаем кнопки для пользователей на текущей странице
        buttons = []
        for i in range(start_idx, end_idx):
            user = self.current_users[i]
            username = user.get('username', 'Unknown')
            
            # Проверяем статус
            status = user.get('status', '')
            status_emoji = "✅" if status == 'ACTIVE' else "❌"
            
            # Проверяем онлайн статус
            online_emoji = "🔴"  # по умолчанию
            online_at = user.get('onlineAt')
            if online_at:
                try:
                    online_time = datetime.fromisoformat(online_at.replace('Z', '+00:00'))
                    now = datetime.now(online_time.tzinfo)
                    time_diff = now - online_time
                    if time_diff.total_seconds() <= 600:  # 10 минут
                        online_emoji = "🟢"
                except:
                    pass
            
            button_text = f"{status_emoji}{online_emoji} {username}"
            # Используем UUID вместо индекса для более надежной идентификации
            user_uuid = user.get('uuid', '')
            callback_data = f"user_select_{user_uuid}"
            
            logging.info(f"Создание кнопки для пользователя: {username} (UUID: {user_uuid})")
            
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )])
        
        # Кнопки навигации
        nav_buttons = []
        if self.current_page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Предыдущая",
                callback_data="users_prev_page"
            ))
        
        if self.current_page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="Следующая ➡️",
                callback_data="users_next_page"
            ))
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Кнопки управления
        management_buttons = [
            [
                InlineKeyboardButton(text="➕ Создать пользователя", callback_data="create_user_menu"),
                InlineKeyboardButton(text="⚡ Быстрое создание", callback_data="quick_create_user")
            ],
            [
                InlineKeyboardButton(text="🔄 Обновить список", callback_data="refresh_users"),
                InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
            ]
        ]
        
        buttons.extend(management_buttons)
        
        # Информация о странице
        if total_pages > 1:
            page_info = f"Страница {self.current_page + 1} из {total_pages}"
            buttons.append([InlineKeyboardButton(
                text=page_info,
                callback_data="page_info"
            )])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def get_user_management_keyboard(self, user_data: dict) -> InlineKeyboardMarkup:
        """Создает клавиатуру для управления конкретным пользователем"""
        status = user_data.get('status', '')
        is_active = status == 'ACTIVE'
        
        buttons = [
            [
                InlineKeyboardButton(
                    text="🔴 Отключить" if is_active else "🟢 Включить",
                    callback_data="toggle_user_status"
                ),
                InlineKeyboardButton(text="🔄 Сбросить трафик", callback_data="reset_user_traffic")
            ],
            [
                InlineKeyboardButton(text="📋 Получить ссылку", callback_data="get_user_link"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data="delete_user")
            ],
            [
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_user_info"),
                InlineKeyboardButton(text="🔙 К списку", callback_data="back_to_users")
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def get_squads_selection_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру для выбора сквада"""
        buttons = []
        
        logging.info(f"Создание клавиатуры сквадов. Количество сквадов: {len(self.current_squads)}")
        
        # Добавляем кнопку "Без сквада"
        buttons.append([InlineKeyboardButton(
            text="❌ Без сквада",
            callback_data="select_squad_none"
        )])
        
        # Добавляем кнопки для каждого сквада
        for squad in self.current_squads:
            squad_name = squad.get('name', 'Unknown')
            squad_uuid = squad.get('uuid', '')
            
            logging.info(f"Добавляем сквад: {squad_name} - {squad_uuid}")
            
            buttons.append([InlineKeyboardButton(
                text=f"👥 {squad_name}",
                callback_data=f"select_squad_{squad_uuid}"
            )])
        
        # Кнопка отмены
        buttons.append([InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_user_creation"
        )])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def get_creation_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру для меню создания пользователя"""
        buttons = [
            [InlineKeyboardButton(text="✏️ Пользовательские данные", callback_data="create_user_custom")],
            [InlineKeyboardButton(text="⚡ Быстрое создание (1 месяц)", callback_data="create_user_quick")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_users")]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def get_custom_creation_keyboard(self) -> InlineKeyboardMarkup:
        """Создает клавиатуру для пользовательского создания"""
        creation_data = self.creation_data
        
        username_status = "✅" if creation_data.get('username') else "❌"
        expire_status = "✅" if creation_data.get('expire_days') else "❌"
        traffic_status = "✅" if creation_data.get('traffic_limit') else "❌"
        
        buttons = [
            [InlineKeyboardButton(text=f"{username_status} Имя пользователя", callback_data="set_username")],
            [InlineKeyboardButton(text=f"{expire_status} Срок действия (дни)", callback_data="set_expire_days")],
            [InlineKeyboardButton(text=f"{traffic_status} Лимит трафика (GB)", callback_data="set_traffic_limit")],
            [InlineKeyboardButton(text="📝 Описание (опционально)", callback_data="set_description")],
            [InlineKeyboardButton(text="📧 Email (опционально)", callback_data="set_email")],
            [InlineKeyboardButton(text="🏷️ Тег (опционально)", callback_data="set_tag")],
        ]
        
        # Показываем кнопку создания только если заполнены обязательные поля
        if creation_data.get('username') and creation_data.get('expire_days') and creation_data.get('traffic_limit') is not None:
            buttons.append([InlineKeyboardButton(text="✅ Создать пользователя", callback_data="proceed_to_squad_selection")])
        
        buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="create_user_menu")])
        
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    async def create_user_quick(self) -> Tuple[bool, str, Optional[dict]]:
        """Быстрое создание пользователя с параметрами по умолчанию"""
        try:
            # Генерируем случайное имя пользователя
            username = f"user_{uuid.uuid4().hex[:8]}"
            
            # Устанавливаем срок действия на 1 месяц
            expire_date = datetime.now() + timedelta(days=30)
            expire_at = expire_date.isoformat() + "Z"
            
            async with UsersAPI() as users_api:
                result = await users_api.prepare_and_create_user(
                    username=username,
                    expire_at=expire_at,
                    squad_uuid=self.selected_squad_uuid,
                    traffic_limit_bytes=0,  # Без лимита
                    description="Быстро созданный пользователь"
                )
                
                if isinstance(result, dict) and "response" in result:
                    user_data = result["response"]
                    # Добавляем созданного пользователя в локальный список
                    self.current_users.append(user_data)
                    logging.info(f"Пользователь {username} создан и добавлен в локальный список. UUID: {user_data.get('uuid')}")
                    logging.info(f"Текущее количество пользователей в списке: {len(self.current_users)}")
                    escaped_username = self.escape_markdown(username)
                    return True, f"✅ Пользователь **{escaped_username}** успешно создан!", user_data
                else:
                    logging.error(f"Неожиданная стр**уктура ответа API: {result}")
                    return False, "❌ Ошибка при создании пользователя", None
                    
        except Exception as e:
            logging.error(f"Ошибка быстрого создания пользователя: {e}")
            return False, f"❌ Ошибка создания: {str(e)}", None
    
    async def create_user_custom(self) -> Tuple[bool, str, Optional[dict]]:
        """Создание пользователя с пользовательскими данными"""
        try:
            creation_data = self.creation_data
            
            # Подготавливаем дату истечения
            expire_days = creation_data.get('expire_days', 30)
            expire_date = datetime.now() + timedelta(days=expire_days)
            expire_at = expire_date.isoformat() + "Z"
            
            # Подготавливаем лимит трафика (конвертируем GB в байты)
            traffic_limit_gb = creation_data.get('traffic_limit', 0)
            traffic_limit_bytes = int(traffic_limit_gb * 1024 * 1024 * 1024) if traffic_limit_gb > 0 else 0
            
            async with UsersAPI() as users_api:
                result = await users_api.prepare_and_create_user(
                    username=creation_data.get('username'),
                    expire_at=expire_at,
                    squad_uuid=self.selected_squad_uuid,
                    traffic_limit_bytes=traffic_limit_bytes,
                    description=creation_data.get('description'),
                    tag=creation_data.get('tag'),
                    email=creation_data.get('email')
                )
                
                if isinstance(result, dict) and "response" in result:
                    user_data = result["response"]
                    username = creation_data.get('username', 'Unknown')
                    # Добавляем созданного пользователя в локальный список
                    self.current_users.append(user_data)
                    logging.info(f"Пользователь {username} создан и добавлен в локальный список. UUID: {user_data.get('uuid')}")
                    logging.info(f"Текущее количество пользователей в списке: {len(self.current_users)}")
                    escaped_username = self.escape_markdown(username)
                    return True, f"✅ Пользователь **{escaped_username}** успешно создан!", user_data
                else:
                    return False, "❌ Ошибка при создании пользователя", None
                    
        except Exception as e:
            logging.error(f"Ошибка создания пользователя: {e}")
            return False, f"❌ Ошибка создания: {str(e)}", None
    
    async def toggle_user_status(self, user_data: dict) -> Tuple[bool, str]:
        """Переключает статус пользователя (включить/отключить)"""
        try:
            user_uuid = user_data.get('uuid')
            status = user_data.get('status', '')
            is_active = status == 'ACTIVE'
            username = user_data.get('username', 'Unknown')
            
            async with UsersAPI() as users_api:
                if is_active:
                    result = await users_api.disable_user(user_uuid)
                    action = "отключен"
                else:
                    result = await users_api.enable_user(user_uuid)
                    action = "включен"
                
                if isinstance(result, dict) and "success" in result and result["success"]:
                    escaped_username = self.escape_markdown(username)
                    return True, f"✅ Пользователь **{escaped_username}** успешно {action}!"
                else:
                    escaped_username = self.escape_markdown(username)
                    return False, f"❌ Ошибка при изменении статуса пользователя **{escaped_username}**"
                    
        except Exception as e:
            logging.error(f"Ошибка изменения статуса пользователя: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def reset_user_traffic(self, user_data: dict) -> Tuple[bool, str]:
        """Сбрасывает трафик пользователя"""
        try:
            user_uuid = user_data.get('uuid')
            username = user_data.get('username', 'Unknown')
            
            async with UsersAPI() as users_api:
                result = await users_api.reset_user_traffic(user_uuid)
                
                if isinstance(result, dict) and "success" in result and result["success"]:
                    escaped_username = self.escape_markdown(username)
                    return True, f"✅ Трафик пользователя **{escaped_username}** успешно сброшен!"
                else:
                    escaped_username = self.escape_markdown(username)
                    return False, f"❌ Ошибка при сбросе трафика пользователя **{escaped_username}**"
                    
        except Exception as e:
            logging.error(f"Ошибка сброса трафика: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def delete_user(self, user_data: dict) -> Tuple[bool, str]:
        """Удаляет пользователя"""
        try:
            user_uuid = user_data.get('uuid')
            username = user_data.get('username', 'Unknown')
            
            async with UsersAPI() as users_api:
                result = await users_api.delete_user(user_uuid)
                
                if isinstance(result, dict) and "success" in result and result["success"]:
                    # Удаляем пользователя из локального списка
                    self.current_users = [u for u in self.current_users if u.get('uuid') != user_uuid]
                    escaped_username = self.escape_markdown(username)
                    return True, f"✅ Пользователь **{escaped_username}** успешно удален!"
                else:
                    escaped_username = self.escape_markdown(username)
                    return False, f"❌ Ошибка при удалении пользователя **{escaped_username}**"
                    
        except Exception as e:
            logging.error(f"Ошибка удаления пользователя: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    async def get_user_subscription_link(self, user_data: dict) -> Tuple[bool, str]:
        """Получает ссылку на подписку пользователя"""
        try:
            async with UsersAPI() as users_api:
                subscription_link = await users_api.get_sublink({"response": user_data})
                
                if subscription_link:
                    username = user_data.get('username', 'Unknown')
                    escaped_username = self.escape_markdown(username)
                    return True, f"🔗 **Ссылка для {escaped_username}:**\n\n`{subscription_link}`"
                else:
                    return False, "❌ Не удалось получить ссылку на подписку"
                    
        except Exception as e:
            logging.error(f"Ошибка получения ссылки: {e}")
            return False, f"❌ Ошибка: {str(e)}"
    
    def get_user_by_index(self, index: int) -> Optional[dict]:
        """Получает пользователя по индексу"""
        if 0 <= index < len(self.current_users):
            return self.current_users[index]
        return None
    
    async def get_user_by_uuid(self, user_uuid: str) -> Optional[dict]:
        """Получает пользователя по UUID, сначала из локального списка, затем из API"""
        logging.info(f"Поиск пользователя с UUID: {user_uuid}")
        logging.info(f"Количество пользователей в локальном списке: {len(self.current_users)}")
        
        # Сначала ищем в локальном списке
        for user in self.current_users:
            if user.get('uuid') == user_uuid:
                logging.info(f"Пользователь найден в локальном списке: {user.get('username', 'Unknown')}")
                return user
        
        logging.info("Пользователь не найден в локальном списке, запрашиваем из API")
        
        # Если не найден локально, запрашиваем из API
        try:
            async with UsersAPI() as users_api:
                result = await users_api.get_user_by_uuid(user_uuid)
                logging.info(f"Результат запроса к API: {result}")
                
                if isinstance(result, dict) and "response" in result:
                    user_data = result["response"]
                    logging.info(f"Пользователь найден в API: {user_data.get('username', 'Unknown')}")
                    # Добавляем пользователя в локальный список для кэширования
                    self.current_users.append(user_data)
                    logging.info(f"Пользователь добавлен в локальный список. Новое количество: {len(self.current_users)}")
                    return user_data
        except Exception as e:
            logging.error(f"Ошибка получения пользователя по UUID {user_uuid}: {e}")
        
        logging.warning(f"Пользователь с UUID {user_uuid} не найден ни локально, ни в API")
        return None
    
    def set_selected_user(self, user_data: dict):
        """Устанавливает выбранного пользователя"""
        self.selected_user = user_data
    
    def get_selected_user(self) -> Optional[dict]:
        """Получает выбранного пользователя"""
        return self.selected_user
    
    def clear_selected_user(self):
        """Очищает выбранного пользователя"""
        self.selected_user = None
    
    def next_page(self) -> bool:
        """Переходит на следующую страницу"""
        total_pages = (len(self.current_users) + self.users_per_page - 1) // self.users_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            return True
        return False
    
    def prev_page(self) -> bool:
        """Переходит на предыдущую страницу"""
        if self.current_page > 0:
            self.current_page -= 1
            return True
        return False
    
    def reset_page(self):
        """Сбрасывает текущую страницу на первую"""
        self.current_page = 0
    
    def clear_creation_data(self):
        """Очищает данные создания пользователя"""
        self.creation_data = {}
        self.selected_squad_uuid = None
        self.waiting_for_username = False
        self.waiting_for_expire_days = False
        self.waiting_for_traffic_limit = False
        self.waiting_for_description = False
        self.waiting_for_email = False
        self.waiting_for_tag = False
    
    def set_last_message(self, message_id: int, chat_id: int):
        """Сохраняет ID последнего сообщения"""
        self.last_message_id = message_id
        self.last_chat_id = chat_id
    
    def get_last_message_info(self) -> Tuple[Optional[int], Optional[int]]:
        """Возвращает информацию о последнем сообщении"""
        return self.last_message_id, self.last_chat_id
    
    def clear_last_message(self):
        """Очищает информацию о последнем сообщении"""
        self.last_message_id = None
        self.last_chat_id = None
