import asyncio
import sys
import os
from typing import Optional, Dict, Any, List
from aiogram import types

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from handlers.api.system_stats import SystemStatsAPI
from handlers.api.bandwidth import BandwidthAPI


class SystemStatsManager:
    """Менеджер для работы со статистикой системы"""

    def __init__(self):
        self.system_stats_api = SystemStatsAPI()
        self.bandwidth_api = BandwidthAPI()
        self.current_category = None
        self.last_message_id = None
        self.last_chat_id = None
        self.system_data = {}
        self.bandwidth_data = {}
        self.health_data = {}
        self.nodes_metrics_data = {}
        self.real_time_data = {}

    def set_last_message(self, message_id: int, chat_id: int):
        """Сохраняет ID последнего сообщения для обновления"""
        self.last_message_id = message_id
        self.last_chat_id = chat_id

    def get_last_message(self) -> tuple:
        """Возвращает ID последнего сообщения и чата"""
        return self.last_message_id, self.last_chat_id

    def set_current_category(self, category: str):
        """Устанавливает текущую категорию статистики"""
        self.current_category = category

    def get_current_category(self) -> Optional[str]:
        """Возвращает текущую категорию статистики"""
        return self.current_category

    async def load_all_stats_data(self) -> tuple[bool, Optional[str]]:
        """Загружает все данные статистики"""
        try:
            async with self.system_stats_api as api:
                # Загружаем основные системные статистики
                system_response = await api.get_system_stats()
                self.system_data = system_response

                # Загружаем статистику полосы пропускания
                bandwidth_response = await api.get_bandwidth_stats()
                self.bandwidth_data = bandwidth_response

                # Загружаем состояние системы
                health_response = await api.get_system_health()
                self.health_data = health_response

                # Загружаем метрики нод
                nodes_metrics_response = await api.get_nodes_metrics()
                self.nodes_metrics_data = nodes_metrics_response

            # Загружаем данные в реальном времени
            async with self.bandwidth_api as bandwidth:
                real_time_response = await bandwidth.get_nodes_rt_usage()
                self.real_time_data = real_time_response

            return True, None

        except Exception as e:
            return False, f"Ошибка при загрузке статистики: {str(e)}"

    def get_main_stats_keyboard(self) -> types.InlineKeyboardMarkup:
        """Создает клавиатуру с категориями статистики"""
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="📊 Общая статистика системы",
                    callback_data="stats_system"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="📡 Статистика трафика",
                    callback_data="stats_bandwidth"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🌐 Статистика нод",
                    callback_data="stats_nodes"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="⚡ Статистика нод в реальном времени",
                    callback_data="stats_realtime"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🔧 Процессы",
                    callback_data="stats_health"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🔄 Обновить все",
                    callback_data="stats_refresh_all"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🔙 Назад в главное меню",
                    callback_data="back_to_main"
                )
            ]
        ])
        return keyboard

    def get_category_keyboard(self, category: str) -> types.InlineKeyboardMarkup:
        """Создает клавиатуру для конкретной категории"""
        keyboard_buttons = []

        if category == "stats_system":
            keyboard_buttons = [
                [types.InlineKeyboardButton(text="👥 Пользователи", callback_data="system_users")],
                [types.InlineKeyboardButton(text="💾 Память", callback_data="system_memory")]
            ]
        elif category == "stats_bandwidth":
            # Убираем кнопки для отдельных периодов, так как они уже выводятся в общей статистике
            keyboard_buttons = []
        elif category == "stats_nodes":
            keyboard_buttons = [
                [types.InlineKeyboardButton(text="📊 Общая информация", callback_data="nodes_general")],
                [types.InlineKeyboardButton(text="📈 Детальная статистика", callback_data="nodes_detailed")]
            ]

        # Общие кнопки для всех категорий
        keyboard_buttons.extend([
            [types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_{category}")],
            [types.InlineKeyboardButton(text="🔙 К категориям", callback_data="stats_back_to_categories")]
        ])

        return types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    def format_system_stats(self) -> str:
        """Форматирует общую системную статистику"""
        if not self.system_data or 'response' not in self.system_data:
            return "❌ Данные системной статистики недоступны"

        data = self.system_data['response']
        
        # Информация о памяти  
        memory_info = data.get('memory', {})
        total_mb = memory_info.get('total', 0) / 1024 / 1024
        used_mb = memory_info.get('used', 0) / 1024 / 1024
        free_mb = memory_info.get('free', 0) / 1024 / 1024
        
        memory_text = f"💾 **Память:**\n"
        memory_text += f"├ Всего: {total_mb:.1f} MB\n"
        memory_text += f"├ Используется: {used_mb:.1f} MB\n"
        memory_text += f"└ Свободно: {free_mb:.1f} MB\n\n"

        # Информация о пользователях
        users_info = data.get('users', {})
        status_counts = users_info.get('statusCounts', {})
        
        users_text = f"👥 **Пользователи:**\n"
        users_text += f"├ Всего: {users_info.get('totalUsers', 0)}\n"
        users_text += f"├ Активных: {status_counts.get('ACTIVE', 0)}\n"
        users_text += f"├ Отключенных: {status_counts.get('DISABLED', 0)}\n"
        users_text += f"├ Ограниченных: {status_counts.get('LIMITED', 0)}\n"
        users_text += f"└ Истекших: {status_counts.get('EXPIRED', 0)}\n\n"

        # Онлайн статистика
        online_info = data.get('onlineStats', {})
        online_text = f"📈 **Онлайн:**\n"
        online_text += f"├ Сейчас: {online_info.get('onlineNow', 0)}\n"
        online_text += f"├ За день: {online_info.get('lastDay', 0)}\n"
        online_text += f"├ За неделю: {online_info.get('lastWeek', 0)}\n"
        online_text += f"└ Никогда не были: {online_info.get('neverOnline', 0)}\n\n"

        # Время работы
        uptime_seconds = data.get('uptime', 0)
        uptime_days = uptime_seconds // 86400
        uptime_hours = (uptime_seconds % 86400) // 3600
        uptime_text = f"⏱ **Время работы:** {int(uptime_days)} дней, {int(uptime_hours)} часов\n"

        return f"📊 **Системная статистика**\n\n{memory_text}{users_text}{online_text}{uptime_text}"

    def format_bandwidth_stats(self) -> str:
        """Форматирует статистику полосы пропускания"""
        if not self.bandwidth_data or 'response' not in self.bandwidth_data:
            return "❌ Данные полосы пропускания недоступны"

        data = self.bandwidth_data['response']

        text = "📡 **Статистика трафика**\n\n"

        # За 2 дня
        two_days = data.get('bandwidthLastTwoDays', {})
        text += f"📅 **За последние 2 дня:**\n"
        text += f"├ Текущий: {two_days.get('current', 'N/A')}\n"
        text += f"├ Предыдущий: {two_days.get('previous', 'N/A')}\n"
        text += f"└ Разница: {two_days.get('difference', 'N/A')}\n\n"

        # За неделю
        week = data.get('bandwidthLastSevenDays', {})
        text += f"📅 **За последние 7 дней:**\n"
        text += f"├ Текущий: {week.get('current', 'N/A')}\n"
        text += f"├ Предыдущий: {week.get('previous', 'N/A')}\n"
        text += f"└ Разница: {week.get('difference', 'N/A')}\n\n"

        # За месяц
        month = data.get('bandwidthLast30Days', {})
        text += f"📅 **За последние 30 дней:**\n"
        text += f"├ Текущий: {month.get('current', 'N/A')}\n"
        text += f"├ Предыдущий: {month.get('previous', 'N/A')}\n"
        text += f"└ Разница: {month.get('difference', 'N/A')}\n\n"

        # За календарный месяц
        cal_month = data.get('bandwidthCalendarMonth', {})
        text += f"📅 **За календарный месяц:**\n"
        text += f"├ Текущий: {cal_month.get('current', 'N/A')}\n"
        text += f"├ Предыдущий: {cal_month.get('previous', 'N/A')}\n"
        text += f"└ Разница: {cal_month.get('difference', 'N/A')}\n\n"

        # За год
        year = data.get('bandwidthCurrentYear', {})
        text += f"📅 **За текущий год:**\n"
        text += f"├ Текущий: {year.get('current', 'N/A')}\n"
        text += f"├ Предыдущий: {year.get('previous', 'N/A')}\n"
        text += f"└ Разница: {year.get('difference', 'N/A')}\n"

        return text

    def format_nodes_stats(self) -> str:
        """Форматирует статистику нод"""
        if not self.nodes_metrics_data or 'response' not in self.nodes_metrics_data:
            return "❌ Данные нод недоступны"

        data = self.nodes_metrics_data['response']
        nodes = data.get('nodes', [])

        if not nodes:
            return "📍 Ноды не найдены"

        text = "🌐 **Статистика нод**\n\n"

        for i, node in enumerate(nodes[:5]):  # Показываем только первые 5 нод
            text += f"{node.get('countryEmoji', '🌍')} **{node.get('nodeName', 'Неизвестная нода')}**\n"
            text += f"├ UUID: `{node.get('nodeUuid', 'N/A')[:8]}...`\n"
            text += f"├ Провайдер: {node.get('providerName', 'N/A')}\n"
            text += f"└ Пользователей онлайн: {node.get('usersOnline', 0)}\n"

            # Inbound статистика
            inbounds = node.get('inboundsStats', [])
            if inbounds:
                text += f"  📥 **Входящий трафик:**\n"
                for inbound in inbounds[:2]:  # Первые 2
                    text += f"  ├ {inbound.get('tag', 'N/A')}: ↓{inbound.get('download', '0')} ↑{inbound.get('upload', '0')}\n"

            text += "\n"

        if len(nodes) > 5:
            text += f"... и еще {len(nodes) - 5} нод\n"

        return text

    def format_realtime_stats(self) -> str:
        """Форматирует статистику в реальном времени"""
        if not self.real_time_data or 'response' not in self.real_time_data:
            return "❌ Данные в реальном времени недоступны"

        nodes = self.real_time_data['response']

        if not nodes:
            return "⚡ Нет данных в реальном времени"

        text = "⚡ **Статистика нод в реальном времени**\n\n"

        for node in nodes:
            flag = "🇸🇪" if node.get('countryCode') == "SE" else \
                   "🇷🇺" if node.get('countryCode') == "RU" else \
                   "🇩🇪" if node.get('countryCode') == "DE" else "🌍"
            
            text += f"{flag} **{node.get('nodeName', 'Неизвестный узел')}**\n"
            text += f"├ Скачано: {self._format_bytes(node.get('downloadBytes', 0))}\n"
            text += f"├ Загружено: {self._format_bytes(node.get('uploadBytes', 0))}\n"
            text += f"├ Всего: {self._format_bytes(node.get('totalBytes', 0))}\n"
            text += f"├ Скорость ↓: {node.get('downloadSpeedBps', 0)} Bps\n"
            text += f"└ Скорость ↑: {node.get('uploadSpeedBps', 0)} Bps\n\n"

        return text

    def format_health_stats(self) -> str:
        """Форматирует статистику состояния системы"""
        if not self.health_data or 'response' not in self.health_data:
            return "❌ Данные состояния системы недоступны"

        data = self.health_data['response']
        pm2_stats = data.get('pm2Stats', [])

        if not pm2_stats:
            return "🔧 Нет данных о состоянии PM2 процессов"

        text = "🔧 **Процессы системы (PM2)**\n\n"

        for process in pm2_stats:
            text += f"⚙️ **{process.get('name', 'Неизвестный процесс')}**\n"
            text += f"├ Память: {process.get('memory', 'N/A')}\n"
            text += f"└ CPU: {process.get('cpu', 'N/A')}%\n\n"

        return text

    def _format_bytes(self, bytes_value: int) -> str:
        """Форматирует байты в читаемый вид"""
        if bytes_value >= 1024**3:
            return f"{bytes_value / (1024**3):.2f} GB"
        elif bytes_value >= 1024**2:
            return f"{bytes_value / (1024**2):.2f} MB"
        elif bytes_value >= 1024:
            return f"{bytes_value / 1024:.2f} KB"
        else:
            return f"{bytes_value} B"

    def get_stats_summary(self) -> str:
        """Возвращает краткую сводку всей статистики"""
        summary = "📊 **Сводка статистики**\n\n"

        # Основные показатели из системной статистики
        if self.system_data and 'response' in self.system_data:
            data = self.system_data['response']
            users_info = data.get('users', {})
            online_info = data.get('onlineStats', {})
            nodes_info = data.get('nodes', {})
            
            summary += f"👥 Пользователей: {users_info.get('totalUsers', 0)}\n"
            summary += f"🟢 Онлайн сейчас: {online_info.get('onlineNow', 0)}\n"
            
            # Память
            memory_info = data.get('memory', {})
            used_gb = memory_info.get('used', 0) / (1024**3)
            total_gb = memory_info.get('total', 0) / (1024**3)
            summary += f"💾 Память: {used_gb:.1f}/{total_gb:.1f} GB\n"

        # Трафик из статистики полосы пропускания
        if self.bandwidth_data and 'response' in self.bandwidth_data:
            data = self.bandwidth_data['response']
            month_data = data.get('bandwidthLast30Days', {})
            summary += f"📡 Трафик за месяц: {month_data.get('current', 'N/A')}\n"

        summary += "\nВыберите категорию для подробной информации:"
        return summary
