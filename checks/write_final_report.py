"""Build the local submission report from saved read-only audit evidence."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
evidence = json.loads((ROOT / "checks/final_sepolia_audit.json").read_text(encoding="utf-8"))
checks = json.loads((ROOT / "checks/results.json").read_text(encoding="utf-8-sig"))
assert all(c["status"] == "PASS" for c in checks)
assert evidence["contractsSha256Before"] == evidence["contractsSha256After"]
for relative, digest in evidence["contractsSha256Before"].items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
task2, task3 = evidence["task2"], evidence["task3"]
task4 = evidence["task4"]
token = task4["token"]
path = ROOT / "FINAL_REPORT.md"
archive = ROOT / "checks/FINAL_REPORT_before_final_audit.md"
if not archive.exists():
    archive.write_bytes(path.read_bytes())


def eth(value):
    return format(Decimal(value) / Decimal(10**18), "f")


def row(label, item):
    return (f"| {label} | `{item['tx_hash']}` | {item['block_number']} | "
            f"{item['confirmations']} | [Success]({item['etherscan']}) |")


text = f"""# Итоговый отчёт Ethereum/EVM — Task 1–4

Финальная проверка: **{evidence['verifiedAt']}**. Сеть: **Ethereum Sepolia**, chain ID **11155111**.
RPC: `{evidence['rpc']}`. Адрес пользователя: `{task2['from']}`.

Во время этой проверки использовались только read-only RPC и локальные тесты EVM/unit tests.
Новых транзакций не отправлено, смарт-контракт не изменён, публикаций не было.
Сервер подписи остановлен. Сырые доказательства: [final_sepolia_audit.json](checks/final_sepolia_audit.json).

## Итоговая таблица

| Задание | Выполнено и проверено | Статус | Что осталось для сдачи |
| --- | --- | --- | --- |
| Task 1 — среднее на EVM opcodes | 139 байт mnemonic-only, signed average, округление к нулю, валидация calldata и REVERT, 29 векторов + 1000 случайных случаев; 5 Foundry-тестов в Cancun PASS | Частично: код и тесты готовы, обязательный Playground Cancun не подтверждён | Запустить program.evm именно в EVM Codes Playground с Cancun, проверить возврат результата и пустой стек. Скриншот условием не требуется |
| Task 2 — кошелёк / Sepolia ETH | Успешный реальный перевод {eth(task2['value_wei'])} ETH на `{task2['to']}`, receipt и блок подтверждены RPC; Etherscan-ссылки указаны | Сетевая часть выполнена; ручные шаги независимо не проверены | Убедиться, что выполнены создание нового MetaMask-кошелька, faucet, перевод именно коллеге и просмотр блока в Etherscan. Сами скриншоты в задании не требуются |
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
| From | `{task2['from']}` |
| To | `{task2['to']}` |
| ETH Value | **{eth(task2['value_wei'])} ETH** (`{task2['value_wei']}` wei) |
| Input Data | `{task2['input_data']}` |
| Transaction hash | `{task2['tx_hash']}` |
| Статус | Success, canonical block, {task2['confirmations']} подтверждений на момент проверки |
| Блок | [{task2['block_number']}](https://sepolia.etherscan.io/block/{task2['block_number']}) |
| Block hash | `{task2['block_hash']}` |
| Gas used | {task2['gas_used']} |
| Фактическая комиссия | {eth(task2['actual_fee_wei'])} ETH |
| Транзакция в explorer | [Sepolia Etherscan]({task2['etherscan']}) |
| RPC evidence | [receipt.json](task2/receipt.json) |

Существование и использование адреса для подписи подтверждаются транзакциями.
История создания кошелька, происхождение faucet ETH и личность владельца To не выводятся
из одного receipt; отдельные подтверждения этих пунктов не найдены. Приватные данные не запрашивались.

## Task 3: реальное Input Data

Hash: `{task3['tx_hash']}` — [Success в Sepolia Etherscan]({task3['etherscan']}).
Блок: [{task3['block_number']}](https://sepolia.etherscan.io/block/{task3['block_number']});
block hash: `{task3['block_hash']}`; подтверждений: **{task3['confirmations']}**.
From: `{task3['from']}`; To: `{task3['to']}`;
Value: **{eth(task3['value_wei'])} ETH** (`{task3['value_wei']}` wei).

Input Data декодируется из hex в UTF-8 строго в следующий текст:

```text
{evidence['task3Decoded']['text']}
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

Контракт: **`{task4['contract']}`** — [Sepolia Etherscan](https://sepolia.etherscan.io/address/{task4['contract']}).
Name: **{token['name']}**, symbol: **{token['symbol']}**, decimals: **{token['decimals']}**.
Owner: `{token['owner']}`. Получатель: `0x4a097d48ef380b479773eb609511a49cf17020f4`.
Существующая логика `task4/src/LabToken.sol` не изменена; используются параметры конструктора.

| Операция | Transaction hash | Блок | Подтверждения | Etherscan |
| --- | --- | --- | --- | --- |
{row('Deploy', task4['transactions']['deploy'])}
{row('Mint: 1 VMKRULIT владельцу', task4['transactions']['mint'])}
{row('Transfer: 1 VMKRULIT получателю', task4['transactions']['transfer'])}

Для всех трёх транзакций подтверждены status=1, канонический блок, From, Sepolia chain ID,
нулевой ETH Value и точный Input Data. Deployment совпадает с подготовленным байткодом;
runtime проверен с подстановкой immutable owner. Для mint/transfer проверены события Transfer
с точными адресами и количеством `1000000000000000000`, а не минимальной единицей токена.
На блоке mint баланс владельца и totalSupply равнялись 10^18. Никаких дополнительных approve не было.

Состояние на одном блоке **{token['block']}**:

| Метод | Результат |
| --- | --- |
| totalSupply() | `{token['totalSupply']}` = 1 VMKRULIT |
| balanceOf(получатель) | `{token['recipientBalance']}` = **1 VMKRULIT** |
| balanceOf(owner) | `{token['ownerBalance']}` |

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
"""
path.write_text(text, encoding="utf-8")
print("Updated FINAL_REPORT.md from verified RPC evidence; previous report archived. No smart contract changes.")
