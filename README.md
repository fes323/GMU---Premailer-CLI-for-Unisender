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

- Python 3.11 или новее.
- Node.js 18 или новее и npm.
- Git для установки и обновления из репозитория.

Poetry для обычной установки не нужен. Команды ниже устанавливают GMU из этого репозитория, без зависимости от публикации пакета в PyPI.

### Windows (PowerShell)

Установите [Python](https://www.python.org/downloads/windows/), [Node.js](https://nodejs.org/en/download) и [Git](https://git-scm.com/downloads/win). В установщике Python включите добавление Python в `PATH` и установку Python Launcher (`py`). Затем откройте новое окно PowerShell.

В примерах выбран Python 3.11. Если у вас другая версия, замените `py -3.11` во всех командах на соответствующую, например `py -3.12`. Посмотреть установленные версии можно командой `py --list`.

```powershell
py -3.11 --version
node --version
npm.cmd --version
git --version
```

Склонируйте репозиторий в постоянную папку и установите GMU:

```powershell
git clone https://github.com/fes323/GMU---Premailer-CLI-for-Unisender..git "$env:USERPROFILE\gmu-source"
Set-Location "$env:USERPROFILE\gmu-source"
py -3.11 -m pip install --upgrade .
npm.cmd install -g juice@11.0.1 @resvg/resvg-js@2.6.2
py -3.11 -m playwright install chromium
```

Если pip отсутствует, сначала выполните `py -3.11 -m ensurepip --upgrade`, затем повторите установку. `npm.cmd` позволяет запускать npm из PowerShell без изменения политики выполнения скриптов.

Чтобы `gmu` находился из любой директории, добавьте каталог скриптов выбранного Python в пользовательский `PATH`:

```powershell
$gmuScripts = py -3.11 -c "import sysconfig; print(sysconfig.get_path('scripts'))"
$gmuUserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (($gmuUserPath -split ';') -notcontains $gmuScripts) {
    [Environment]::SetEnvironmentVariable('Path', "$gmuScripts;$gmuUserPath", 'User')
}
$env:Path = "$gmuScripts;$env:Path"
```

Создайте пользовательский `.env` по инструкции в разделе «Настройка окружения». Затем проверьте запуск из другой папки:

```powershell
Set-Location $env:USERPROFILE
Get-Command gmu -All
gmu --version
gmu --help
npm.cmd ls -g juice @resvg/resvg-js
```

Новые окна PowerShell и CMD будут использовать сохранённый `PATH`. Если `Get-Command gmu -All` показывает несколько установок, первая должна относиться к выбранному Python. Для обновления уже установленного GMU используйте тот же Python, которым он был установлен.

### macOS (Terminal, zsh)

Установите [Homebrew](https://brew.sh/) по инструкции на сайте, включая предложенную настройку `brew shellenv`. Затем установите зависимости:

```sh
brew install python node git
python3 --version
node --version
npm --version
git --version
```

GMU устанавливается в постоянное виртуальное окружение. Активировать его перед использованием команды не потребуется:

```sh
git clone https://github.com/fes323/GMU---Premailer-CLI-for-Unisender..git "$HOME/gmu-source"
cd "$HOME/gmu-source"
python3 -m venv "$HOME/.local/share/gmu/venv"
"$HOME/.local/share/gmu/venv/bin/python" -m pip install --upgrade .
npm install -g juice@11.0.1 @resvg/resvg-js@2.6.2
"$HOME/.local/share/gmu/venv/bin/python" -m playwright install chromium
mkdir -p "$HOME/.local/bin"
ln -sfn "$HOME/.local/share/gmu/venv/bin/gmu" "$HOME/.local/bin/gmu"
```

Добавьте каталог команды в `PATH` для текущего и будущих окон Terminal:

```sh
touch "$HOME/.zprofile"
grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.zprofile" || \
  printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$HOME/.zprofile"
export PATH="$HOME/.local/bin:$PATH"
```

Эта настройка предназначена для стандартной оболочки zsh. Если используете Bash, добавьте ту же строку `export PATH` в `~/.bash_profile`.

Создайте пользовательский `.env` по инструкции ниже и проверьте запуск:

```sh
cd "$HOME"
command -v gmu
gmu --version
gmu --help
npm ls -g juice @resvg/resvg-js
```

### Обновление существующей установки

Сначала сохраните существующий полный `.env` в пользовательскую папку из раздела «Настройка окружения». Если он уже находится там, повторно создавать его не нужно. Используйте способ обновления, соответствующий вашей установке.

Windows, для установки через выбранный Python:

```powershell
Set-Location "$env:USERPROFILE\gmu-source"
git pull --ff-only
py -3.11 -m pip install --upgrade .
npm.cmd install -g juice@11.0.1 @resvg/resvg-js@2.6.2
py -3.11 -m playwright install chromium
gmu --version
```

Если исходники уже находятся в другой папке, перейдите в неё вместо `gmu-source`. Python должен совпадать с установленной командой `gmu`; путь можно проверить через `Get-Command gmu -All`.

macOS, для виртуального окружения из инструкции выше:

```sh
cd "$HOME/gmu-source"
git pull --ff-only
"$HOME/.local/share/gmu/venv/bin/python" -m pip install --upgrade .
npm install -g juice@11.0.1 @resvg/resvg-js@2.6.2
"$HOME/.local/share/gmu/venv/bin/python" -m playwright install chromium
gmu --version
```

При обновлении Playwright может потребоваться новая версия Chromium, поэтому команда установки браузера включена и в обновление. Подробнее — в [документации Playwright](https://playwright.dev/python/docs/browsers).

### Установка из wheel и разработка

Вместо установки из исходников можно установить готовый wheel. В Windows выполните `py -3.11 -m pip install --upgrade "C:\path\to\gmu-2.0.4-py3-none-any.whl"`, в macOS — `"$HOME/.local/share/gmu/venv/bin/python" -m pip install --upgrade /path/to/gmu-2.0.4-py3-none-any.whl`. Подставьте имя полученного файла. Настройка `PATH`, `.env`, установка JS-зависимостей и Chromium остаются такими же, как выше.

Для разработки в клонированном репозитории можно использовать Poetry: `poetry install`, `npm install`, `poetry run playwright install chromium`, `poetry run gmu --version`. Для сборки wheel выполните `poetry build`; результат появится в `dist/`.

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

Для запуска из любой папки храните полные настройки в пользовательском `.env`. Файл рядом с установленным пакетом имеет приоритет: при переносе убедитесь, что оба файла содержат актуальные настройки. Уже заданные переменные окружения также могут переопределять значения из `.env`.

При первой установке создайте файл из `example.env` в папке исходников. Команды ниже сохраняют уже существующий пользовательский файл.

Windows (PowerShell):

```powershell
$gmuConfigDir = Join-Path $env:APPDATA 'gmu'
New-Item -ItemType Directory -Path $gmuConfigDir -Force | Out-Null
$gmuEnvFile = Join-Path $gmuConfigDir '.env'
if (-not (Test-Path -LiteralPath $gmuEnvFile)) {
    Copy-Item -LiteralPath "$env:USERPROFILE\gmu-source\example.env" -Destination $gmuEnvFile
}
notepad $gmuEnvFile
```

macOS:

```sh
mkdir -p "$HOME/.config/gmu"
if [ ! -f "$HOME/.config/gmu/.env" ]; then
  cp "$HOME/gmu-source/example.env" "$HOME/.config/gmu/.env"
fi
chmod 600 "$HOME/.config/gmu/.env"
nano "$HOME/.config/gmu/.env"
```

Заполните ключи и адреса сервисов. Если полный `.env` уже есть в старой установке, скопируйте его в пользовательскую папку вместо шаблона. Не заменяйте заполненный файл пустым `example.env`. При другом расположении исходников исправьте путь к шаблону в командах выше.

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
- `message_creation_pending` - создание письма начато, но его результат ещё не сохранён.

Настройка `git_auto_sync` хранится отдельно для всех проектов: Windows — `%APPDATA%\gmu\settings.json`, Linux/macOS — `~/.config/gmu/settings.json`. Старое поле `settings.git_auto_sync` в проектах больше не управляет синхронизацией; включите её один раз командой `gmu cfg git --enable`.

## Команды

### Общие команды

| Команда | Коротко | Назначение |
| --- | --- | --- |
| `gmu --version` | `gmu -V` | Версия CLI |
| `gmu version` | `gmu v` | Версия CLI |
| `gmu archive` | `gmu a` | Создать ZIP-архив |
| `gmu jpeg` | `gmu jpg` | JPEG-снимок всего письма |
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

Создает ZIP-архив письма. Если `--html-filename` не указан, используется единственный `.html` в текущей папке; при нескольких файлах укажите `--html-filename`.

Пример:

```bash
gmu a --html-filename index.html --images-folder images
```

### JPEG-снимок письма

```bash
gmu jpeg
gmu jpeg --html-filename index.html --width 800
gmu jpeg --html-filename index.html --output preview/letter.jpeg --quality 95
```

Создаёт один JPEG на всю высоту письма, включая содержимое ниже первого экрана. По умолчанию используется единственный HTML-файл в текущей папке, ширина окна 1280 px, качество 95; результат сохраняется рядом с HTML как `<имя>.jpg`. Можно указать ширину 375 px для мобильного вида. Локальные пути изображений и CSS разрешаются относительно HTML. Исходники и `gmu.json` не изменяются.

Перед съёмкой GMU ждёт загрузки изображений и шрифтов; ленивые изображения также загружаются. Ошибка загрузки изображения останавливает команду, чтобы не сохранить неполный снимок.

Старый вызов `gmu pdf` совместим с этой командой и теперь создаёт JPEG. `wkhtmltopdf` и `pdfkit` для неё не нужны. Снимок использует экранный вид Chromium, без разбивки на страницы PDF.

Библиотека Playwright устанавливается вместе с GMU. GMU использует установленный Chromium, Edge или Chrome. Если браузер не найден:

```bash
playwright install chromium
```

Браузер можно выбрать явно: `gmu jpeg --browser msedge`, `--browser chrome` или `--browser chromium`.

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

`--force` заменяет существующее письмо: старое удаляется, затем создаётся новое. Для обычного обновления используйте `gmu m u`.

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

Показывает `letter_version`, глобальный `git_auto_sync`, `message_id`, `webletter_id`, `campaign_id`.

#### Git-автосинхронизация

```bash
gmu settings git
gmu settings git --enable
gmu settings git --disable
gmu cfg git --enable
```

Включение и отключение сохраняются для текущего пользователя и действуют во всех проектах. Когда глобальный `git_auto_sync=true`, после успешных команд, которые меняют письмо, кампанию или WebLetter, GMU выполняет:

```bash
git pull --ff-only
git add -- ./ ':(exclude).gmu.lock' ':(glob,exclude)**/.gmu.lock'
git commit -m "<название рабочей директории> v <letter_version>"
git push
```

Перед `git add ./` команда увеличивает `letter_version` в `gmu.json`, поэтому новая версия попадает в коммит. Если git-команда завершилась ошибкой, выполненный деплой не откатывается.

Файлы `.gmu.lock` исключаются из автосинхронизации независимо от `.gitignore` репозитория письма. Это предотвращает ошибку индексации активной блокировки на Windows.

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

После успешной загрузки GMU выполнит `git pull --ff-only`, увеличит `letter_version`, сделает `git add ./`, создаст коммит вида `my-letter v 2` и выполнит `git push`.

### Ручная проверка актуальной версии письма

```bash
gmu m act
gmu c c --start-time "2026-05-04 10:00"
```

## Обработка HTML и изображений

GMU выбирает единственный HTML-файл в текущей папке, если `--html-filename` не указан. Если файлов несколько, нужно указать файл явно. Тема из `<title>` и прехедер сохраняются одной строкой: переносы и отступы форматтера заменяются пробелами. Внешние URL изображений сохраняются; отсутствие локального изображения останавливает обработку до удаления старого письма. Изображения по умолчанию берутся из папки `images`.

В итоговом HTML для Unisender, архивов и WebLetter тема записывается как `<title>Тема письма</title>` без атрибутов и переносов, а прехедер — как `<div style="display:none;max-height:0px;overflow:hidden">Текст прехедера</div>`. Это формат, который распознаёт [WebLetter API](https://github.com/fes323/webletter-api/blob/main/src/services/file.service.ts). Прехедер берётся из первого скрытого `div` с непустым текстом; его вложенная разметка заменяется текстом, дополнительные стили и атрибуты сохраняются во внешнем скрытом блоке. Нормализация выполняется после CSS-инлайнинга, исходный HTML-файл не изменяется. Отсутствующие тему и прехедер GMU не добавляет.

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

### Прервалось создание письма

GMU сохраняет конфиг без запроса на его перезапись и блокирует одновременные изменения в одной папке. `--force` не пропускает удаление старого письма.

При таймауте, некорректном ответе или ошибке сохранения ID повторное создание блокируется через `message_creation_pending`: сервер мог успеть создать письмо. Проверьте кабинет Unisender. Если письмо создано, восстановите привязку:

```bash
gmu m info --id 123456789 --save
```

Если убедились, что письмо не создано, установите `message_creation_pending=false` в `gmu.json` и повторите `gmu m u`. После явного отказа API блокировка снимается автоматически.

Обновление с вложениями всё ещё выполняется удалением и созданием: локальная проверка происходит до удаления, но при отказе сервера создать новое письмо старое уже может быть удалено. GMU очищает его ID, чтобы следующий запуск не пытался удалить его снова.

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
