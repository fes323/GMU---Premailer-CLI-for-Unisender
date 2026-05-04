# GMU - CLI для email-рассылок

GMU автоматизирует подготовку HTML-писем, загрузку в Unisender, работу с WebLetter, отправку тестов, создание кампаний и хранение служебного состояния проекта в `gmu.json`.

Основной рабочий сценарий: сверстать письмо в папке проекта, обработать HTML и изображения, создать или обновить письмо в Unisender, загрузить превью в WebLetter, отправить тест, создать кампанию и при необходимости зафиксировать изменения в git.

## Возможности

- Инлайн CSS через JS-библиотеку Juice.
- Конвертация SVG в PNG через `@resvg/resvg-js` без Cairo/GTK и других системных графических зависимостей.
- Обработка изображений через Pillow: ресайз, сжатие, переименование вложений.
- Создание ZIP-архива письма.
- Создание, обновление, удаление и проверка писем в Unisender.
- Отправка тестовых писем через Unisender.
- Создание кампаний Unisender, проверка статуса и получение web version.
- Загрузка и удаление писем в WebLetter.
- Хранение `message_id`, `webletter_id`, `campaign_id`, версии письма и настроек в `gmu.json`.
- Опциональная git-автосинхронизация после успешных операций.

## Стек

### Python

- Python 3.11+
- Typer - CLI-команды и автодополнение.
- Requests - HTTP-запросы к Unisender и WebLetter.
- BeautifulSoup4 - парсинг и правка HTML.
- Pillow - обработка изображений.
- python-dotenv - загрузка `.env`.
- termcolor и Rich - форматированный вывод в консоль.
- pyperclip - копирование ID письма в буфер обмена, если буфер доступен.

### Node.js

- Node.js 18+
- npm
- Juice 11.0.1 - CSS inliner.
- `@resvg/resvg-js` 2.6.2 - SVG -> PNG.

### Внешние сервисы

- Unisender API.
- WebLetter API.
- Git, только если включена git-автосинхронизация.

## Установка

### Требования

Проверьте версии:

```bash
python --version
node --version
npm --version
```

Для установки из исходников нужен Poetry:

```bash
poetry --version
```

### Установка из репозитория

```bash
git clone https://github.com/fes323/GMU---Premailer-CLI-for-Unisender.git
cd GMU---Premailer-CLI-for-Unisender
poetry install
npm install
poetry run gmu --version
```

При разработке команды можно запускать через `poetry run`, например `poetry run gmu m u`.

### Установка wheel

Сборка:

```bash
poetry build
```

Установка:

```bash
pip install dist/gmu-2.0.0-py3-none-any.whl
```

После установки Python-пакета установите JS-зависимости. Можно глобально:

```bash
npm install -g juice@11.0.1 @resvg/resvg-js@2.6.2
```

Или локально в папке проекта письма:

```bash
npm install juice@11.0.1 @resvg/resvg-js@2.6.2
```

Проверка:

```bash
gmu --version
npm ls -g juice @resvg/resvg-js
```

### Установка через pip

Если пакет опубликован в PyPI:

```bash
pip install gmu
npm install -g juice@11.0.1 @resvg/resvg-js@2.6.2
gmu --version
```

### Переменные для нестандартных путей

Если Node.js или npm-пакеты установлены нестандартно, можно указать пути вручную.

PowerShell:

```powershell
$env:GMU_NODE_BINARY="C:\path\to\node.exe"
$env:GMU_JUICE_MODULE="C:\path\to\node_modules\juice"
$env:GMU_JUICE_CONFIG="C:\path\to\juice_config.js"
$env:GMU_RESVG_MODULE="C:\path\to\node_modules\@resvg\resvg-js"
```

cmd.exe:

```cmd
set GMU_NODE_BINARY=C:\path\to\node.exe
set GMU_JUICE_MODULE=C:\path\to\node_modules\juice
set GMU_JUICE_CONFIG=C:\path\to\juice_config.js
set GMU_RESVG_MODULE=C:\path\to\node_modules\@resvg\resvg-js
```

По умолчанию настройки Juice лежат в `gmu/utils/juice_config.js`. В конфиг перенесены параметры из `cahe`: `preserveImportant: true` и `removeStyleTags: false`.

## Настройка окружения

GMU ищет `.env` рядом с пакетом или в пользовательской директории:

- Windows: `%APPDATA%\gmu\.env`
- Linux/macOS: `~/.config/gmu/.env`

Пример:

```env
UNISENDER_API_KEY=your_api_key_here
UNISENDER_API_URL=https://api.unisender.com/ru/api/

WL_AUTH_TOKEN=your_wl_token_here
WL_URL=https://domain.ru/
WL_ENDPOINT=https://domain.ru/api/webletters/
```

`UNISENDER_API_KEY` и `UNISENDER_API_URL` нужны для команд Unisender. `WL_AUTH_TOKEN`, `WL_URL` и `WL_ENDPOINT` нужны для команд WebLetter.

## Структура проекта письма

Минимальная структура:

```text
letter-project/
├── index.html
├── images/
└── gmu.json
```

`gmu.json` создается автоматически. В нем GMU хранит:

- `message_id`, `message_url` - письмо в Unisender.
- `sender_name`, `sender_email`, `subject`, `preheader`, `lang` - данные, извлеченные из HTML.
- `webletter_id`, `webletter_url` - письмо в WebLetter.
- `campaign_id`, `campaign_status`, `campaign_creation_time`, `campaign_start_time` - последняя кампания.
- `web_version_url`, `web_version_letter_id` - web version кампании.
- `actual_version_id` - актуальная версия письма в Unisender.
- `zip_size` - размер ZIP-архива.
- `letter_version` - версия письма для git-коммитов.
- `settings.git_auto_sync` - включение git-автосинхронизации.

## Команды

### Общие команды

| Команда | Коротко | Назначение |
| --- | --- | --- |
| `gmu --version` | `gmu -V` | Версия CLI |
| `gmu version` | `gmu v` | Версия CLI |
| `gmu archive` | `gmu a` | Создать ZIP-архив |
| `gmu message ...` | `gmu m ...` | Команды Unisender для писем |
| `gmu campaign ...` | `gmu c ...` | Команды Unisender для кампаний |
| `gmu settings ...` | `gmu cfg ...` | Настройки проекта |
| `gmu wl ...` | `gmu webletter ...` | Команды WebLetter |

Автодополнение:

```bash
gmu --install-completion
gmu --show-completion
```

### Архив

```bash
gmu archive [--html-filename FILE] [--images-folder FOLDER]
gmu a [--html-filename FILE] [--images-folder FOLDER]
```

Создает ZIP-архив письма. Если `--html-filename` не указан, используется первый `.html` в текущей папке.

Пример:

```bash
gmu a --html-filename index.html --images-folder images
```

### Письма Unisender

#### Создать письмо

```bash
gmu message create [--list-id LIST_ID] [--html-filename FILE] [--images-folder FOLDER] [--force]
gmu m c [--list-id LIST_ID] [--html-filename FILE] [--images-folder FOLDER] [--force]
```

Создает письмо в Unisender, архивирует HTML и изображения, сохраняет `message_id` и `message_url` в `gmu.json`.

Пример:

```bash
gmu m c --list-id 20547119 --html-filename index.html
```

`--force` пропускает проверку, что в `gmu.json` уже есть `message_id`.

#### Создать или пересоздать письмо

```bash
gmu message upsert [--list-id LIST_ID] [--html-filename FILE] [--images-folder FOLDER] [--force]
gmu m u [--list-id LIST_ID] [--html-filename FILE] [--images-folder FOLDER] [--force]
```

Если `message_id` есть в `gmu.json`, команда удаляет старое письмо и создает новое. Если `message_id` нет, создает письмо.

Пример:

```bash
gmu m u
```

#### Обновить письмо

```bash
gmu message update [--html-filename FILE] [--list-id LIST_ID] [--images-folder FOLDER]
gmu m upd [--html-filename FILE] [--list-id LIST_ID] [--images-folder FOLDER]
```

Команда берет `message_id` из `gmu.json`, удаляет письмо в Unisender и создает новое с новым ID.

Пример:

```bash
gmu m upd --html-filename index.html
```

#### Удалить письмо

```bash
gmu message delete [--id MESSAGE_ID]
gmu m d [--id MESSAGE_ID]
```

Если `--id` не указан, ID берется из `gmu.json`. После успешного удаления `message_id`, `message_url` и `actual_version_id` очищаются.

Пример:

```bash
gmu m d
gmu m d --id 123456789
```

#### Отправить тест

```bash
gmu message test [--id MESSAGE_ID] --email EMAILS
gmu m t [--id MESSAGE_ID] --email EMAILS
```

`--email` может содержать один адрес или несколько адресов через запятую.

Пример:

```bash
gmu m t --email test@example.com
gmu m t --id 123456789 --email "a@example.com,b@example.com"
```

#### Получить информацию о письме

```bash
gmu message info [--id MESSAGE_ID] [--save/--no-save]
gmu m i [--id MESSAGE_ID] [--save/--no-save]
```

Показывает данные письма из Unisender. С `--save` сохраняет метаданные в `gmu.json`.

Пример:

```bash
gmu m i
gmu m i --id 123456789 --save
```

#### Проверить актуальную версию письма

```bash
gmu message actual [--id MESSAGE_ID] [--save/--no-save]
gmu m act [--id MESSAGE_ID] [--save/--no-save]
```

Команда вызывает `getActualMessageVersion`. По умолчанию сохраняет `actual_version_id` и обновляет `message_id` в `gmu.json`.

Пример:

```bash
gmu m act
gmu m act --id 123456789 --no-save
```

### Кампании Unisender

#### Создать кампанию

```bash
gmu campaign create [--message-id ID] [--start-time TIME | --now] [--timezone UTC] [--track-read 0|1] [--track-links 0|1] [--track-ga 0|1] [--ga-medium MEDIUM] [--ga-source SOURCE] [--ga-campaign CAMPAIGN] [--use-actual-version/--skip-actual-version]
gmu c c [--message-id ID] [--start-time TIME | --now] [--timezone UTC] [--track-read 0|1] [--track-links 0|1] [--track-ga 0|1] [--ga-medium MEDIUM] [--ga-source SOURCE] [--ga-campaign CAMPAIGN] [--use-actual-version/--skip-actual-version]
```

Если `--message-id` не указан, используется `message_id` из `gmu.json`. Перед созданием кампании GMU по умолчанию проверяет актуальную версию письма через `getActualMessageVersion`.

Примеры:

```bash
gmu c c --start-time "2026-05-04 10:00"
gmu c c --now
gmu c c --message-id 123456789 --start-time "2026-05-04 10:00" --track-ga 1 --ga-campaign may_digest
gmu c c --start-time "2026-05-04 10:00" --skip-actual-version
```

После успешного создания сохраняются `campaign_id` и `campaign_status`.

#### Получить статус кампании

```bash
gmu campaign status [CAMPAIGN_ID]
gmu c s [CAMPAIGN_ID]
```

Если `CAMPAIGN_ID` не указан, используется `campaign_id` из `gmu.json`.

Пример:

```bash
gmu c s
gmu c s 987654321
```

#### Получить web version кампании

```bash
gmu campaign web [--campaign-id CAMPAIGN_ID]
gmu c w [--campaign-id CAMPAIGN_ID]
```

Если `--campaign-id` не указан, используется `campaign_id` из `gmu.json`. Результат сохраняется в `web_version_url`.

Пример:

```bash
gmu c w
gmu c w --campaign-id 987654321
```

### WebLetter

#### Загрузить или обновить письмо

```bash
gmu wl upsert
gmu wl u
```

Команда собирает архив и загружает его в WebLetter. Если в `gmu.json` есть `webletter_id`, письмо обновляется по той же ссылке. Если ID нет, создается новое письмо.

Пример:

```bash
gmu wl u
```

#### Удалить письмо

```bash
gmu wl delete [--id WL_ID]
gmu wl d [--id WL_ID]
```

Если `--id` не указан, используется `webletter_id` из `gmu.json`.

Пример:

```bash
gmu wl d
gmu wl d --id abc123
```

### Настройки проекта

#### Показать настройки

```bash
gmu settings show
gmu cfg show
```

Показывает `letter_version`, `git_auto_sync`, `message_id`, `webletter_id`, `campaign_id`.

#### Git-автосинхронизация

```bash
gmu settings git
gmu settings git --enable
gmu settings git --disable
gmu cfg git --enable
```

Когда `settings.git_auto_sync=true`, после успешных команд, которые меняют письмо, кампанию или WebLetter, GMU выполняет:

```bash
git pull
git add ./
git commit -m "<название рабочей директории> v <letter_version>"
git push
```

Перед `git add ./` команда увеличивает `letter_version` в `gmu.json`, поэтому новая версия попадает в коммит. Если git-команда завершилась ошибкой, выполненный деплой не откатывается.

#### Версия письма

```bash
gmu settings version
gmu settings version VERSION
gmu cfg version VERSION
```

Пример:

```bash
gmu cfg version 12
```

## Рабочие сценарии

### Быстрый старт Unisender

```bash
gmu m c --list-id 20547119
gmu m t --email test@example.com
gmu c c --start-time "2026-05-04 10:00"
gmu c s
gmu c w
```

### Обновление письма

```bash
gmu m u
gmu m t --email test@example.com
```

### Превью в WebLetter

```bash
gmu wl u
```

После правок HTML:

```bash
gmu wl u
```

### Работа с git-автосинхронизацией

```bash
gmu cfg git --enable
gmu cfg version 1
gmu wl u
```

После успешной загрузки GMU выполнит `git pull`, увеличит `letter_version`, сделает `git add ./`, создаст коммит вида `my-letter v 2` и выполнит `git push`.

### Ручная проверка актуальной версии письма

```bash
gmu m act
gmu c c --start-time "2026-05-04 10:00"
```

## Обработка HTML и изображений

GMU ищет HTML-файл в текущей папке, если `--html-filename` не указан. Изображения по умолчанию берутся из папки `images`.

CSS инлайнится через Juice. Конфиг: `gmu/utils/juice_config.js`.

SVG-файлы конвертируются в PNG через `@resvg/resvg-js`, затем проходят через обработку Pillow. Это позволяет не устанавливать Cairo, GTK или системные SVG-библиотеки.

Если у изображения задан `data-width`, GMU использует его при ресайзе. GIF-файлы не ресайзятся.

## Документация API

Полезные страницы Unisender:

- [`createEmailMessage`](https://www.unisender.com/ru/support/api/messages/createemailmessage/)
- [`deleteMessage`](https://www.unisender.com/ru/support/api/messages/deletemessage/)
- [`sendTestEmail`](https://www.unisender.com/ru/support/api/messages/sendtestemail/)
- [`createCampaign`](https://www.unisender.com/ru/support/api/messages/createcampaign/)
- [`getCampaignStatus`](https://www.unisender.com/ru/support/api/statistics/getcampaignstatus/)
- [`getActualMessageVersion`](https://www.unisender.com/ru/support/api/messages/get-actual-message-version/)
- [`getWebVersion`](https://www.unisender.com/ru/support/api/messages/getwebversion/)
- [`getMessage`](https://www.unisender.com/ru/support/api/statistics/getmessage/)

## Устранение неполадок

### Не работает Unisender API

- Проверьте `UNISENDER_API_KEY`.
- Проверьте `UNISENDER_API_URL=https://api.unisender.com/ru/api/`.
- Запустите команду из папки проекта письма, где есть `gmu.json`, если команда должна брать ID из конфига.

### Не работает WebLetter

- Проверьте `WL_AUTH_TOKEN`.
- Проверьте `WL_URL` и `WL_ENDPOINT`.
- Убедитесь, что в `gmu.json` есть `webletter_id`, если команда должна обновлять или удалять существующее письмо.

### Не найден Juice

```bash
npm install
npm ls juice
npm root -g
```

Если Juice установлен в другом месте, задайте `GMU_JUICE_MODULE`.

PowerShell для текущей сессии:

```powershell
$npmRoot = npm root -g
$env:GMU_JUICE_MODULE = Join-Path $npmRoot "juice"
$env:GMU_RESVG_MODULE = Join-Path $npmRoot "@resvg\resvg-js"
```

PowerShell, чтобы сохранить пути в профиле пользователя:

```powershell
$npmRoot = npm root -g
[Environment]::SetEnvironmentVariable("GMU_JUICE_MODULE", (Join-Path $npmRoot "juice"), "User")
[Environment]::SetEnvironmentVariable("GMU_RESVG_MODULE", (Join-Path $npmRoot "@resvg\resvg-js"), "User")
```

После сохранения переменных откройте новый терминал.

### Не конвертируется SVG

```bash
npm install
npm ls @resvg/resvg-js
```

Если `@resvg/resvg-js` установлен в другом месте, задайте `GMU_RESVG_MODULE`.

### Git-автосинхронизация не сработала

- Проверьте, что текущая папка является git-репозиторием.
- Проверьте доступ к remote.
- Выполните вручную `git status`, `git pull`, `git push`.
- Если автосинхронизация не нужна, выключите ее:

```bash
gmu cfg git --disable
```

## Поддержка

При возникновении проблем создайте issue в репозитории или приложите к задаче команду, которую запускали, содержимое `gmu.json` без секретов и текст ошибки из консоли.
