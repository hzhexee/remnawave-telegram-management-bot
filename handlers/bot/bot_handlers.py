import asyncio
import logging
from typing import Optional
from aiogram import Bot, types
from node_manager import NodeManager
from user_manager import UserManager
from system_stats_manager import SystemStatsManager


class BotHandlers:
    """Класс с обработчиками для Telegram бота"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.node_manager = NodeManager()
        self.user_manager = UserManager()
        self.stats_manager = SystemStatsManager()
    
    def get_main_keyboard(self) -> types.ReplyKeyboardMarkup:
        """Создает основную клавиатуру"""
        kb = [
            [
                types.KeyboardButton(text="Управление пользователями"),
                types.KeyboardButton(text="Управление нодами")
            ],
            [
                types.KeyboardButton(text="Статистика системы")
            ]
        ]
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
        return keyboard
    
    async def handle_start(self, message: types.Message) -> None:
        """Обработчик команды /start"""
        await message.answer(
            "Добро пожаловать! Выберите действие:",
            reply_markup=self.get_main_keyboard()
        )
    
    async def handle_help(self, message: types.Message) -> None:
        """Обработчик команды /help"""
        help_text = (
            "Доступные команды:\n"
            "/start - Начать взаимодействие с ботом\n"
            "/help - Показать это сообщение\n"
            "/create_user - Создать нового пользователя\n"
            "/reboot_node - Перезагрузить узел\n"
        )
        await message.answer(help_text)
    
    async def handle_manage_users(self, message: types.Message) -> None:
        """Обработчик управления пользователями"""
        await message.answer("Загружаю список пользователей...")
        
        # Сбрасываем данные создания и страницу
        self.user_manager.clear_creation_data()
        self.user_manager.clear_selected_user()
        self.user_manager.reset_page()
        
        success, error_message = await self.user_manager.load_users_data()
        
        if not success:
            await message.answer(f"❌ Ошибка загрузки пользователей: {error_message}")
            return
        
        # Создаем клавиатуру со списком пользователей
        keyboard = self.user_manager.get_users_page_keyboard()
        
        # Отправляем список пользователей
        users_summary = self.user_manager.get_users_summary()
        sent_message = await message.answer(
            f"{users_summary}\n\nВыберите пользователя для управления:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        self.user_manager.set_last_message(sent_message.message_id, message.chat.id)
    
    async def handle_manage_nodes(self, message: types.Message) -> None:
        """Обработчик управления нодами"""
        await message.answer("Загружаю список нод...")
        
        success, error_message = await self.node_manager.load_nodes_data()
        
        if not success:
            await message.answer(error_message)
            return
        
        # Создаем клавиатуру со списком нод
        keyboard = self.node_manager.get_nodes_list_keyboard()
        
        # Отправляем список нод
        nodes_summary = self.node_manager.get_nodes_summary()
        await message.answer(
            f"{nodes_summary}\n\nВыберите ноду для управления:",
            reply_markup=keyboard
        )
    
    async def handle_back(self, message: types.Message) -> None:
        """Обработчик кнопки 'Назад'"""
        await message.answer(
            "Добро пожаловать! Выберите действие:",
            reply_markup=self.get_main_keyboard()
        )
    
    async def handle_node_selection(self, message: types.Message) -> None:
        """Обработчик выбора конкретной ноды"""
        node_name = message.text
        if not node_name:
            await message.answer("Некорректное имя ноды.")
            return
            
        node_data = self.node_manager.get_node_data(node_name)
        
        if not node_data:
            await message.answer("Данные о ноде не найдены. Попробуйте обновить список нод.")
            return
        
        # Сохраняем выбранную ноду
        self.node_manager.set_selected_node(node_name)
        
        # Форматируем информацию о ноде
        node_info = self.node_manager.format_node_info(node_data)
        
        # Создаем только инлайн-клавиатуру для управления
        keyboard = self.node_manager.get_node_management_inline_keyboard(node_data)
        
        # Отправляем сообщение и сохраняем его ID
        sent_message = await message.answer(node_info, reply_markup=keyboard, parse_mode="Markdown")
        self.node_manager.set_last_message(sent_message.message_id, message.chat.id)
    
    async def handle_enable_node(self, message: types.Message) -> None:
        """Обработчик включения ноды"""
        current_node = self.node_manager.get_selected_node()
        if not current_node:
            await message.answer("Сначала выберите ноду для управления.")
            return
        
        success, result_message = await self.node_manager.enable_node(current_node)
        await message.answer(result_message)
        
        if success:
            # Обновляем информацию о ноде
            await self._update_node_info(message, current_node)
    
    async def handle_disable_node(self, message: types.Message) -> None:
        """Обработчик отключения ноды"""
        current_node = self.node_manager.get_selected_node()
        if not current_node:
            await message.answer("Сначала выберите ноду для управления.")
            return
        
        success, result_message = await self.node_manager.disable_node(current_node)
        await message.answer(result_message)
        
        if success:
            # Обновляем информацию о ноде
            await self._update_node_info(message, current_node)
    
    async def handle_restart_node(self, message: types.Message) -> None:
        """Обработчик перезагрузки ноды"""
        current_node = self.node_manager.get_selected_node()
        if not current_node:
            await message.answer("Сначала выберите ноду для управления.")
            return
        
        success, result_message = await self.node_manager.restart_node(current_node)
        await message.answer(result_message)
        
        if success:
            # Обновляем информацию о ноде через несколько секунд
            await asyncio.sleep(3)
            await self._update_node_info(message, current_node)
    
    async def handle_refresh_node_info(self, message: types.Message) -> None:
        """Обработчик обновления информации о ноде"""
        current_node = self.node_manager.get_selected_node()
        if not current_node:
            await message.answer("Сначала выберите ноду для управления.")
            return
        
        await self._update_node_info(message, current_node)
    
    async def handle_back_to_nodes(self, message: types.Message) -> None:
        """Обработчик возврата к списку нод"""
        self.node_manager.clear_selected_node()
        await self.handle_manage_nodes(message)
    
    async def handle_restart_all_nodes(self, message: types.Message) -> None:
        """Обработчик перезагрузки всех нод"""
        if not self.node_manager.current_nodes:
            await message.answer("Список нод не загружен. Сначала загрузите список нод.")
            return
        
        nodes_count = len(self.node_manager.current_nodes)
        confirmation_keyboard = self.node_manager.get_restart_all_confirmation_keyboard()
        
        await message.answer(
            f"⚠️ **Подтверждение действия**\n\n"
            f"Вы действительно хотите перезагрузить **все ноды** ({nodes_count} нод(ы))?\n\n"
            f"Это может привести к временной недоступности сервисов.",
            reply_markup=confirmation_keyboard,
            parse_mode="Markdown"
        )
    
    async def _update_node_info(self, message: types.Message, node_name: str) -> None:
        """Обновляет информацию о конкретной ноде"""
        success, error_message = await self.node_manager.load_nodes_data()
        
        if not success:
            await message.answer(f"Не удалось получить обновленную информацию: {error_message}")
            return
        
        # Получаем обновленные данные о выбранной ноде
        node_data = self.node_manager.get_node_data(node_name)
        if not node_data:
            await message.answer("Нода не найдена в обновленных данных.")
            return
        
        # Форматируем информацию
        node_info = self.node_manager.format_node_info(node_data)
        inline_keyboard = self.node_manager.get_node_management_inline_keyboard(node_data)
        
        # Пытаемся обновить предыдущее сообщение
        message_id, chat_id = self.node_manager.get_last_message_info()
        
        if message_id and chat_id:
            try:
                await self.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=node_info,
                    reply_markup=inline_keyboard,
                    parse_mode="Markdown"
                )
            except Exception as e:
                error_text = str(e).lower()
                
                # Проверяем, является ли ошибка "сообщение не изменилось"
                if "message is not modified" in error_text or "exactly the same" in error_text:
                    await message.answer("ℹ️ Информация уже актуальна, изменений нет")
                    return
                
                # Если не удалось отредактировать, отправляем новое сообщение
                logging.warning(f"Не удалось отредактировать сообщение: {e}")
                sent_message = await message.answer(
                    f"🔄 **Обновленная информация:**\n{node_info}",
                    reply_markup=inline_keyboard,
                    parse_mode="Markdown"
                )
                self.node_manager.set_last_message(sent_message.message_id, message.chat.id)
        else:
            # Если нет сохраненного сообщения, отправляем новое
            sent_message = await message.answer(
                f"🔄 **Обновленная информация:**\n{node_info}",
                reply_markup=inline_keyboard,
                parse_mode="Markdown"
            )
            self.node_manager.set_last_message(sent_message.message_id, message.chat.id)
    
    def is_node_name(self, text: str) -> bool:
        """Проверяет, является ли текст именем ноды"""
        return self.node_manager.is_node_in_list(text)
    
    # Обработчики для инлайн-кнопок (callback_query)
    async def handle_inline_enable_node(self, callback_query) -> None:
        """Обработчик инлайн-кнопки включения ноды"""
        current_node = self.node_manager.get_selected_node()
        if not current_node:
            await callback_query.answer("Сначала выберите ноду для управления.", show_alert=True)
            return
        
        success, result_message = await self.node_manager.enable_node(current_node)
        
        if success:
            # Первое обновление сразу после включения
            await self._update_node_info_from_callback(callback_query, current_node)
            
            # Автоматическое обновление через 3 секунды
            asyncio.create_task(self._auto_update_node_after_delay(callback_query, current_node, 3))
        else:
            await callback_query.answer(result_message, show_alert=True)
    
    async def handle_inline_disable_node(self, callback_query) -> None:
        """Обработчик инлайн-кнопки отключения ноды"""
        current_node = self.node_manager.get_selected_node()
        if not current_node:
            await callback_query.answer("Сначала выберите ноду для управления.", show_alert=True)
            return
        
        success, result_message = await self.node_manager.disable_node(current_node)
        
        if success:
            # Первое обновление сразу после отключения
            await self._update_node_info_from_callback(callback_query, current_node)
            
            # Автоматическое обновление через 3 секунды
            asyncio.create_task(self._auto_update_node_after_delay(callback_query, current_node, 3))
        else:
            await callback_query.answer(result_message, show_alert=True)
    
    async def handle_inline_restart_node(self, callback_query) -> None:
        """Обработчик инлайн-кнопки перезагрузки ноды"""
        current_node = self.node_manager.get_selected_node()
        if not current_node:
            await callback_query.answer("Сначала выберите ноду для управления.", show_alert=True)
            return
        
        success, result_message = await self.node_manager.restart_node(current_node)
        
        if success:
            # Первое обновление сразу после перезагрузки
            await self._update_node_info_from_callback(callback_query, current_node)
            
            # Автоматическое обновление через 5 секунд (перезагрузка может занять больше времени)
            asyncio.create_task(self._auto_update_node_after_delay(callback_query, current_node, 5))
        else:
            await callback_query.answer(result_message, show_alert=True)
    
    async def handle_inline_refresh_info(self, callback_query) -> None:
        """Обработчик инлайн-кнопки обновления информации"""
        current_node = self.node_manager.get_selected_node()
        if not current_node:
            await callback_query.answer("Сначала выберите ноду для управления.", show_alert=True)
            return
        
        await self._update_node_info_from_callback(callback_query, current_node)
    
    async def handle_inline_back_to_nodes(self, callback_query) -> None:
        """Обработчик инлайн-кнопки возврата к списку нод"""
        await callback_query.answer()
        self.node_manager.clear_selected_node()
        self.node_manager.clear_last_message()
        
        # Получаем актуальный список нод
        success, error_message = await self.node_manager.load_nodes_data()
        
        if not success:
            await callback_query.message.answer(error_message)
            return
        
        # Создаем клавиатуру со списком нод
        keyboard = self.node_manager.get_nodes_list_keyboard()
        
        # Отправляем список нод
        nodes_summary = self.node_manager.get_nodes_summary()
        await callback_query.message.answer(
            f"{nodes_summary}\n\nВыберите ноду для управления:",
            reply_markup=keyboard
        )
    
    async def _update_node_info_from_callback(self, callback_query, node_name: str) -> None:
        """Обновляет информацию о ноде после нажатия инлайн-кнопки"""
        success, error_message = await self.node_manager.load_nodes_data()
        
        if not success:
            await callback_query.answer(f"Ошибка обновления: {error_message}", show_alert=True)
            return
        
        node_data = self.node_manager.get_node_data(node_name)
        if not node_data:
            await callback_query.answer("Нода не найдена в обновленных данных.", show_alert=True)
            return
        
        node_info = self.node_manager.format_node_info(node_data)
        inline_keyboard = self.node_manager.get_node_management_inline_keyboard(node_data)
        
        try:
            await self.bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                text=node_info,
                reply_markup=inline_keyboard,
                parse_mode="Markdown"
            )
            # Обновляем сохраненный ID сообщения
            self.node_manager.set_last_message(callback_query.message.message_id, callback_query.message.chat.id)
            # Отвечаем на callback без показа алерта (информация успешно обновилась)
            await callback_query.answer()
        except Exception as e:
            error_text = str(e).lower()
            
            # Проверяем, является ли ошибка "сообщение не изменилось"
            if "message is not modified" in error_text or "exactly the same" in error_text:
                await callback_query.answer("ℹ️ Информация уже актуальна, изменений нет", show_alert=True)
                return
            
            # Проверяем, можно ли редактировать сообщение
            if "message can't be edited" in error_text:
                await callback_query.answer("⚠️ Сообщение устарело и не может быть отредактировано", show_alert=True)
                # Отправляем новое сообщение
                sent_message = await callback_query.message.answer(
                    f"🔄 **Обновленная информация:**\n{node_info}", 
                    reply_markup=inline_keyboard,
                    parse_mode="Markdown"
                )
                self.node_manager.set_last_message(sent_message.message_id, callback_query.message.chat.id)
                return
            
            # Для других ошибок логируем и показываем алерт
            logging.warning(f"Не удалось отредактировать сообщение: {e}")
            await callback_query.answer("❌ Ошибка при обновлении сообщения", show_alert=True)
    
    async def _auto_update_node_after_delay(self, callback_query, node_name: str, delay_seconds: int) -> None:
        """Автоматическое обновление информации о ноде через заданное время"""
        try:
            # Ждем заданное количество секунд
            await asyncio.sleep(delay_seconds)
            
            # Проверяем, что нода все еще выбрана (пользователь не перешел к другой ноде)
            current_selected_node = self.node_manager.get_selected_node()
            if current_selected_node != node_name:
                return  # Пользователь перешел к другой ноде, не обновляем
            
            # Загружаем актуальные данные
            success, error_message = await self.node_manager.load_nodes_data()
            if not success:
                logging.warning(f"Не удалось загрузить данные для автообновления: {error_message}")
                return
            
            # Получаем данные ноды
            node_data = self.node_manager.get_node_data(node_name)
            if not node_data:
                logging.warning(f"Нода {node_name} не найдена при автообновлении")
                return
            
            # Форматируем информацию и создаем клавиатуру
            node_info = self.node_manager.format_node_info(node_data)
            inline_keyboard = self.node_manager.get_node_management_inline_keyboard(node_data)
            
            # Обновляем сообщение
            try:
                await self.bot.edit_message_text(
                    chat_id=callback_query.message.chat.id,
                    message_id=callback_query.message.message_id,
                    text=node_info,
                    reply_markup=inline_keyboard,
                    parse_mode="Markdown"
                )
            except Exception as e:
                error_text = str(e).lower()
                # Игнорируем ошибку "сообщение не изменилось"
                if "message is not modified" not in error_text and "exactly the same" not in error_text:
                    logging.warning(f"Ошибка при автообновлении сообщения: {e}")
                    
        except Exception as e:
            logging.error(f"Ошибка в автообновлении ноды {node_name}: {e}")
    
    # Обработчики для подтверждения перезагрузки всех нод
    async def handle_confirm_restart_all(self, callback_query) -> None:
        """Обработчик подтверждения перезагрузки всех нод"""
        await callback_query.answer()
        
        success, result_message = await self.node_manager.restart_all_nodes()
        
        if success:
            await callback_query.message.edit_text(
                f"✅ {result_message}\n\n"
                f"Процесс перезагрузки может занять несколько минут.",
                parse_mode="Markdown"
            )
        else:
            await callback_query.message.edit_text(
                f"❌ **Ошибка при перезагрузке всех нод**\n\n{result_message}",
                parse_mode="Markdown"
            )
    
    async def handle_cancel_restart_all(self, callback_query) -> None:
        """Обработчик отмены перезагрузки всех нод"""
        await callback_query.answer("Операция отменена")
        
        await callback_query.message.edit_text(
            "❌ **Операция отменена**\n\nПерезагрузка всех нод была отменена.",
            parse_mode="Markdown"
        )

    # =============== ОБРАБОТЧИКИ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ ===============
    
    async def handle_user_select(self, callback_query, user_index: int) -> None:
        """Обработчик выбора пользователя (устаревший метод)"""
        await callback_query.answer()
        
        user_data = self.user_manager.get_user_by_index(user_index)
        if not user_data:
            await callback_query.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Сохраняем выбранного пользователя
        self.user_manager.set_selected_user(user_data)
        
        # Форматируем информацию о пользователе
        user_info = self.user_manager.format_user_info(user_data)
        
        # Создаем клавиатуру для управления пользователем
        keyboard = self.user_manager.get_user_management_keyboard(user_data)
        
        try:
            await callback_query.message.edit_text(
                user_info,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.answer("❌ Ошибка при отображении информации", show_alert=True)
    
    async def handle_user_select_by_uuid(self, callback_query, user_uuid: str) -> None:
        """Обработчик выбора пользователя по UUID"""
        logging.info(f"Попытка выбора пользователя с UUID: {user_uuid}")
        await callback_query.answer()
        
        user_data = await self.user_manager.get_user_by_uuid(user_uuid)
        logging.info(f"Результат поиска пользователя: {user_data is not None}")
        
        if not user_data:
            logging.warning(f"Пользователь с UUID {user_uuid} не найден")
            await callback_query.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Сохраняем выбранного пользователя
        self.user_manager.set_selected_user(user_data)
        
        # Форматируем информацию о пользователе
        user_info = self.user_manager.format_user_info(user_data)
        
        # Создаем клавиатуру для управления пользователем
        keyboard = self.user_manager.get_user_management_keyboard(user_data)
        
        try:
            logging.info(f"Пытаемся отобразить информацию о пользователе {user_data.get('username', 'Unknown')}")
            await callback_query.message.edit_text(
                user_info,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            logging.info("Информация о пользователе успешно отображена")
        except Exception as e:
            logging.error(f"Ошибка при отображении информации о пользователе: {e}")
            await callback_query.answer("❌ Ошибка при отображении информации", show_alert=True)
    
    async def handle_users_pagination(self, callback_query, direction: str) -> None:
        """Обработчик пагинации пользователей"""
        await callback_query.answer()
        
        if direction == "next":
            if not self.user_manager.next_page():
                await callback_query.answer("Это последняя страница", show_alert=True)
                return
        elif direction == "prev":
            if not self.user_manager.prev_page():
                await callback_query.answer("Это первая страница", show_alert=True)
                return
        
        # Обновляем клавиатуру
        keyboard = self.user_manager.get_users_page_keyboard()
        users_summary = self.user_manager.get_users_summary()
        
        try:
            await callback_query.message.edit_text(
                f"{users_summary}\n\nВыберите пользователя для управления:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.answer("❌ Ошибка при обновлении страницы", show_alert=True)
    
    async def handle_refresh_users(self, callback_query) -> None:
        """Обработчик обновления списка пользователей"""
        await callback_query.answer("Обновляю список пользователей...")
        
        self.user_manager.reset_page()
        success, error_message = await self.user_manager.load_users_data()
        
        if not success:
            await callback_query.answer(f"❌ Ошибка: {error_message}", show_alert=True)
            return
        
        keyboard = self.user_manager.get_users_page_keyboard()
        users_summary = self.user_manager.get_users_summary()
        
        try:
            await callback_query.message.edit_text(
                f"{users_summary}\n\nВыберите пользователя для управления:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.answer("❌ Ошибка при обновлении", show_alert=True)
    
    async def handle_create_user_menu(self, callback_query) -> None:
        """Обработчик меню создания пользователя"""
        await callback_query.answer()
        
        # Загружаем список сквадов
        success, error_message = await self.user_manager.load_squads_data()
        if not success:
            await callback_query.answer(f"❌ Ошибка загрузки сквадов: {error_message}", show_alert=True)
            return
        
        keyboard = self.user_manager.get_creation_menu_keyboard()
        
        try:
            await callback_query.message.edit_text(
                "**🆕 Создание пользователя**\n\n"
                "Выберите тип создания:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.answer("❌ Ошибка при отображении меню", show_alert=True)
    
    async def handle_quick_create_user(self, callback_query) -> None:
        """Обработчик быстрого создания пользователя"""
        await callback_query.answer()
        
        # Загружаем список сквадов
        success, error_message = await self.user_manager.load_squads_data()
        if not success:
            await callback_query.answer(f"❌ Ошибка загрузки сквадов: {error_message}", show_alert=True)
            return
        
        # Показываем выбор сквада
        keyboard = self.user_manager.get_squads_selection_keyboard()
        
        try:
            await callback_query.message.edit_text(
                "**⚡ Быстрое создание пользователя**\n\n"
                "Параметры:\n"
                "• Случайное имя пользователя\n"
                "• Срок действия: 1 месяц\n"
                "• Без лимита трафика\n\n"
                "Выберите сквад для пользователя:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.answer("❌ Ошибка при отображении", show_alert=True)
    
    async def handle_create_user_custom(self, callback_query) -> None:
        """Обработчик пользовательского создания"""
        await callback_query.answer()
        
        self.user_manager.clear_creation_data()
        keyboard = self.user_manager.get_custom_creation_keyboard()
        
        try:
            await callback_query.message.edit_text(
                "**✏️ Пользовательское создание**\n\n"
                "Заполните параметры пользователя:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.answer("❌ Ошибка при отображении", show_alert=True)
    
    async def handle_squad_selection(self, callback_query, squad_uuid: str) -> None:
        """Обработчик выбора сквада"""
        await callback_query.answer()
        
        if squad_uuid == "none":
            self.user_manager.selected_squad_uuid = None
            squad_name = "Без сквада"
        else:
            self.user_manager.selected_squad_uuid = squad_uuid
            # Находим имя сквада
            squad_name = "Unknown"
            for squad in self.user_manager.current_squads:
                if squad.get('uuid') == squad_uuid:
                    squad_name = squad.get('name', 'Unknown')
                    break
        
        # Если это быстрое создание - создаем пользователя
        if callback_query.data.startswith("select_squad_") and "быстрое создание" in callback_query.message.text.lower():
            await callback_query.message.edit_text(
                f"⏳ Создаю пользователя в скваде **{squad_name}**...",
                parse_mode="Markdown"
            )
            
            success, message, user_data = await self.user_manager.create_user_quick()
            
            if success and user_data:
                # Устанавливаем созданного пользователя как выбранного
                self.user_manager.set_selected_user(user_data)
                
                # Показываем информацию о созданном пользователе
                user_info = self.user_manager.format_user_info(user_data)
                keyboard = self.user_manager.get_user_management_keyboard(user_data)
                
                await callback_query.message.edit_text(
                    f"{message}\n\n{user_info}",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                await callback_query.message.edit_text(
                    message,
                    parse_mode="Markdown"
                )
        else:
            # Если это выбор сквада для пользовательского создания - создаем пользователя
            if self.user_manager.creation_data and all(key in self.user_manager.creation_data 
                                                     for key in ['username', 'expire_days', 'traffic_limit']):
                await callback_query.message.edit_text(
                    f"⏳ Создаю пользователя **{self.user_manager.creation_data.get('username')}** в скваде **{squad_name}**...",
                    parse_mode="Markdown"
                )
                
                success, message, user_data = await self.user_manager.create_user_custom()
                
                if success and user_data:
                    # Устанавливаем созданного пользователя как выбранного
                    self.user_manager.set_selected_user(user_data)
                    
                    # Показываем информацию о созданном пользователе
                    user_info = self.user_manager.format_user_info(user_data)
                    keyboard = self.user_manager.get_user_management_keyboard(user_data)
                    
                    await callback_query.message.edit_text(
                        f"{message}\n\n{user_info}",
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                else:
                    await callback_query.message.edit_text(
                        message,
                        parse_mode="Markdown"
                    )
            else:
                # Переходим к созданию с пользовательскими данными
                keyboard = self.user_manager.get_custom_creation_keyboard()
                
                try:
                    await callback_query.message.edit_text(
                        f"**✏️ Пользовательское создание**\n\n"
                        f"Выбранный сквад: **{squad_name}**\n\n"
                        f"Заполните остальные параметры:",
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    await callback_query.answer("❌ Ошибка при отображении", show_alert=True)
    
    async def handle_proceed_to_squad_selection(self, callback_query) -> None:
        """Обработчик перехода к выбору сквада для пользовательского создания"""
        await callback_query.answer()
        
        # Загружаем список сквадов
        success, error_message = await self.user_manager.load_squads_data()
        if not success:
            await callback_query.answer(f"❌ Ошибка загрузки сквадов: {error_message}", show_alert=True)
            return
        
        keyboard = self.user_manager.get_squads_selection_keyboard()
        
        try:
            await callback_query.message.edit_text(
                "**✏️ Создание пользователя**\n\n"
                "Параметры заполнены. Выберите сквад:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.answer("❌ Ошибка при отображении", show_alert=True)
    
    async def handle_toggle_user_status(self, callback_query, user_data: dict) -> None:
        """Обработчик переключения статуса пользователя"""
        await callback_query.answer("Изменяю статус пользователя...")
        
        success, message = await self.user_manager.toggle_user_status(user_data)
        
        if success:
            # Обновляем данные пользователей и показываем обновленную информацию
            await self.user_manager.load_users_data()
            updated_user = None
            for user in self.user_manager.current_users:
                if user.get('uuid') == user_data.get('uuid'):
                    updated_user = user
                    break
            
            if updated_user:
                # Обновляем выбранного пользователя
                self.user_manager.set_selected_user(updated_user)
                
                user_info = self.user_manager.format_user_info(updated_user)
                keyboard = self.user_manager.get_user_management_keyboard(updated_user)
                
                try:
                    await callback_query.message.edit_text(
                        user_info,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    await callback_query.answer(f"✅ {message}", show_alert=True)
                except Exception as e:
                    await callback_query.answer(f"✅ {message}", show_alert=True)
            else:
                await callback_query.answer(message, show_alert=True)
        else:
            await callback_query.answer(message, show_alert=True)
    
    async def handle_reset_user_traffic(self, callback_query, user_data: dict) -> None:
        """Обработчик сброса трафика пользователя"""
        await callback_query.answer("Сбрасываю трафик...")
        
        success, message = await self.user_manager.reset_user_traffic(user_data)
        
        if success:
            # Обновляем данные пользователей и показываем обновленную информацию
            await self.user_manager.load_users_data()
            updated_user = None
            for user in self.user_manager.current_users:
                if user.get('uuid') == user_data.get('uuid'):
                    updated_user = user
                    break
            
            if updated_user:
                # Обновляем выбранного пользователя
                self.user_manager.set_selected_user(updated_user)
                
                user_info = self.user_manager.format_user_info(updated_user)
                keyboard = self.user_manager.get_user_management_keyboard(updated_user)
                
                try:
                    await callback_query.message.edit_text(
                        user_info,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    await callback_query.answer(f"✅ {message}", show_alert=True)
                except Exception as e:
                    await callback_query.answer(f"✅ {message}", show_alert=True)
            else:
                await callback_query.answer(message, show_alert=True)
        else:
            await callback_query.answer(message, show_alert=True)
    
    async def handle_get_user_link(self, callback_query, user_data: dict) -> None:
        """Обработчик получения ссылки пользователя"""
        await callback_query.answer("Получаю ссылку...")
        
        success, message = await self.user_manager.get_user_subscription_link(user_data)
        
        if success:
            # Отправляем ссылку в новом сообщении
            await callback_query.message.answer(message, parse_mode="Markdown")
            await callback_query.answer("✅ Ссылка отправлена", show_alert=True)
        else:
            await callback_query.answer(message, show_alert=True)
    
    async def handle_delete_user(self, callback_query, user_data: dict) -> None:
        """Обработчик удаления пользователя"""
        await callback_query.answer("Удаляю пользователя...")
        
        success, message = await self.user_manager.delete_user(user_data)
        
        if success:
            # Очищаем выбранного пользователя и возвращаемся к списку
            self.user_manager.clear_selected_user()
            self.user_manager.reset_page()
            await self.user_manager.load_users_data()
            
            keyboard = self.user_manager.get_users_page_keyboard()
            users_summary = self.user_manager.get_users_summary()
            
            try:
                await callback_query.message.edit_text(
                    f"{users_summary}\n\nВыберите пользователя для управления:",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                await callback_query.answer(f"✅ {message}", show_alert=True)
            except Exception as e:
                await callback_query.answer(f"✅ {message}", show_alert=True)
        else:
            await callback_query.answer(message, show_alert=True)
    
    async def handle_back_to_users(self, callback_query) -> None:
        """Обработчик возврата к списку пользователей"""
        await callback_query.answer()
        
        self.user_manager.clear_selected_user()
        self.user_manager.reset_page()
        success, error_message = await self.user_manager.load_users_data()
        
        if not success:
            await callback_query.answer(f"❌ Ошибка: {error_message}", show_alert=True)
            return
        
        keyboard = self.user_manager.get_users_page_keyboard()
        users_summary = self.user_manager.get_users_summary()
        
        try:
            await callback_query.message.edit_text(
                f"{users_summary}\n\nВыберите пользователя для управления:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.answer("❌ Ошибка при возврате", show_alert=True)
    
    async def handle_back_to_main(self, callback_query) -> None:
        """Обработчик возврата в главное меню"""
        await callback_query.answer()
        
        # Очищаем данные пользователей
        self.user_manager.clear_creation_data()
        self.user_manager.clear_selected_user()
        self.user_manager.clear_last_message()
        
        try:
            await callback_query.message.edit_text(
                "Добро пожаловать! Выберите действие:",
                reply_markup=None
            )
        except Exception as e:
            pass
    
    async def handle_cancel_user_creation(self, callback_query) -> None:
        """Обработчик отмены создания пользователя"""
        await callback_query.answer("Создание отменено")
        
        self.user_manager.clear_creation_data()
        await self.handle_back_to_users(callback_query)
    
    async def handle_refresh_user_info(self, callback_query, user_data: dict) -> None:
        """Обработчик обновления информации о пользователе"""
        await callback_query.answer("Обновляю информацию...")
        
        # Перезагружаем данные пользователей
        success, error_message = await self.user_manager.load_users_data()
        
        if not success:
            await callback_query.answer(f"❌ Ошибка: {error_message}", show_alert=True)
            return
        
        # Находим обновленные данные пользователя
        updated_user = None
        for user in self.user_manager.current_users:
            if user.get('uuid') == user_data.get('uuid'):
                updated_user = user
                break
        
        if not updated_user:
            await callback_query.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # Обновляем выбранного пользователя
        self.user_manager.set_selected_user(updated_user)
        
        # Обновляем отображение
        user_info = self.user_manager.format_user_info(updated_user)
        keyboard = self.user_manager.get_user_management_keyboard(updated_user)
        
        try:
            await callback_query.message.edit_text(
                user_info,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback_query.answer("ℹ️ Информация уже актуальна", show_alert=True)
    
    # Методы для работы с текстовыми сообщениями при создании пользователя
    def is_waiting_for_user_input(self) -> bool:
        """Проверяет, ожидается ли ввод от пользователя"""
        return (self.user_manager.waiting_for_username or 
                self.user_manager.waiting_for_expire_days or
                self.user_manager.waiting_for_traffic_limit or
                self.user_manager.waiting_for_description or
                self.user_manager.waiting_for_email or
                self.user_manager.waiting_for_tag)
    
    async def handle_user_text_input(self, message: types.Message) -> None:
        """Обработчик текстового ввода при создании пользователя"""
        if not message.text:
            return
            
        text = message.text.strip()
        
        if self.user_manager.waiting_for_username:
            self.user_manager.creation_data['username'] = text
            self.user_manager.waiting_for_username = False
            response = f"✅ Имя пользователя установлено: **{text}**"
            
        elif self.user_manager.waiting_for_expire_days:
            try:
                days = int(text)
                if days <= 0:
                    await message.answer("❌ Количество дней должно быть положительным числом")
                    return
                self.user_manager.creation_data['expire_days'] = days
                self.user_manager.waiting_for_expire_days = False
                response = f"✅ Срок действия установлен: **{days} дней**"
            except ValueError:
                await message.answer("❌ Введите корректное число дней")
                return
                
        elif self.user_manager.waiting_for_traffic_limit:
            try:
                if text.lower() in ['0', 'без лимита', 'unlimited']:
                    limit = 0
                else:
                    limit = float(text)
                    if limit < 0:
                        await message.answer("❌ Лимит трафика не может быть отрицательным")
                        return
                
                self.user_manager.creation_data['traffic_limit'] = limit
                self.user_manager.waiting_for_traffic_limit = False
                
                if limit == 0:
                    response = "✅ Лимит трафика: **Без ограничений**"
                else:
                    response = f"✅ Лимит трафика установлен: **{limit} GB**"
            except ValueError:
                await message.answer("❌ Введите корректное число или '0' для безлимита")
                return
                
        elif self.user_manager.waiting_for_description:
            self.user_manager.creation_data['description'] = text
            self.user_manager.waiting_for_description = False
            response = f"✅ Описание установлено: **{text}**"
            
        elif self.user_manager.waiting_for_email:
            self.user_manager.creation_data['email'] = text
            self.user_manager.waiting_for_email = False
            response = f"✅ Email установлен: **{text}**"
            
        elif self.user_manager.waiting_for_tag:
            self.user_manager.creation_data['tag'] = text
            self.user_manager.waiting_for_tag = False
            response = f"✅ Тег установлен: **{text}**"
        else:
            return
        
        # Отправляем подтверждение и обновленную клавиатуру
        keyboard = self.user_manager.get_custom_creation_keyboard()
        await message.answer(response, parse_mode="Markdown")
        
        # Обновляем последнее сообщение с клавиатурой
        message_id, chat_id = self.user_manager.get_last_message_info()
        if message_id and chat_id:
            try:
                await self.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=keyboard
                )
            except Exception:
                pass

    # =============== ОБРАБОТЧИКИ СТАТИСТИКИ СИСТЕМЫ ===============
    
    async def handle_system_stats(self, message: types.Message) -> None:
        """Обработчик меню статистики системы"""
        await message.answer("Загружаю статистику системы...")
        
        # Загружаем все данные
        success, error_message = await self.stats_manager.load_all_stats_data()
        
        if not success:
            await message.answer(f"❌ Ошибка загрузки статистики: {error_message}")
            return
        
        # Показываем сводку и клавиатуру категорий
        summary = self.stats_manager.get_stats_summary()
        keyboard = self.stats_manager.get_main_stats_keyboard()
        
        sent_message = await message.answer(
            summary,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        self.stats_manager.set_last_message(sent_message.message_id, message.chat.id)

    async def handle_stats_category(self, callback_query, category: str) -> None:
        """Обработчик выбора категории статистики"""
        self.stats_manager.set_current_category(category)
        
        # Определяем текст и клавиатуру в зависимости от категории
        if category == "stats_system":
            text = self.stats_manager.format_system_stats()
        elif category == "stats_bandwidth":
            text = self.stats_manager.format_bandwidth_stats()
        elif category == "stats_nodes":
            text = self.stats_manager.format_nodes_stats()
        elif category == "stats_realtime":
            text = self.stats_manager.format_realtime_stats()
        elif category == "stats_health":
            text = self.stats_manager.format_health_stats()
        else:
            text = "❌ Неизвестная категория статистики"

        keyboard = self.stats_manager.get_category_keyboard(category)
        
        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback_query.answer()
        except Exception as e:
            error_text = str(e).lower()
            
            # Проверяем, является ли ошибка "сообщение не изменилось"
            if "message is not modified" in error_text or "exactly the same" in error_text:
                await callback_query.answer("ℹ️ Информация уже актуальна, изменений нет", show_alert=True)
                return
            
            await callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

    async def handle_refresh_stats(self, callback_query, category: Optional[str] = None) -> None:
        """Обработчик обновления статистики"""
        await callback_query.answer("Обновляю статистику...")
        
        # Загружаем свежие данные
        success, error_message = await self.stats_manager.load_all_stats_data()
        
        if not success:
            await callback_query.answer(f"❌ Ошибка: {error_message}", show_alert=True)
            return
        
        if category:
            # Обновляем конкретную категорию
            await self.handle_stats_category(callback_query, category)
        else:
            # Обновляем главное меню статистики
            summary = self.stats_manager.get_stats_summary()
            keyboard = self.stats_manager.get_main_stats_keyboard()
            
            try:
                await callback_query.message.edit_text(
                    summary,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
                await callback_query.answer("✅ Статистика обновлена", show_alert=True)
            except Exception as e:
                error_text = str(e).lower()
                
                # Проверяем, является ли ошибка "сообщение не изменилось"
                if "message is not modified" in error_text or "exactly the same" in error_text:
                    await callback_query.answer("ℹ️ Информация уже актуальна, изменений нет", show_alert=True)
                    return
                
                await callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

    async def handle_stats_back_to_categories(self, callback_query) -> None:
        """Обработчик возврата к категориям статистики"""
        summary = self.stats_manager.get_stats_summary()
        keyboard = self.stats_manager.get_main_stats_keyboard()
        
        try:
            await callback_query.message.edit_text(
                summary,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback_query.answer()
        except Exception as e:
            error_text = str(e).lower()
            
            # Проверяем, является ли ошибка "сообщение не изменилось"
            if "message is not modified" in error_text or "exactly the same" in error_text:
                await callback_query.answer("ℹ️ Информация уже актуальна, изменений нет", show_alert=True)
                return
            
            await callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

    async def handle_stats_subcategory(self, callback_query, subcategory: str) -> None:
        """Обработчик подкатегорий статистики"""
        current_category = self.stats_manager.get_current_category()
        
        if not current_category:
            await callback_query.answer("❌ Категория не выбрана")
            return
        
        if subcategory.startswith("system_"):
            # Подкатегории системной статистики
            text = self._format_system_subcategory(subcategory)
        elif subcategory.startswith("bandwidth_"):
            # Подкатегории полосы пропускания больше не поддерживаются
            text = "❌ Подкатегории трафика больше не доступны. Вся информация отображается в общей статистике трафика."
        elif subcategory.startswith("nodes_"):
            # Подкатегории нод
            text = self._format_nodes_subcategory(subcategory)
        else:
            text = "❌ Неизвестная подкатегория"

        keyboard = self.stats_manager.get_category_keyboard(current_category)
        
        try:
            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback_query.answer()
        except Exception as e:
            error_text = str(e).lower()
            
            # Проверяем, является ли ошибка "сообщение не изменилось"
            if "message is not modified" in error_text or "exactly the same" in error_text:
                await callback_query.answer("ℹ️ Информация уже актуальна, изменений нет", show_alert=True)
                return
            
            await callback_query.answer(f"Ошибка: {str(e)}", show_alert=True)

    def _format_system_subcategory(self, subcategory: str) -> str:
        """Форматирует подкатегории системной статистики"""
        if not self.stats_manager.system_data or 'response' not in self.stats_manager.system_data:
            return "❌ Данные системной статистики недоступны"

        data = self.stats_manager.system_data['response']

        if subcategory == "system_users":
            users_info = data.get('users', {})
            status_counts = users_info.get('statusCounts', {})
            traffic_bytes = int(users_info.get('totalTrafficBytes', 0))
            traffic_gb = traffic_bytes / (1024**3)

            text = "👥 **Статистика пользователей**\n\n"
            text += f"📊 **Общие показатели:**\n"
            text += f"├ Всего пользователей: {users_info.get('totalUsers', 0)}\n"
            text += f"└ Общий трафик: {traffic_gb:.2f} GB\n\n"
            text += f"📈 **По статусам:**\n"
            text += f"├ 🟢 Активных: {status_counts.get('ACTIVE', 0)}\n"
            text += f"├ 🔴 Отключенных: {status_counts.get('DISABLED', 0)}\n"
            text += f"├ 🟡 Ограниченных: {status_counts.get('LIMITED', 0)}\n"
            text += f"└ ⚫ Истекших: {status_counts.get('EXPIRED', 0)}\n"
            
        elif subcategory == "system_memory":
            memory_info = data.get('memory', {})
            total_gb = memory_info.get('total', 0) / (1024**3)
            used_gb = memory_info.get('used', 0) / (1024**3)
            free_gb = memory_info.get('free', 0) / (1024**3)
            active_gb = memory_info.get('active', 0) / (1024**3)
            available_gb = memory_info.get('available', 0) / (1024**3)
            usage_percent = (used_gb / total_gb * 100) if total_gb > 0 else 0

            text = "💾 **Статистика памяти**\n\n"
            text += f"📊 **Использование: {usage_percent:.1f}%**\n\n"
            text += f"├ 📦 Всего: {total_gb:.2f} GB\n"
            text += f"├ ✅ Используется: {used_gb:.2f} GB\n"
            text += f"├ 🆓 Свободно: {free_gb:.2f} GB\n"
            text += f"├ ⚡ Активно: {active_gb:.2f} GB\n"
            text += f"└ 📋 Доступно: {available_gb:.2f} GB\n"
            
        else:
            text = "❌ Неизвестная подкатегория системной статистики"

        return text

    def _format_nodes_subcategory(self, subcategory: str) -> str:
        """Форматирует подкатегории нод"""
        if subcategory == "nodes_general":
            return self.stats_manager.format_nodes_stats()
        elif subcategory == "nodes_detailed":
            if not self.stats_manager.nodes_metrics_data or 'response' not in self.stats_manager.nodes_metrics_data:
                return "❌ Детальные данные нод недоступны"

            data = self.stats_manager.nodes_metrics_data['response']
            nodes = data.get('nodes', [])

            text = "🌐 **Детальная статистика нод**\n\n"

            for node in nodes:
                text += f"{node.get('countryEmoji', '🌍')} **{node.get('nodeName', 'Неизвестный узел')}**\n"
                text += f"├ Провайдер: {node.get('providerName', 'N/A')}\n"
                text += f"├ Пользователей онлайн: {node.get('usersOnline', 0)}\n\n"

                # Детальная статистика входящего трафика
                inbounds = node.get('inboundsStats', [])
                if inbounds:
                    text += f"  📥 **Входящий трафик:**\n"
                    for inbound in inbounds:
                        text += f"  ├ {inbound.get('tag', 'N/A')}: ↓{inbound.get('download', '0')} ↑{inbound.get('upload', '0')}\n"

                # Детальная статистика исходящего трафика
                outbounds = node.get('outboundsStats', [])
                if outbounds:
                    text += f"  📤 **Исходящий трафик:**\n"
                    for outbound in outbounds:
                        text += f"  ├ {outbound.get('tag', 'N/A')}: ↓{outbound.get('download', '0')} ↑{outbound.get('upload', '0')}\n"

                text += "\n"

            return text
        else:
            return "❌ Неизвестная подкатегория нод"
