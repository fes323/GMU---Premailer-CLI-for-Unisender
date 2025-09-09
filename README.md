# GMU - Premailer CLI-app
GMU позволяет собрать архив E-mail рассылки для загрузки в сервис рассылок (Unisender/SendSay).
Есть поддержка загрузки писем в Unisender по API (```gmu message create/update/delete```).

### Загрузка писем - [Unisender](https://www.unisender.com/)
Для загрузки писем в Unisender необходимо указать API Key в файле ```.env```.

**Доступные команды**
1. ```gmu message create``` - создает письмо в Unisender. ID письма копируется в буфер обмена.
2. ```gmu message update``` - обновляет письмо в Unisender. Из-за ограничения Unisender, вызывается два метода API - ```delete``` и ```create```, т.к. если вызывать метод ```update```, то при использовании картинок через директорию ```images/``` возникает ошибка, что Unisender не загружает картинки, а лишь обновляет саму верстку.
3. ```gmu message delete``` - удаляет письмо в Unisender.

### Загрузка писем - [WebLetter-api](https://github.com/rastereo/webletter-api)
Есть поддержка загрузки превью писем на [WebLetter](https://github.com/rastereo/webletter-api "Проект на GitHub. Нужно будет развернуть backend и frontend на сервере или локально и добавить адрес + токен в .env файл").
Функция загрузки писем на WebLetter отличается от загрузи писем в Unisender, реализованы разные подходы.

**Соответствующие команды:**
1. ```gmu message wl``` - загрузить/обновить письмо на WebLetter
2. ```gmu message wl-delete``` - удалить письмо

## Используемые библиотеки
Все библиотеки перечислены в файле ```pyproject.toml```
1. Typer
2. Premailer
3. beautifulsoup4
4. requests
5. python-dotenv
6. cairosvg
7. termcolor
8. pillow  

У CairoSVG есть дополнительные зависимости, которые нужно установить вручную.  
* Windows - [GTK-for-Windows-Runtime-Environment-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)  
* macOS - cairo и libffi ([Homebrew](https://brew.sh/)). На macOS не тестировал, поэтому рекомендую ознакомиться с зависимостями в [документации CairoSVG](https://cairosvg.org/documentation/)  
* Linux - cairo, python3-dev и libffi-dev пакеты  

#### Автодополнение/автозавершение команд
Для автодополнения команд необходимо, после установки gmu, выполнить следующие команды:
1. ```gmu --install-completion``` - установить автодополнение
2. ```gmu --show-completion``` - посмотреть автодополнение  

Это позволит завершать команды по нажатию TAB.
