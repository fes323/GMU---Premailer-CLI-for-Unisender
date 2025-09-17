# GMU - Premailer CLI-app
GMU позволяет собрать архив E-mail рассылки для загрузки в сервис рассылок (Unisender/SendSay).
Есть поддержка загрузки писем в Unisender по API (```gmu message create/update/delete```).

![CLI working](https://my-bucket.ru/upload/process_1709.gif)

## 🤖 Установка
Для установки CLI необходимо установить Python >= 3.6 и пакетный менеджер pip.
1. Скопировать проект на локальный диск   
```bash
git clone https://github.com/fes323/GMU---Premailer-CLI-for-Unisender./tree/main
```   
2. Перейти в директорию проекта    
```bash
cd  GMU---Premailer-CLI-for-Unisender
```   
3. Установить зависимости   
```bash
poetry install
```
4. Собрать установщик    
```bash 
poetry build
```
5. Перейти в директорию dist/   
```bash
cd dist
```
6. Установить CLI 
```bash
pip install <название пакета whl>
```   
Это позволит установить CLI в глобальное окружение. В командной строке появится возможность использовать команды gmu.
Для проверки корректности установи можно ввести базовую команду 
```bash 
gmu --version
```

## Используемые библиотеки
Все библиотеки перечислены в файле ```pyproject.toml```   
Все зависимости можно посмотреть в ```requirements.txt```   

1. [Typer](https://github.com/fastapi/typer)
2. [Premailer](https://github.com/peterbe/premailer)
3. [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
4. [requests](https://requests.readthedocs.io/en/latest/)
5. [python-dotenv](https://github.com/theskumar/python-dotenv)
6. [cairosvg](https://cairosvg.org/)
7. [termcolor](https://github.com/termcolor/termcolor)
8. [pillow](https://python-pillow.github.io/)  

У **CairoSVG** есть дополнительные зависимости, которые нужно установить вручную.  
* Windows - [GTK-for-Windows-Runtime-Environment-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)  
* macOS - cairo и libffi ([Homebrew](https://brew.sh/)). На macOS не тестировал, поэтому рекомендую ознакомиться с зависимостями в [документации CairoSVG](https://cairosvg.org/documentation/)  
* Linux - cairo, python3-dev и libffi-dev пакеты  

**Создание PDF доступно пока только для Windows.**
Есть дополнительная зависимость, которую нужно установить вручную - [wkhtmltopdf](https://wkhtmltopdf.org/)
К сожалению, обычные конверторы PDF не поддерживают в полной мере табличную верстку, поэтому приходится использовать более изоощеренные подходы.   
wkhtmltopdf достаточно устарел, имеет баги и почти не обновляется. Идут поиски альтернативных решений.  
  
## Автодополнение/автозавершение команд
Для автодополнения команд необходимо, после установки gmu, выполнить следующие команды:
1. ```gmu --install-completion``` - установить автодополнение
2. ```gmu --show-completion``` - посмотреть автодополнение  

Это позволит завершать команды по нажатию TAB.

## Загрузка писем - [Unisender](https://www.unisender.com/)
Для загрузки писем в Unisender необходимо указать API Key в файле ```.env```.

**Доступные команды**
1. Создает/обновляет письмо в Unisender. Если в рабочей директории есть gmu.json с message_id, то письмо будет обновлено (старое письмо удалено и создано новое), если файла gmu.json нет и/или нет message_id, то будет создано новое письмо
```bash
gmu message upsert
```
2. Cоздает письмо в Unisender. ID письма копируется в буфер обмена.
```bash
gmu message create
```
3. Обновляет письмо в Unisender. Из-за ограничения Unisender, вызывается два метода API - ```delete``` и ```create```, т.к. если вызывать метод ```update```, то при использовании картинок через директорию ```images/``` возникает ошибка, что Unisender не загружает картинки, а лишь обновляет саму верстку.
```bash
gmu message update
```
4. Удаляет письмо в Unisender.
```bash
gmu message delete
```

## Загрузка писем - [WebLetter-api](https://github.com/rastereo/webletter-api)
Есть поддержка загрузки превью писем на [WebLetter](https://github.com/rastereo/webletter-api "Проект на GitHub. Нужно будет развернуть backend и frontend на сервере или локально и добавить адрес + токен в .env файл").
Функция загрузки писем на WebLetter отличается от загрузи писем в Unisender, реализованы разные подходы.

**Соответствующие команды:**
1. Загрузить/обновить письмо на WebLetter
```bash
gmu wl upsert
```
2. Удалить письмо
```bash
gmu wl delete
```

## Дополнительные возможности
1. Создание PDF Документа (только Windows)
```bash
gmu pdf
```
2. Создание архива
```bash
gmu archive
```



