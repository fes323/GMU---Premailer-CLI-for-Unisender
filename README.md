# GMU - CLI инструмент для верстальщиков email-рассылок

**GMU** — это мощный командный интерфейс для верстальщиков email-рассылок, который автоматизирует процесс создания, обработки и загрузки писем в популярные сервисы рассылок. Инструмент поддерживает интеграцию с **Unisender** и **WebLetter**, обеспечивая полный цикл работы с email-кампаниями от верстки до отправки.

![CLI working](https://my-bucket.ru/upload/process_1709.gif)

## 🚀 Основные возможности

- **Автоматическая инлайн-обработка CSS** с помощью собственного класса
- **Загрузка писем в Unisender** через API с полной поддержкой изображений
- **Интеграция с WebLetter** для создания превью писем
- **Создание архивов** для удобного хранения и передачи
- **Отправка тестовых писем** для проверки перед массовой рассылкой
- **Управление кампаниями** с поддержкой UTM-меток
- **Автодополнение команд** для повышения эффективности работы

## 📦 Установка

### Способ 1: Установка через Poetry (рекомендуется)

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/fes323/GMU---Premailer-CLI-for-Unisender.git
cd GMU---Premailer-CLI-for-Unisender
```

2. **Установите зависимости:**
```bash
poetry install
```

3. **Соберите пакет:**
```bash
poetry build
```

4. **Установите CLI:**
```bash
cd dist
pip install gmu-1.0.0-py3-none-any.whl
```

### Способ 2: Установка через pip

```bash
pip install gmu
```

### Проверка установки

```bash
gmu --version
```

## ⚙️ Настройка окружения

Создайте файл `.env` в корне проекта или в директории пользователя:

**Windows:** `C:\Users\USERNAME\AppData\Roaming\gmu\.env`  
**Linux/macOS:** `~/.config/gmu/.env`

```env
# Unisender API
UNISENDER_API_KEY=your_api_key_here
UNISENDER_API_URL=https://api.unisender.com/ru/api/

# WebLetter (опционально)
WL_AUTH_TOKEN=your_wl_token_here
WL_URL=https://domain.ru/
WL_ENDPOINT=https://domain.ru/api/webletters/

# Дополнительные настройки
UNICNV_DLL_PATH=
```

## 🛠️ Используемые библиотеки/фреймворки

### Основные зависимости:
- **[Typer](https://github.com/fastapi/typer)** (>=0.16.0) - CLI фреймворк для создания команд
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** (>=4.13.4) - Парсинг и обработка HTML
- **[Requests](https://requests.readthedocs.io/en/latest/)** (>=2.32.3) - HTTP-запросы к API
- **[Python-dotenv](https://github.com/theskumar/python-dotenv)** (>=1.1.0) - Загрузка переменных окружения
- **[CairoSVG](https://cairosvg.org/)** (>=2.8.2) - Конвертация SVG в другие форматы
- **[Termcolor](https://github.com/termcolor/termcolor)** (>=3.1.0) - Цветной вывод в терминал
- **[Pillow](https://python-pillow.github.io/)** (>=11.2.1) - Обработка изображений

### Дополнительные зависимости CairoSVG:

**⚠️ Важно:** CairoSVG требует установки системных зависимостей:

- **Windows:** [GTK-for-Windows-Runtime-Environment-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
- **macOS:** 
  ```bash
  brew install cairo libffi
  ```
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt-get install cairo python3-dev libffi-dev
  ```

## 📋 Команды и их использование

### 🔧 Основные команды

#### Версия
```bash
gmu --version
```
Показывает текущую версию CLI.

#### Автодополнение
```bash
gmu --install-completion  # Установить автодополнение
gmu --show-completion     # Показать настройки автодополнения
```

### 📧 Работа с сообщениями (Unisender)

#### Создание письма
```bash
gmu message create [--list-id LIST_ID] [--html-filename FILE] [--images-folder FOLDER] [--force]
```
- `--list-id` - ID списка рассылки (по умолчанию: 20547119)
- `--html-filename` - Имя HTML файла (по умолчанию: первый .html в папке)
- `--images-folder` - Папка с изображениями (по умолчанию: "images")
- `--force` - Пропустить проверку существующего письма

#### Создание/обновление письма (upsert)
```bash
gmu message upsert [--list-id LIST_ID] [--html-filename FILE] [--images-folder FOLDER] [--force]
```
Автоматически определяет, нужно ли создать новое письмо или обновить существующее на основе файла `gmu.json`.

#### Обновление письма
```bash
gmu message update [--html-filename FILE] [--list-id LIST_ID] [--images-folder FOLDER]
```
**Важно:** Unisender не поддерживает прямое обновление писем с изображениями, поэтому команда сначала удаляет старое письмо, затем создает новое.

#### Удаление письма
```bash
gmu message delete [--id MESSAGE_ID]
```
- `--id` - ID письма для удаления (по умолчанию берется из `gmu.json`)

#### Отправка тестового письма
```bash
gmu message test [--id MESSAGE_ID] [--email EMAIL_ADDRESSES]
```
- `--id` - ID письма в Unisender (по умолчанию из `gmu.json`)
- `--email` - Email адреса для тестирования (можно указать несколько через запятую)

### 🎯 Управление кампаниями

#### Создание кампании
```bash
gmu campaign create [--message-id ID] [--start-time TIME] [--track-ga 0|1] [--ga-medium MEDIUM] [--ga-source SOURCE] [--ga-campaign CAMPAIGN]
```
- `--message-id` - ID письма (по умолчанию из `gmu.json`)
- `--start-time` - Время начала в формате 'YYYY-MM-DD HH:MM'
- `--track-ga` - Включить UTM-метки (1) или выключить (0)
- `--ga-medium`, `--ga-source`, `--ga-campaign` - Параметры UTM-меток

#### Статус кампании
```bash
gmu campaign status CAMPAIGN_ID
```

### 🌐 Интеграция с WebLetter

#### Загрузка/обновление письма на WebLetter
```bash
gmu wl upsert
```
Загружает письмо на [WebLetter](https://github.com/rastereo/webletter-api) для создания превью.

#### Удаление письма с WebLetter
```bash
gmu wl delete [--id WL_ID]
```
- `--id` - ID письма в WebLetter (по умолчанию из `gmu.json`)

### 📁 Дополнительные возможности

#### Создание архива
```bash
gmu archive [--html-filename FILE] [--images-folder FOLDER]
```
Создает ZIP-архив с HTML файлом и изображениями.

## 📝 Структура проекта

```
project/
├── index.html          # Основной HTML файл письма
├── images/            # Папка с изображениями
└── gmu.json           # Конфигурационный файл (создается автоматически)
```

## 🔍 Примеры использования

### Базовый workflow:

1. **Создайте HTML файл письма** в корне проекта
2. **Поместите изображения** в папку `images/`
3. **Настройте переменные окружения** в `.env`
4. **Создайте письмо:**
   ```bash
   gmu message create
   ```
5. **Отправьте тестовое письмо:**
   ```bash
   gmu message test --email test@example.com
   ```
6. **Создайте кампанию:**
   ```bash
   gmu campaign create --start-time "2024-01-15 10:00"
   ```

### Обновление существующего письма:

```bash
gmu message upsert
```

### Загрузка на WebLetter:

```bash
gmu wl upsert
```

## 🐛 Устранение неполадок

### Проблемы с CairoSVG:
- Убедитесь, что установлены все системные зависимости
- На Windows установите GTK Runtime Environment
- На Linux установите пакеты: `cairo`, `python3-dev`, `libffi-dev`

### Проблемы с API:
- Проверьте правильность API ключей в `.env`
- Убедитесь, что файл `.env` находится в правильной директории
- Проверьте доступность API endpoints

### Проблемы с файлами:
- Убедитесь, что HTML файл находится в корне проекта
- Проверьте права доступа к папке `images/`
- Убедитесь, что все изображения имеют корректные пути


## 🤝 Поддержка

При возникновении проблем создайте issue в репозитории.



