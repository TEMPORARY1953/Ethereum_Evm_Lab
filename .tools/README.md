# Автоматическая установка и локальная проверка на Windows

Все инструменты устанавливаются **внутри этого проекта**, в `.tools/bin/`.
Ручное скачивание отдельных EXE, глобальная установка, изменение PATH, Git Bash и WSL
не требуются. Используются официальные Windows x64 binaries.

## Одна команда для всех этапов

Из корня проекта:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_local.ps1
```

Она выполняет `.tools/install.ps1`, `verify.ps1` и `task4/scripts/local_demo.ps1`.
Даже если установка заблокирована, доступные Python-тесты выполняются, а недоступные
этапы получают статус BLOCKED. Публичные транзакции не отправляются.
ExecutionPolicy задаётся только дочернему процессу; системная настройка не меняется.

Только установка:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\.tools\install.ps1
```

Установщик скачивает:

- Forge, Cast, Anvil из [официального Foundry v1.8.6](https://github.com/foundry-rs/foundry/releases/tag/v1.8.6).
  Архив выбирается через GitHub API, SHA-256 сравнивается с digest release asset.
- Solc **0.8.28+commit.7893614a** из [официального Solidity binary repository](https://binaries.soliditylang.org/windows-amd64/list.json).
  SHA-256: `76a71001309810aafd0462d9b2f2612bf19b89550c866140edca26e533de06bc`.

Бинарники запускаются после проверки SHA-256. Архивы и metadata сохраняются в
`.tools/downloads/`; результат установки — `checks/install_results.json`.
Если загрузка не состоялась, проверка файла и запуск версии не объявляются выполненными.
Вывод и коды этапов — в `checks/local_run.json` и `checks/*.log`.

## Фактический результат в среде агента

Установщик **действительно запускался**, но обе загрузки заблокированы:
`CODEX_SANDBOX_NETWORK_DISABLED=1`, `curl exit 7 / Could not connect to server`.
Git Bash имеет такую же ошибку сети, WSL сообщает `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`.
Это ограничение среды выполнения, а не несовместимость Foundry с PowerShell.
У агента нет разрешённого способа изменить эту настройку sandbox.

При доступе к сети в обычном терминале VS Code достаточно одной команды выше.
Ручное скачивание каждого EXE не требуется. Текущая установка **не состоялась**.

## Проверки отдельно

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\verify.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\task4\scripts\local_demo.ps1
```

`foundry.toml` использует локальный `solc.exe`, Cancun и `offline = true`.
Проект самодостаточен; OpenZeppelin и forge-std устанавливать не требуется.
Python доступен через runtime Codex; можно указать `verify.ps1 -PythonPath 'ПУТЬ_К_PYTHON_EXE'`.
