# homework_bot
### python telegram bot
Проверяет статус домашней работы
- Перед запуском проверяет наличие токенов:
PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID;
- Отправляет запрос на ENDPOINT;
- Проверяет полученный ответ на корректность;
- Из полученного ответа извлекает значения двух ключей:
homework_name и status;
- Отправляет пользователю значение двух ключей(homework_name и status),
либо сообщение об ошибке.
