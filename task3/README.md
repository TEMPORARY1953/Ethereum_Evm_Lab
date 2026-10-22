# Task 3 — сообщение UTF-8 → Hex → Sepolia

Имя пользователя: **TEST1337**. Получатель по заданию:
`0x4A097D48ef380B479773EB609511a49CF17020f4`.
Адрес отправителя ещё не создан, реальный hash Task 2 отсутствует.
**Сообщение не отправлено; готовый payload с реальными реквизитами пока не сформирован.**
По исходным требованиям агент выполняет только локальное кодирование и тесты;
публичную отправку пользователь выполняет самостоятельно по инструкции ниже.

## Кодирование локально

Python 3.10+, без сторонних библиотек и без RPC:

```powershell
python -B task3/encode_message.py --name TEST1337 --address '<YOUR_TEST_ADDRESS>' --tx-hash '<REAL_TASK2_TX_HASH>'
```

Подставить настоящий адрес и **успешный** настоящий Task 2 hash. Placeholders намеренно
не проходят валидацию. Скрипт печатает только `0x` + hex UTF-8 байтов сообщения:

```text
Name: TEST1337
Ethereum address: <YOUR_TEST_ADDRESS>
Task 2 transaction hash: <REAL_TASK2_TX_HASH>
```

Проверяется 20-байтовый адрес, ненулевое значение, префикс `0x` и hex-символы;
для hash — ровно 32 байта и ненулевое значение. Имя не может быть пустым или содержать
управляющие символы. Проверка адреса **синтаксическая**: EIP-55 checksum, владение адресом
и существование транзакции скрипт не устанавливает. Hash нужно проверить через RPC Task 2.
Hex-данные не являются шифрованием: имя и реквизиты станут публичными при отправке.

```powershell
$HEX = python -B task3/encode_message.py --name TEST1337 --address $SENDER --tx-hash $TASK2_HASH
if ($LASTEXITCODE -ne 0) { throw 'Encoding failed' }
python -B task3/encode_message.py --decode $HEX
$HEX | Set-Content -Encoding ascii -NoNewline task3/message.hex
python -B task3/encode_message.py --decode $HEX | Set-Content -Encoding utf8 task3/message.txt
```

Файлы `message.hex`, `message.txt` создаются только после получения реальных данных.
Сейчас есть лишь [message_template.txt](message_template.txt).

## MetaMask и ненулевой value

В MetaMask **Extension** включить Settings → Transactions → **Show hex data**.
В старых версиях настройка может находиться в Advanced. Если поля нет, использовать
Cast с локальным encrypted keystore, а не отправлять транзакцию без сообщения.
См. [официальную инструкцию Hex Data](https://support.metamask.io/configure/transactions/how-to-add-a-memo-to-a-transaction/).

1. Выбрать отдельный тестовый аккаунт и **Ethereum Sepolia**.
2. Убедиться, что Task 2 подтверждён и hash включён в `$HEX` без placeholders.
3. Подготовить read-only оценку для получателя и ненулевых **0.000001 test ETH**:

```powershell
$RECIPIENT = '0x4a097d48ef380b479773eb609511a49cf17020f4'
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task3/transaction_plan.json plan --sender $SENDER --recipient $RECIPIENT --value-wei 1000000000000 --data $HEX
```

4. Самостоятельно проверить сеть, получателя, value, сообщение и бюджет комиссии.
   Если получатель — контракт, предварительный
   `eth_estimateGas` должен успешно проверить вызов с этим value/data.
5. MetaMask → Send → указанный получатель → 0.000001 ETH → Hex Data = `$HEX`.
   Проверить адрес, данные и комиссию; пользователь самостоятельно нажимает Confirm.
6. Альтернатива через Cast **только для ручного запуска**, без повторной отправки MetaMask:

```powershell
& ./.tools/bin/cast.exe send $RECIPIENT --value 0.000001ether --data $HEX --rpc-url $RPC --chain 11155111 --from $SENDER --keystore $KEYSTORE --gas-limit <PLAN_GAS_LIMIT> --gas-price <PLAN_MAX_FEE_WEI> --priority-gas-price <PLAN_PRIORITY_FEE_WEI> --json
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task3/receipt.json receipt --tx-hash <REAL_TASK3_TX_HASH>
```

7. Проверить Success и включение в canonical block. На Etherscan открыть Input Data,
   сравнить raw hex и декодированный UTF-8 с `message.txt`, проверить ненулевой Value.
   Сохранить настоящий hash, block number, ссылку, `message.hex` и `receipt.json`.

## Тесты

```powershell
python -B -m unittest discover -s task3 -v
```

9 тестовых методов: известные ASCII/UTF-8 байты, round trip, полный формат,
ошибочные адреса/hash/имена, hex и невалидный UTF-8. Тестовые адреса и hash явно
синтетические; их нельзя выдавать за данные Task 2.
