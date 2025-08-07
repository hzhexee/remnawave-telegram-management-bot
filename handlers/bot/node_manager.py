import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from api.nodes import NodesAPI


class NodeManager:
    """Класс для управления нодами и форматирования информации о них"""
    
    def __init__(self):
        self.current_nodes: List[str] = []
        self.current_nodes_data: Dict[str, dict] = {}
        self.current_selected_node: Optional[str] = None
        self.last_message_id: Optional[int] = None
        self.last_chat_id: Optional[int] = None
    
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
    
    def format_node_info(self, node_data: dict) -> str:
        """Форматирует информацию о ноде для отображения"""
        name = node_data.get('name', 'Unknown')
        address = node_data.get('address', 'N/A')
        port = node_data.get('port', 'N/A')
        
        # Статусы
        is_connected = "✅ Подключена" if node_data.get('isConnected') else "❌ Отключена"
        is_online = "🟢 Онлайн" if node_data.get('isNodeOnline') else "🔴 Оффлайн"
        is_xray_running = "✅ Запущен" if node_data.get('isXrayRunning') else "❌ Остановлен"
        is_disabled = "🚫 Отключена" if node_data.get('isDisabled') else "✅ Активна"
        
        # Дополнительная информация
        users_online = node_data.get('usersOnline', 0)
        xray_version = node_data.get('xrayVersion', 'N/A')
        node_version = node_data.get('nodeVersion', 'N/A')
        country_code = node_data.get('countryCode', 'N/A')
        
        # Трафик
        traffic_used = node_data.get('trafficUsedBytes', 0)
        traffic_limit = node_data.get('trafficLimitBytes', 0)
        
        traffic_used_str = self.format_bytes(traffic_used)
        traffic_limit_str = self.format_bytes(traffic_limit) if traffic_limit > 0 else "Безлимит"
        
        info_text = f"""
🔧 **Информация о ноде: {name}**

🌐 **Подключение:**
• Адрес: `{address}:{port}`
• Страна: {country_code}
• Статус подключения: {is_connected}
• Статус ноды: {is_online}
• Состояние: {is_disabled}

⚙️ **Сервисы:**
• Xray: {is_xray_running}
• Версия Xray: {xray_version}
• Версия ноды: {node_version}

👥 **Пользователи:**
• Онлайн: {users_online}

📊 **Трафик:**
• Использовано: {traffic_used_str}
• Лимит: {traffic_limit_str}
"""
        return info_text
    
    def get_node_management_keyboard(self, node_data: dict) -> types.ReplyKeyboardMarkup:
        """Создает клавиатуру для управления нодой"""
        kb = []
        
        # Кнопки включения/отключения
        if node_data.get('isDisabled'):
            kb.append([types.KeyboardButton(text="🟢 Включить ноду")])
        else:
            kb.append([types.KeyboardButton(text="🔴 Отключить ноду")])
        
        # Кнопка перезагрузки
        kb.append([types.KeyboardButton(text="🔄 Перезагрузить ноду")])
        
        # Кнопка обновления информации
        kb.append([types.KeyboardButton(text="🔍 Обновить информацию")])
        
        # Кнопка назад
        kb.append([types.KeyboardButton(text="🔙 Назад к списку нод")])
        
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
        return keyboard
    
    def get_node_management_inline_keyboard(self, node_data: dict) -> InlineKeyboardMarkup:
        """Создает инлайн-клавиатуру для управления нодой (для редактирования сообщений)"""
        kb = []
        
        # Кнопки включения/отключения
        if node_data.get('isDisabled'):
            kb.append([InlineKeyboardButton(text="🟢 Включить ноду", callback_data="enable_node")])
        else:
            kb.append([InlineKeyboardButton(text="🔴 Отключить ноду", callback_data="disable_node")])
        
        # Кнопка перезагрузки
        kb.append([InlineKeyboardButton(text="🔄 Перезагрузить ноду", callback_data="restart_node")])
        
        # Кнопка обновления информации
        kb.append([InlineKeyboardButton(text="🔍 Обновить информацию", callback_data="refresh_info")])
        
        # Кнопка назад
        kb.append([InlineKeyboardButton(text="🔙 Назад к списку нод", callback_data="back_to_nodes")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
        return keyboard
    
    def get_nodes_list_keyboard(self) -> types.ReplyKeyboardMarkup:
        """Создает клавиатуру со списком нод"""
        kb = []
        nodes = self.current_nodes
        
        # Располагаем ноды по 2 в ряд
        for i in range(0, len(nodes), 2):
            row = []
            row.append(types.KeyboardButton(text=nodes[i]))
            if i + 1 < len(nodes):
                row.append(types.KeyboardButton(text=nodes[i + 1]))
            kb.append(row)
        
        # Добавляем кнопку перезагрузки всех нод
        kb.append([types.KeyboardButton(text="🔄 Перезагрузить все ноды")])
        
        # Добавляем кнопку "Назад"
        kb.append([types.KeyboardButton(text="🔙 Назад")])
        
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите ноду для управления"
        )
        return keyboard
    
    def get_restart_all_confirmation_keyboard(self) -> types.InlineKeyboardMarkup:
        """Создает инлайн-клавиатуру для подтверждения перезагрузки всех нод"""
        kb = [
            [
                types.InlineKeyboardButton(text="❌ Нет", callback_data="cancel_restart_all"),
                types.InlineKeyboardButton(text="✅ Да", callback_data="confirm_restart_all")
            ]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        return keyboard
    
    async def load_nodes_data(self) -> Tuple[bool, str]:
        """
        Загружает данные о нодах из API
        
        Returns:
            Tuple[bool, str]: (успех, сообщение об ошибке или пустая строка)
        """
        try:
            async with NodesAPI() as nodes_api:
                nodes_data = await nodes_api.get_all_nodes()
            
            if not nodes_data:
                return False, "Ноды не найдены."
            
            # Извлекаем список нод из ключа 'response'
            nodes_list = nodes_data.get('response', [])
            
            if not nodes_list:
                return False, "Ноды не найдены."
            
            # Извлекаем имена нод из ответа API
            self.current_nodes = [
                node.get("name", f"Node-{node.get('uuid', 'Unknown')}")
                for node in nodes_list
            ]
            
            # Сохраняем полные данные нод с ключом по имени
            self.current_nodes_data = {
                node.get("name", f"Node-{node.get('uuid', 'Unknown')}"): node
                for node in nodes_list
            }
            
            return True, ""
            
        except Exception as e:
            logging.error(f"Ошибка при получении списка нод: {e}")
            return False, f"Произошла ошибка при получении списка нод: {str(e)}"
    
    def get_node_data(self, node_name: str) -> Optional[dict]:
        """Получает данные о конкретной ноде"""
        return self.current_nodes_data.get(node_name)
    
    def set_selected_node(self, node_name: str) -> None:
        """Устанавливает текущую выбранную ноду"""
        self.current_selected_node = node_name
    
    def clear_selected_node(self) -> None:
        """Очищает текущую выбранную ноду"""
        self.current_selected_node = None
    
    def get_selected_node(self) -> Optional[str]:
        """Получает имя текущей выбранной ноды"""
        return self.current_selected_node
    
    def set_last_message(self, message_id: int, chat_id: int) -> None:
        """Сохраняет ID последнего сообщения для обновления"""
        self.last_message_id = message_id
        self.last_chat_id = chat_id
    
    def get_last_message_info(self) -> Tuple[Optional[int], Optional[int]]:
        """Получает информацию о последнем сообщении"""
        return self.last_message_id, self.last_chat_id
    
    def clear_last_message(self) -> None:
        """Очищает информацию о последнем сообщении"""
        self.last_message_id = None
        self.last_chat_id = None
    
    def is_node_in_list(self, node_name: str) -> bool:
        """Проверяет, есть ли нода в списке"""
        return node_name in self.current_nodes
    
    async def enable_node(self, node_name: str) -> Tuple[bool, str]:
        """
        Включает ноду
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        node_data = self.get_node_data(node_name)
        if not node_data:
            return False, "Данные о ноде не найдены."
        
        try:
            node_uuid = node_data.get('uuid')
            async with NodesAPI() as nodes_api:
                await nodes_api.enable_node(node_uuid)
            
            return True, f"✅ Нода {node_name} была включена!"
            
        except Exception as e:
            logging.error(f"Ошибка при включении ноды: {e}")
            return False, f"❌ Произошла ошибка при включении ноды: {str(e)}"
    
    async def disable_node(self, node_name: str) -> Tuple[bool, str]:
        """
        Отключает ноду
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        node_data = self.get_node_data(node_name)
        if not node_data:
            return False, "Данные о ноде не найдены."
        
        try:
            node_uuid = node_data.get('uuid')
            async with NodesAPI() as nodes_api:
                await nodes_api.disable_node(node_uuid)
            
            return True, f"🔴 Нода {node_name} была отключена!"
            
        except Exception as e:
            logging.error(f"Ошибка при отключении ноды: {e}")
            return False, f"❌ Произошла ошибка при отключении ноды: {str(e)}"
    
    async def restart_node(self, node_name: str) -> Tuple[bool, str]:
        """
        Перезагружает ноду
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        node_data = self.get_node_data(node_name)
        if not node_data:
            return False, "Данные о ноде не найдены."
        
        try:
            node_uuid = node_data.get('uuid')
            async with NodesAPI() as nodes_api:
                await nodes_api.restart_node(node_uuid)
            
            return True, f"🔄 Нода {node_name} перезагружается..."
            
        except Exception as e:
            logging.error(f"Ошибка при перезагрузке ноды: {e}")
            return False, f"❌ Произошла ошибка при перезагрузке ноды: {str(e)}"
    
    async def restart_all_nodes(self) -> Tuple[bool, str]:
        """
        Перезагружает все ноды
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        if not self.current_nodes:
            return False, "Список нод не загружен."
        
        try:
            async with NodesAPI() as nodes_api:
                await nodes_api.restart_all_nodes()
            
            nodes_count = len(self.current_nodes)
            return True, f"🔄 Запущена перезагрузка всех нод ({nodes_count} нод(ы))..."
            
        except Exception as e:
            logging.error(f"Ошибка при перезагрузке всех нод: {e}")
            return False, f"❌ Произошла ошибка при перезагрузке всех нод: {str(e)}"
    
    def get_nodes_summary(self) -> str:
        """Возвращает краткую сводку по нодам"""
        if not self.current_nodes:
            return "Ноды не загружены."
        
        return "Доступные ноды:\n" + "\n".join([f"• {node}" for node in self.current_nodes])
