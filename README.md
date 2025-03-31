# Сервис по созданию коротких ссылок
## Функциональность 
### В сервисе реализованы следующие основные функции
1. Создание информации по короткой ссылке (доступно авторизованным и неавторизованным пользователям):  
POST /links/shorten – создает короткую ссылку  
POST /links/shorten (создается с параметром expires_at в формате даты)  
POST /links/shorten (создается кастомная ссылка, проверяется уникальность)  
2. Перенаправление на оригинальный адрес (доступно авторизованным и неавторизованным пользователям)  
GET /links/get_link/{short_code} – перенаправляет на оригинальный URL  
3. Удаление ссылки (доступно авторизованным пользователям, для удаления доступны свои ссылки и ссылки созданные неавторизованными пользователями)  
DELETE /links/delete_link/{short_code} – удаляет связь  
4. Обновление ссылки (доступно авторизованным пользователям, для удаления доступны свои ссылки и ссылки созданные неавторизованными пользователями)  
PUT /links/put_link/{short_code}  
5. Получение статистики по ссылке (доступно авторизованным и неавторизованным пользователям)  
GET /links/{short_code}/stats  
6. Поиск ссылки по оригинальному URL  (доступно авторизованным пользователям)
GET /links/search?original_url={url}
### В сервисе реализованы следующие дополнительные функции
1. Отображение истории всех истекших ссылок с информацией о них (доступно авторизованным пользователям)
GET /links/expired/  
3. Группировка ссылок по проектам (доступно авторизованным пользователям, доступны только созданные пользователем ссылки)
GET /links/project/{project}
5. Создание коротких ссылок для незарегистрированных пользователей.


## Демонстрация работы сервиса

### Регистрация пользователя
![Upload%20data.gif](https://github.com/Max-Arkhipov/AP_HW3_Fastapi/blob/main/assets/user_reg.gif)
### Создание короткой ссылки
![Upload%20data.gif](https://github.com/Max-Arkhipov/AP_HW3_Fastapi/blob/main/assets/link_shorten.gif)
### Изменение короткой ссылки  
![Upload%20data.gif](https://github.com/Max-Arkhipov/AP_HW3_Fastapi/blob/main/assets/link_put.gif)
### Удаление короткой ссылки
![Upload%20data.gif](https://github.com/Max-Arkhipov/AP_HW3_Fastapi/blob/main/assets/link_delete.gif)
### Получение оригинального URL  
![Upload%20data.gif](https://github.com/Max-Arkhipov/AP_HW3_Fastapi/blob/main/assets/link_get.gif)
### Поиск по оригинальному URL
![Upload%20data.gif](https://github.com/Max-Arkhipov/AP_HW3_Fastapi/blob/main/assets/link_search.gif)
### Просмотр удаленных ссылок
![Upload%20data.gif](https://github.com/Max-Arkhipov/AP_HW3_Fastapi/blob/main/assets/link_expired.gif)
### Просмотр ссылок по проекту
![Upload%20data.gif](https://github.com/Max-Arkhipov/AP_HW3_Fastapi/blob/main/assets/link_project.gif)

