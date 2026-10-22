# Итоговый отчёт Ethereum/EVM

<!-- SEPOLIA_TASK4_START -->
## Task 4: подтверждённое выполнение в Ethereum Sepolia

Проверено через read-only RPC `https://ethereum-sepolia-rpc.publicnode.com`: 2026-10-22T12:53:49.670911+00:00. Chain ID: **11155111**.

Контракт: **`0x423e0fd91d46055cff2d5d1cac7c1a9b88fe6cdb`** — [Sepolia Etherscan](https://sepolia.etherscan.io/address/0x423e0fd91d46055cff2d5d1cac7c1a9b88fe6cdb).

Владелец: `0xfCB373793743A9bce32394EED450CEdfa7B10655`. Токен: **Vmk Rulit Token / VMKRULIT**, decimals **18**.
Выпущено **1 VMKRULIT** (10^18 единиц), переведено **1 VMKRULIT** на `0x4a097d48ef380b479773eb609511a49cf17020f4`.

| Операция | Transaction hash | Блок | Etherscan |
| --- | --- | --- | --- |
| deploy | `0xc288b4ebc4f6ce8f11e896e4702c37869058cfdbb7c2b96283cb80e06914fe4e` | 11969622 | [Success](https://sepolia.etherscan.io/tx/0xc288b4ebc4f6ce8f11e896e4702c37869058cfdbb7c2b96283cb80e06914fe4e) |
| mint | `0x7d9dc2f1b2e5eda87aff7efd235e9ccd5c6ec74e3879fe088812a677ba1a9c61` | 11969646 | [Success](https://sepolia.etherscan.io/tx/0x7d9dc2f1b2e5eda87aff7efd235e9ccd5c6ec74e3879fe088812a677ba1a9c61) |
| transfer | `0x68315222299c67e4b06e8dec607b0b8bf4abcd7c99c221d05ead485d9f28808c` | 11969663 | [Success](https://sepolia.etherscan.io/tx/0x68315222299c67e4b06e8dec607b0b8bf4abcd7c99c221d05ead485d9f28808c) |

На блоке 11969665: totalSupply = `1000000000000000000`, balanceOf(получатель) = `1000000000000000000`, balanceOf(owner) = `0`.
Проверены status=1, канонические блоки, минимум 2 подтверждения, точные calldata, отправитель, сеть, нулевой ETH value, события mint/transfer и runtime bytecode с immutable owner.
Подпись — существующий MetaMask, по отдельному подтверждению пользователя для каждой операции.
Доказательства: `task4/sepolia_result.json`; Foundry: `checks/task4_final_foundry.log` (23 PASS).
Task 3 также подтверждён: [0xe0e9be26f386c5c1b6ccad6408b0af754c33b8c5937d21dc9700aecefb86532f](https://sepolia.etherscan.io/tx/0xe0e9be26f386c5c1b6ccad6408b0af754c33b8c5937d21dc9700aecefb86532f), блок 11969425, status=1.
SHA-256 исходников/конфига: `5c049cea7924c22e4d7b6b2bb2703d71bd61ecd6c82dfd724a57385d693e1dc1`.
<!-- SEPOLIA_TASK4_END -->

## Архив ранней локальной проверки

**Ниже сохранён исторический отчёт до установки инструментов и предоставления Task 3 hash.
Его сообщения BLOCKED, «не отправлено» и запрет выполнения агентом описывают прежний этап.
Текущий статус и согласованный пользователем процесс приведены выше.**

Дата локальной проверки: **2026-10-22**. Имя: **TEST1337**.
Работа возвращена к **первоначальному заданию**: локальная реализация и доступные тесты;
публичные сети, MetaMask и faucet — только ручные инструкции, без выполнения агентом.
Невыполненные Foundry-проверки и ручная часть явно отделены от готового локального решения.

## Сводная таблица

| Задание | Статус | Реальные результаты | Transaction hash / contract address | Block number | Etherscan | Результаты тестов | Что осталось вручную / после разблокировки |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Локальное решение готово; полноценная EVM-проверка ожидает инструменты | `program.evm`, 139 байт, только mnemonic opcodes; signed average и REVERT | Не применимо | Не применимо | Не применимо | 4 Python-метода: 29 фиксированных случаев, 1000 случайных, операнды/переходы/стек; PASS. Проверка ассемблера PASS | Запустить Cancun Playground либо 5 подготовленных Foundry-тестов, показать результат и пустой стек |
| 2 | Инструкции и шаблон готовы; сеть оставлена пользователю | Инструкции encrypted keystore/MetaMask/Sepolia/faucet, RPC-планировщик и проверка receipt | **Нет** | **Нет** | **Нет реальной ссылки** | 8 unit-тестов RPC-утилиты с синтетическими данными: PASS | Самостоятельно создать кошелёк, включить Sepolia, получить ETH, узнать адрес коллеги и отправить перевод; проверить RPC/Etherscan |
| 3 | Код и тесты готовы; отправка только вручную | UTF-8/hex encoder/decoder, имя TEST1337 и шаблон сообщения | **Нет** | **Нет** | **Нет реальной ссылки** | 9 Python-методов: PASS | Получить настоящий Task 2 hash и адрес отправителя; сформировать message.txt/hex; самостоятельно отправить и проверить receipt/Input Data |
| 4 | Исходники и сценарии готовы; Foundry недоступен, Sepolia только вручную | Полный учебный ERC20 Vmk Rulit Token / VMKRULIT, decimals=18; 18 тестов, deploy script, Anvil-сценарий | **Контракт не развёрнут; hash нет** | **Нет** | **Нет реальной ссылки** | Foundry и solc отсутствуют: BLOCKED, не запускались. PowerShell parse PASS; импорты/артефакты проверены | Установить бинарники, выполнить Foundry и Anvil; самостоятельно deploy/mint/transfer в Sepolia, проверить receipts и balanceOf >= 10^18 |

## Task 1: что реализовано и создано

`task1/program.evm`, `program.hex`, `program.bin`, `README.md`, `test_cases.md`, `test_vectors.json`,
`build_program.mjs`, `local_evm.py`, `test_program.py`.
`task4/test/AverageProgram.t.sol` подготовлен для независимого запуска байткода Foundry.

Вход: N и ровно N int256-слов; N > 0. Суммирование циклом, округление среднего к нулю,
отрицательные/положительные/нулевые значения, проверка каждого промежуточного signed
overflow, строгая длина calldata, пустой стек на RETURN/REVERT. Проверка длины не умножает
N и не позволяет обойти валидацию через переполнение размера.

Реально проверено: все перечисленные в исходном задании случаи, крайние int256,
лишний/недостающий байт, overflow и попытка оборачивания длины; 1000 случайных примеров
с фиксированным seed. Это **ограниченная локальная модель инструкций**, без gas/world state,
а не выполненная проверка в полной Cancun EVM. Playground не запускался.

Преподавателю: `program.evm`, формат calldata, воспроизводимые векторы, результаты
положительного/отрицательного среднего, REVERT при плохом вводе и пустой стек.

## Task 2: что реализовано и создано

`task2/README.md`, `report_template.md`, `sepolia_rpc.py`, `test_sepolia_rpc.py`.
Подготовлены установка официального MetaMask, создание encrypted keystore локально,
импорт JSON без раскрытия приватного ключа, Sepolia, faucet, перевод, поиск блока.

RPC-инструмент разрешает только чтение: guard Sepolia, estimateGas, fee budget,
проверка receipt/canonical block/подтверждений, balanceOf. Unit-тесты используют
явно синтетические данные; их hash не являются сетевыми доказательствами.

Преподавателю после выполнения: публичные адреса, Success hash, настоящий номер блока,
RPC receipt, страницы транзакции и блока в Sepolia Etherscan. Сейчас их нет.

## Task 3: что реализовано и создано

`task3/encode_message.py`, `test_encode_message.py`, `message_template.txt`, `README.md`.
Поддерживаются CLI-поля имени/адреса/hash, UTF-8 → hex с `0x`, обратное декодирование,
проверка синтаксиса и ненулевых адреса/hash, ошибок UTF-8/hex/управляющих символов.
Проверка EIP-55 checksum и реальности hash не имитируется: существование hash проверяет RPC.

Имя уточнено: TEST1337. Адрес и Task 2 hash остаются placeholders.
Реальные `message.txt`, `message.hex`, receipt, hash и block number ещё не созданы.

Преподавателю после отправки: message и hex, ненулевой Value, реальный Task 2 hash внутри
сообщения, успешный Task 3 receipt, Input Data в Etherscan.

## Task 4: что реализовано и создано

`task4/src/IERC20.sol`, `src/LabToken.sol`, `foundry.toml`, `test/LabToken.t.sol`,
`test/AverageProgram.t.sol`, `script/Deploy.s.sol`, `scripts/local_demo.ps1`, `README.md`.

Стандарт ERC20 представлен всеми шестью методами, событиями Transfer/Approval;
есть метаданные, owner-only mint, 18 decimals, totalSupply/balanceOf, approve/allowance,
transfer/transferFrom, нулевые/self-переводы и atomic revert. Это собственная учебная
реализация стандарта, без имитаций недоступных внешних библиотек.
Обзор исходника и наличие интерфейса **не заменяют компиляцию и runtime-проверку**.

Подготовлены 18 Foundry-тестов контракта и 5 Task 1 EVM-тестов, два fuzz-теста по 256
запусков. Они **не выполнялись**: forge/solc отсутствуют. Anvil также не запускался.
Не создавались реальные локальные deployment-результаты или сетевые receipts.

Преподавателю после выполнения: вывод `forge test`, локальный Anvil-result, исходник,
name/symbol/decimals, настоящий Sepolia contract address, deployment/mint/transfer hashes,
Transfer event на заданный адрес и balanceOf >= 1000000000000000000.

## Реально выполненные проверки и ограничения среды

### Повторный автоматический запуск установки и локальных проверок

По запросу пользователя выполнен `run_local.ps1`, а не только подготовлены инструкции.
Он автоматически запустил установщик из официальных источников, `verify.ps1` и Anvil-сценарий.
Последний запуск: **2026-10-22 09:56 UTC**. Итоговый exit code **2**, есть заблокированные этапы.

| Этап | Фактический результат | Доказательство |
| --- | --- | --- |
| Foundry v1.8.6, официальный GitHub release API | BLOCKED: curl exit 7, подключение не состоялось; архив не скачан, forge/cast/anvil не установлены | `checks/install.log`, `checks/install_results.json` |
| Solc 0.8.28, официальный binaries.soliditylang.org | BLOCKED: curl exit 7; компилятор не скачан и не установлен | `checks/install.log`, `checks/install_results.json` |
| Git Bash | Та же ошибка подключения к GitHub; смена shell не помогла | Проверено реальным вызовом Git Bash curl |
| WSL | `Wsl/EnumerateDistros/Service/E_ACCESSDENIED`; дистрибутив недоступен агенту | Проверено `wsl.exe --list --quiet` |
| Task 1 offline | PASS: 29 фиксированных случаев, 1000 случайных, порядок операндов, переходы и стек | `checks/task1.log` |
| Task 3 Python | PASS: 9 тестовых методов | `checks/task3.log` |
| Task 2 read-only RPC unit tests | PASS: 8 методов с синтетическими данными | `checks/task2_rpc_unit.log` |
| Артефакты и mnemonic assembler | PASS: 19 обязательных файлов, соответствие mnemonic/hex/binary, 29 векторов, локальные импорты | `checks/artifacts.log`, `checks/assembler.log` |
| PowerShell | PASS: синтаксис четырёх сценариев | `checks/powershell_parse.log` |
| Foundry Solidity/EVM tests | BLOCKED, не выполнялись | `checks/foundry.log` |
| Anvil deployment/mint/transfer | Сценарий запускался, exit 1 из-за отсутствия forge; сам Anvil не запущен, локальных транзакций нет | `checks/anvil_attempt.log` |

Среда явно задаёт `CODEX_SANDBOX_NETWORK_DISABLED=1`; изменить ограничение сети
агенту не разрешено. Git Bash не меняет доступность сети, WSL также недоступен.
Загрузка и исполнение непроверенных альтернатив не использовались.

Добавлены `.tools/install.ps1` и `run_local.ps1`: после появления сетевого доступа
весь процесс запускается одной командой, без ручного скачивания отдельных EXE.
Установщик проверяет SHA-256 официальных артефактов перед запуском; в текущей попытке
этот этап не достигнут, поскольку загрузки не состоялись.
Общая сводка — `checks/local_run.json`, подробности тестов — `checks/results.json`.

Исправлено чтение fixture Task 1: Foundry-тест теперь загружает точные 139 байт
`program.bin` через `readFileBinary`, без зависимости от перевода строки в hex-тексте.
`verify.ps1` запускает Foundry из каталога task4 и проверяет соответствие бинарника
mnemonic-программе. Это проверенные изменения файлов; прохождение самих Foundry-тестов
пока не подтверждено.

### Остальные выполненные действия

- Найдены Node.js v24.18.0 и Python 3.12.14 в локальном runtime.
- Обнаружено отсутствие forge/cast/anvil/solc и Ethereum Python-библиотек.
- Попытка локальной установки npm-зависимостей завершилась сетевым `EACCES`;
  процесс остановлен, зависимости не установлены.
- Прямой HTTPS к официальным релизам Foundry и публичному Sepolia RPC не подключается.
- Все Python-тесты и проверка воспроизводимости mnemonic-программы действительно запущены.
- Синтаксис PowerShell-сценариев проверен встроенным парсером; это не исполнение Anvil.
- Попытка Anvil-сценария корректно остановилась на отсутствии forge до запуска сети.
- Проверен браузерный fallback: подключённых браузеров нет, Playground не запускался.
- Проверена структура обязательных файлов, bytecode/векторы и локальные Solidity imports.
- Повторяемые результаты: `checks/results.json` и логи `checks/*.log`.
- `verify.ps1` завершает работу с кодом **2**, пока Foundry BLOCKED; этот код не означает,
  что Foundry-тесты прошли. Вспомогательный `verify_artifacts.py` не компилирует Solidity.

## Что действительно выполнено в сети

**Ни одной Ethereum-транзакции не отправлено.** Не создан тестовый кошелёк,
не запрашивались faucet ETH, не выполнялись deployment/mint/transfer.
Реальных адресов контрактов, hash, block numbers и Etherscan-подтверждений нет.
Через интернет читалась только публичная документация; исходники, отчёт и персональные
реквизиты во внешние сервисы не загружались. Git push и PR не выполнялись.

## Что остаётся сделать вручную

1. Для недоступной агенту установки достаточно запустить в обычном терминале VS Code
   с доступом к сети одну команду: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_local.ps1`.
   Она сама скачивает инструменты в проект и запускает все локальные проверки.
   Ручное скачивание каждого EXE не требуется; детали — [.tools/README.md](.tools/README.md).
2. Самостоятельно создать отдельный тестовый аккаунт в официальном MetaMask и включить Sepolia.
   При выборе Cast вместо этого можно создать encrypted keystore по инструкции Task 2.
3. Пройти CAPTCHA/вход faucet, если требуются, получить test ETH на отдельный адрес.
   Seed/private key/пароль не передавать в чат или отчёт.
4. Узнать у коллеги адрес. Самостоятельно выполнить публичные операции по инструкциям,
   сохраняя только настоящие receipts, hash и block numbers.
5. Обновить таблицу отчёта реальными данными. Публичные операции не входят в действия агента.
