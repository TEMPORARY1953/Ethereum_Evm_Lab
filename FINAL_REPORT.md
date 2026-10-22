# Итоговый отчёт Ethereum/EVM — Task 1–4

Финальная проверка: **2026-10-22T12:57:57.398143+00:00**. Сеть: **Ethereum Sepolia**, chain ID **11155111**.
RPC: `https://ethereum-sepolia-rpc.publicnode.com`. Адрес пользователя: `0xfcb373793743a9bce32394eed450cedfa7b10655`.

Во время этой проверки использовались только read-only RPC и локальные тесты EVM/unit tests.
Новых транзакций не отправлено, смарт-контракт не изменён, публикаций не было.
Сервер подписи остановлен. Сырые доказательства: [final_sepolia_audit.json](checks/final_sepolia_audit.json).

## Итоговая таблица

| Задание | Выполнено и проверено | Статус | Что осталось для сдачи |
| --- | --- | --- | --- |
| Task 1 — среднее на EVM opcodes | 139 байт mnemonic-only, signed average, округление к нулю, валидация calldata и REVERT, 29 векторов + 1000 случайных случаев; 5 Foundry-тестов в Cancun PASS | Частично: код и тесты готовы, обязательный Playground Cancun не подтверждён | Запустить program.evm именно в EVM Codes Playground с Cancun, проверить возврат результата и пустой стек. Скриншот условием не требуется |
| Task 2 — кошелёк / Sepolia ETH | Успешный реальный перевод 0.0001 ETH на `0x9894a382ab5fd80f0505f00b4f13997d8111d7af`, receipt и блок подтверждены RPC; Etherscan-ссылки указаны | Сетевая часть выполнена; ручные шаги независимо не проверены | Убедиться, что выполнены создание нового MetaMask-кошелька, faucet, перевод именно коллеге и просмотр блока в Etherscan. Сами скриншоты в задании не требуются |
| Task 3 — сообщение в Input Data | Success, ненулевой Value, точное UTF-8-сообщение с именем Lysak Vladimir, адресом и настоящим успешным Task 2 hash; правильный адрес получателя | Onchain-требования выполнены | Новая транзакция не требуется. Условие требует собственное имя; TEST1337 из старых примеров не является требованием задания |
| Task 4 — ERC20 | Vmk Rulit Token / VMKRULIT, 18 decimals; deploy, mint и transfer подтверждены; у получателя ровно 1 токен; 18 ERC20-тестов PASS | Функциональные onchain-требования выполнены; оговорка о deployment-инструменте | Foundry использован для сборки/симуляции, broadcast выполнен страницей MetaMask. Прямой deployment через forge --broadcast или Remix не выполнялся; при буквальной оценке этого пункта соответствие способа развёртывания не подтверждено |

Проверка уточнена по полному оригинальному условию, предоставленному пользователем:
[ORIGINAL_ASSIGNMENT.md](ORIGINAL_ASSIGNMENT.md). Скриншоты, фиксированная сумма ETH,
имя TEST1337, верификация исходников в explorer и публикация GitHub условием не требуются.
Для Task 1 сайт EVM Codes Playground и Cancun указаны прямо и являются обязательными.

## Task 1: EVM-программа

Сдаваемый исходник: [program.evm](task1/program.evm), 139 байт; без Solidity/Yul/макросов/меток.
Calldata: `[N:32 bytes][x0:32 bytes]...[x(N-1):32 bytes]`, слова int256, N > 0.
Возврат: 32-байтовое среднее, SDIV округляет к нулю. Некорректная длина, N <= 0 и
переполнение промежуточной суммы вызывают пустой REVERT. Время выполнения линейно по N.

Проверено:

- Python: 4 метода, 29 фиксированных случаев и 1000 случайных последовательностей;
  RETURN/REVERT, пустой стек, глубина <= 3, порядок операндов и переходы — PASS.
- Реальная локальная EVM Foundry с `evm_version = cancun`: 5 тестов PASS,
  включая fuzz из 256 примеров. Тесты исполняют точные 139 байт `program.bin` через staticcall.
- Ассемблер: mnemonic/hex/binary согласованы; JUMPDEST на 54, 122, 135 — PASS.

Пустой стек проверен локальным интерпретатором и разбором программы; Foundry-тесты
проверяют успешность вызова и возвращённые данные, а не UI-снимок стека Playground.
При последовательности `[MAX_INT256, 1, -1]` программа отклоняет промежуточное переполнение,
хотя итоговая математическая сумма помещается в int256. Этот предел явно описан в README.

Примеры и ожидаемые результаты: [test_cases.md](task1/test_cases.md).
Логи: [task1.log](checks/task1.log), [foundry.log](checks/foundry.log), [assembler.log](checks/assembler.log).
Проверка именно в Playground не выполнена: список доступных управляемых браузеров пуст,
попытка открытия вкладки вернула `Browser is not available: iab`. Web-чтение страницы не
равнозначно запуску программы в её UI. Этот пункт Task 1 остаётся незавершённым;
скриншоты как самостоятельное требование не добавляются.

## Task 2: реальная ETH-транзакция

| Поле | Проверенное значение |
| --- | --- |
| From | `0xfcb373793743a9bce32394eed450cedfa7b10655` |
| To | `0x9894a382ab5fd80f0505f00b4f13997d8111d7af` |
| ETH Value | **0.0001 ETH** (`100000000000000` wei) |
| Input Data | `0x` |
| Transaction hash | `0xf86608a3986288170806e2ab87f3bde134a4137071b745155f349ca966d53f46` |
| Статус | Success, canonical block, 383 подтверждений на момент проверки |
| Блок | [11969303](https://sepolia.etherscan.io/block/11969303) |
| Block hash | `0x05a238c793c5de2f3e8e30bb0e4fcb9cf8fd1f1935ada6bd33ac9db9ff095148` |
| Gas used | 204600 |
| Фактическая комиссия | 0.0003069000034782 ETH |
| Транзакция в explorer | [Sepolia Etherscan](https://sepolia.etherscan.io/tx/0xf86608a3986288170806e2ab87f3bde134a4137071b745155f349ca966d53f46) |
| RPC evidence | [receipt.json](task2/receipt.json) |

Существование и использование адреса для подписи подтверждаются транзакциями.
История создания кошелька, происхождение faucet ETH и личность владельца To не выводятся
из одного receipt; отдельные подтверждения этих пунктов не найдены. Приватные данные не запрашивались.

## Task 3: реальное Input Data

Hash: `0xe0e9be26f386c5c1b6ccad6408b0af754c33b8c5937d21dc9700aecefb86532f` — [Success в Sepolia Etherscan](https://sepolia.etherscan.io/tx/0xe0e9be26f386c5c1b6ccad6408b0af754c33b8c5937d21dc9700aecefb86532f).
Блок: [11969425](https://sepolia.etherscan.io/block/11969425);
block hash: `0x0239f47a34b058efb9e4d35323fb02a11af6e78a067b91dc48d2fd723367dc2c`; подтверждений: **261**.
From: `0xfcb373793743a9bce32394eed450cedfa7b10655`; To: `0x4a097d48ef380b479773eb609511a49cf17020f4`;
Value: **0.00001 ETH** (`10000000000000` wei).

Input Data декодируется из hex в UTF-8 строго в следующий текст:

```text
Name: Lysak Vladimir
Ethereum address: 0xfCB373793743A9bce32394EED450CEdfa7B10655
Task 2 transaction hash: 0xf86608a3986288170806e2ab87f3bde134a4137071b745155f349ca966d53f46
```

Проверены точное обратное кодирование UTF-8 → hex, совпадение адреса сообщения с From,
настоящий Task 2 hash, его успешный receipt и более ранний блок. Это не placeholder.
Величина Value ненулевая; отличия от примерной суммы в README сами по себе не являются ошибкой.

Реальные файлы восстановлены из RPC без повторной отправки:
[message.txt](task3/message.txt), [message.hex](task3/message.hex), [receipt.json](task3/receipt.json).
Лог 9 unit-тестов encoder/decoder: [task3.log](checks/task3.log).
Исходное условие требует имя пользователя, без фиксированного текста. Сообщение содержит
`Lysak Vladimir`; пример `TEST1337` из старых файлов не является критерием оценки и не
создаёт причины для повторной отправки. Содержимое сообщения соответствует трём требуемым полям.

<!-- SEPOLIA_TASK4_START -->
## Task 4: ERC20 в Sepolia

Контракт: **`0x423e0fd91d46055cff2d5d1cac7c1a9b88fe6cdb`** — [Sepolia Etherscan](https://sepolia.etherscan.io/address/0x423e0fd91d46055cff2d5d1cac7c1a9b88fe6cdb).
Name: **Vmk Rulit Token**, symbol: **VMKRULIT**, decimals: **18**.
Owner: `0xfcb373793743a9bce32394eed450cedfa7b10655`. Получатель: `0x4a097d48ef380b479773eb609511a49cf17020f4`.
Существующая логика `task4/src/LabToken.sol` не изменена; используются параметры конструктора.

| Операция | Transaction hash | Блок | Подтверждения | Etherscan |
| --- | --- | --- | --- | --- |
| Deploy | `0xc288b4ebc4f6ce8f11e896e4702c37869058cfdbb7c2b96283cb80e06914fe4e` | 11969622 | 64 | [Success](https://sepolia.etherscan.io/tx/0xc288b4ebc4f6ce8f11e896e4702c37869058cfdbb7c2b96283cb80e06914fe4e) |
| Mint: 1 VMKRULIT владельцу | `0x7d9dc2f1b2e5eda87aff7efd235e9ccd5c6ec74e3879fe088812a677ba1a9c61` | 11969646 | 40 | [Success](https://sepolia.etherscan.io/tx/0x7d9dc2f1b2e5eda87aff7efd235e9ccd5c6ec74e3879fe088812a677ba1a9c61) |
| Transfer: 1 VMKRULIT получателю | `0x68315222299c67e4b06e8dec607b0b8bf4abcd7c99c221d05ead485d9f28808c` | 11969663 | 24 | [Success](https://sepolia.etherscan.io/tx/0x68315222299c67e4b06e8dec607b0b8bf4abcd7c99c221d05ead485d9f28808c) |

Для всех трёх транзакций подтверждены status=1, канонический блок, From, Sepolia chain ID,
нулевой ETH Value и точный Input Data. Deployment совпадает с подготовленным байткодом;
runtime проверен с подстановкой immutable owner. Для mint/transfer проверены события Transfer
с точными адресами и количеством `1000000000000000000`, а не минимальной единицей токена.
На блоке mint баланс владельца и totalSupply равнялись 10^18. Никаких дополнительных approve не было.

Состояние на одном блоке **11969686**:

| Метод | Результат |
| --- | --- |
| totalSupply() | `1000000000000000000` = 1 VMKRULIT |
| balanceOf(получатель) | `1000000000000000000` = **1 VMKRULIT** |
| balanceOf(owner) | `0` |

18 тестов ERC20 (метаданные, mint, события, балансы, transfer, allowance/transferFrom,
нулевые адреса, атомарность revert, overflow, self/zero-transfer и fuzz) — PASS.
Подпись существующих сетевых транзакций выполнялась через MetaMask пользователем.
Инструменты процесса: `forge build`, `forge test`, ABI-encoding через `cast`,
симуляция `forge script` без broadcast; затем подписанный deployment подготовленного
Foundry-байткода через `eth_sendTransaction` локальной страницы MetaMask.
Сам `forge --broadcast` и Remix IDE для отправки не использовались. Это оговорка для
буквальной проверки требования «Deploy ... using Foundry or Remix IDE»; по данным сети
и тестам сам ERC20, его персонализация, выпуск и перевод корректны. Повторный deployment
для устранения этой оговорки в рамках read-only проверки не выполнялся.
Сырые receipts: [sepolia_result.json](task4/sepolia_result.json);
повторная независимая RPC-проверка: [final_sepolia_audit.json](checks/final_sepolia_audit.json).
<!-- SEPOLIA_TASK4_END -->

## Итог тестов и полнота отчёта

`verify.ps1` повторно завершился с кодом **0**:

| Набор | Результат |
| --- | --- |
| PowerShell syntax | 4 сценария PASS |
| Task 1 Python | 4 метода PASS: 29 фиксированных + 1000 случайных случаев |
| Task 2 RPC unit tests | 8 методов PASS, синтетические данные используются только в тестах |
| Task 3 encoder/decoder | 9 методов PASS |
| Артефакты / assembler | PASS, 19 обязательных файлов и 29 векторов |
| Foundry | **23 PASS**, 0 failed: 5 Task 1 + 18 ERC20; 2 fuzz-теста по 256 примеров |
| UI без реального кошелька/сети | PASS: ограничения account/chain, preview, запрет повторов и обработка отказа |
| Сеть | 5 существующих транзакций Task 2–4 повторно подтверждены read-only RPC |

Сводка: [results.json](checks/results.json). Актуальный Foundry-лог: [foundry.log](checks/foundry.log).
Исправлена ошибка только в `verify_artifacts.py`: каталоги Foundry с суффиксом `.sol` больше
не принимаются за исходные файлы. Контракт и его интерфейс не изменены; SHA-256 до/после
совпадают и записаны в `checks/final_sepolia_audit.json`.

До этой проверки отчёт содержал актуальный Task 4 и противоречащую ему старую сводку
«Foundry недоступен / транзакций нет». Она вынесена в
[архив предыдущего отчёта](checks/FINAL_REPORT_before_final_audit.md).
Текущий отчёт содержит все реальные hashes, адрес контракта, блоки, ссылки, Input Data,
token balances и тесты. Старые README/шаблоны могут содержать исторические placeholders;
для текущего статуса использовать этот отчёт и сохранённые RPC evidence.

Остаток по исходному заданию: обязательный запуск Task 1 в Playground Cancun;
для Task 2 — сверить выполненные ручные действия MetaMask/faucet/коллега/Etherscan;
для Task 4 — учесть описанный гибридный способ отправки при оценке требования Foundry/Remix.
Task 3 исправления сообщения не требует. Скриншоты и публикации не являются обязательными.
Новых транзакций при уточнении отчёта не отправлено, контракт не изменён.
