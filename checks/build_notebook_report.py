"""Build a self-contained Jupyter lab with executable examples and screenshots."""
import base64
from contextlib import redirect_stdout
from io import BytesIO
from io import StringIO
import json
from pathlib import Path
from pprint import pformat
import re

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / "checks/final_sepolia_audit.json").read_text(encoding="utf-8"))
t2, t3, t4 = audit["task2"], audit["task3"], audit["task4"]
owner = audit["task3Decoded"]["address"]
recipient = t3["to"]
cells = []


def md(text):
    cells.append({"cell_type": "markdown", "id": f"report-{len(cells) + 1:02d}",
                  "metadata": {}, "source": text.strip().splitlines(keepends=True)})


def code(text, *, hidden=False):
    cells.append({"cell_type": "code", "id": f"report-{len(cells) + 1:02d}",
                  "metadata": {"jupyter": {"source_hidden": True}} if hidden else {},
                  "source": text.strip().splitlines(keepends=True),
                  "execution_count": None, "outputs": []})


def screenshot(filename, caption):
    raw = (ROOT / "Screens" / filename).read_bytes()
    with Image.open(BytesIO(raw)) as picture:
        picture.verify()
    md(f"![{caption}](attachment:{filename})\n\n*{caption}*")
    cells[-1]["attachments"] = {filename: {"image/png": base64.b64encode(raw).decode("ascii")}}


def transaction(label, item):
    return (f"**{label}**\n\n"
            f"Transaction hash: `{item['tx_hash']}`\n\n"
            f"Блок: **{item['block_number']}**. Статус: **Success**. "
            f"[Открыть в Sepolia Etherscan]({item['etherscan']}).")


md(f"""# Лабораторная работа: Ethereum и EVM

**Выполнил:** Lysak Vladimir  
**Дата:** 22.10.2026  
**Сеть:** Ethereum Sepolia (chain ID 11155111)

Мой адрес: `{owner}`

В работе я написал программу на EVM-опкодах, отправил тестовые ETH и сообщение,
а затем выпустил собственный ERC20-токен. Ниже — результаты и скриншоты по каждому заданию.
""")

md("""## Запуск кода

Этот файл — самостоятельный отчёт: для просмотра и выполнения другие файлы и папки не нужны.
Выберите Python 3 и выполните **Run All** сверху вниз. Нужна только стандартная
библиотека Python: исходники, тестовые данные и снимок RPC-ответов встроены в ноутбук.
Результаты ячеек уже сохранены. Снимок относится к проверке от 22.10.2026;
ячейки повторно анализируют эти данные локально, без подключения к сети.
""")
code('''import json
import random
from decimal import Decimal

CHAIN_ID = 11155111
WEI_PER_ETH = 10**18

def wei_to_eth(value):
    return Decimal(value) / Decimal(WEI_PER_ETH)

print("Сеть: Ethereum Sepolia, chain ID:", CHAIN_ID)''')

# Keep the original receipt fields used below; omit bulky blooms and deploy bytecode.
def snapshot_transaction(item):
    result = {key: item[key] for key in (
        "chain_id", "tx_hash", "block_number", "from", "to", "value_wei",
        "gas_used", "actual_fee_wei", "etherscan", "contract_address")}
    if item["to"] is not None:
        result["input_data"] = item["input_data"]
    result["receipt"] = {key: item["receipt"][key] for key in (
        "status", "transactionHash", "blockNumber", "gasUsed", "effectiveGasPrice", "logs")}
    return result

snapshot = {
    "verifiedAt": audit["verifiedAt"], "chainId": audit["chainId"],
    "owner": owner, "recipient": recipient,
    "task2": snapshot_transaction(t2), "task3": snapshot_transaction(t3),
    "task3Decoded": audit["task3Decoded"],
    "task4": {"contract": t4["contract"], "token": t4["token"],
              "transactions": {key: snapshot_transaction(value)
                               for key, value in t4["transactions"].items()}},
}
code("# Снимок RPC-ответов встроен в отчёт; ячейка не выполняет сетевые запросы.\n"
     + "evidence = " + pformat(snapshot, width=100, sort_dicts=False)
     + '\nassert evidence["chainId"] == CHAIN_ID\n'
     + 'print("Дата исходной RPC-проверки:", evidence["verifiedAt"])', hidden=True)

md("""## Task 1. Среднее значение на EVM-опкодах

Программа читает число N и следующие N чисел из calldata. Она проверяет, что N больше
нуля и все числа переданы, считает среднее и возвращает результат. При неверном вводе
выполнение завершается с REVERT. Программа написана на мнемониках EVM, без Solidity и Yul.

Проверил её в **EVM Codes Playground** с выбранным **Cancun**. Для чисел 10, 20 и 30
получилось **20**, то есть **0x14**. После выполнения стек пуст — это видно на скриншоте.

Полный исходный код программы приведён в следующей ячейке.

[Открыть EVM Codes Playground](https://www.evm.codes/playground?fork=cancun&callValue=0&unit=Wei&callData=0x0000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000001e&codeType=Mnemonic&code='d0tkvuv0vmSGTli0qzLTyq~1fcyo0qzDIV~01zSWAP1zSUBvmEQlv0_upqimEQr7asIiwtk~6ew~6b~8ej~6jc~ffzSHRy~8w_biur36spvwomSDIVvehTURNpvhVERTz'~v1gz%5Cnyr87sIw0zMkvzdu0zMSTOREtzCALLDATAszJUMPrv2g00qtSIZEpsDESTo~2mwzlzISZEROykLOADjw~8mXORi~4h0v0zREg%200xeuodPUSHczANDbmADD_oe0i%01_bcdeghijklmopqrstuvwyz~_).
""")
md("""### Исходник и локальное выполнение

Ниже встроен полный исходный код на EVM-мнемониках. Формат calldata: 32-байтовое N, затем ровно N
слов int256; selector отсутствует. `SDIV` округляет к нулю. Если промежуточная
сумма выходит за пределы int256, программа вызывает REVERT.
""")
program_text = (ROOT / "task1/program.evm").read_text(encoding="utf-8").strip()
code('program_source = """\n' + program_text + '\n"""')
md("""Вспомогательный Python-код собирает и выполняет реальные байты этой программы.
Интерпретатор целиком встроен в следующую ячейку. Он поддерживает используемые
инструкции, но не моделирует gas и состояние блокчейна. Проверка в Cancun Playground
показана на скриншоте ниже.
""")
interpreter = (ROOT / "task1/local_evm.py").read_text(encoding="utf-8")
interpreter = interpreter.split("\ndef load_program():", 1)[0].replace("from pathlib import Path\n", "")
code(interpreter + '\n\nprogram = assemble(program_source)\n'
     + 'print("Размер EVM-программы:", len(program), "байт")\n'
     + 'print("Bytecode: 0x" + program.hex())')
code('''values = [10, 20, 30]
input_data = calldata(len(values), values)
result = execute(program, input_data)
average = signed(int.from_bytes(result["data"], "big"))
assert result["status"] == "return" and average == 20
assert result["stack"] == []
print("Calldata: 0x" + input_data.hex())
print("Return data: 0x" + result["data"].hex())
print("Среднее:", average)
print("Стек после RETURN:", result["stack"])
print("Максимальная глубина стека:", result["max_stack"])''')
md("### Граничные случаи и проверка по математическому эталону")
case_source = (ROOT / "task1/test_program.py").read_text(encoding="utf-8")
case_source = case_source.split("def cases():", 1)[1].split("\n\nclass ProgramTests", 1)[0]
code("def cases():" + case_source + '''

def check_execution(data, expected):
    result = execute(program, data)
    assert result["stack"] == [] and result["max_stack"] <= 3
    assert result["status"] == ("revert" if expected is None else "return")
    assert result["data"] == (b"" if expected is None else word(expected))

for label, data, expected in cases():
    check_execution(data, expected)
    print(f"{label}: {'REVERT' if expected is None else expected} — OK")

rng = random.Random(20261022)
edges = [MIN_INT, MIN_INT + 1, -1, 0, 1, MAX_INT - 1, MAX_INT]
for _ in range(1000):
    values = [rng.choice(edges) if rng.randrange(3) == 0 else rng.randint(-10**20, 10**20)
              for _ in range(rng.randint(1, 16))]
    running, expected = 0, None
    for value in values:
        running += value
        if not MIN_INT <= running <= MAX_INT:
            break
    else:
        expected = (-1 if running < 0 else 1) * (abs(running) // len(values))
    check_execution(calldata(len(values), values), expected)
print(f"Итого: {len(cases())} фиксированных + 1000 случайных примеров — OK")''')
screenshot("1.1.png", "EVM Playground: Cancun, результат 0x14 и пустой Stack.")

md(f"""## Task 2. Перевод тестовых ETH

Для работы с Sepolia использовал кошелёк MetaMask. Отправил **0.0001 тестового ETH**
на адрес `{t2['to']}`. В Etherscan у транзакции указан статус **Success** и номер блока.

{transaction('Перевод ETH', t2)}
""")
md("### Проверка receipt, суммы и комиссии\n\nКомиссия вычисляется точно в wei: `gasUsed × effectiveGasPrice`.")
code('''def check_receipt(item):
    receipt = item["receipt"]
    assert item["chain_id"] == CHAIN_ID
    assert int(receipt["status"], 16) == 1
    assert receipt["transactionHash"].lower() == item["tx_hash"].lower()
    assert int(receipt["blockNumber"], 16) == item["block_number"]
    gas_used = int(receipt["gasUsed"], 16)
    assert gas_used == item["gas_used"]
    fee = gas_used * int(receipt["effectiveGasPrice"], 16)
    assert fee == int(item["actual_fee_wei"])
    return fee

eth_transfer = evidence["task2"]
fee_wei = check_receipt(eth_transfer)
assert eth_transfer["from"].lower() == evidence["owner"].lower()
assert eth_transfer["input_data"] == "0x"
assert int(eth_transfer["value_wei"]) == 10**14
print("Блок:", eth_transfer["block_number"])
print("Получатель:", eth_transfer["to"])
print("Сумма:", wei_to_eth(eth_transfer["value_wei"]), "ETH")
print("Gas used:", eth_transfer["gas_used"])
print("Комиссия:", fee_wei, "wei =", wei_to_eth(fee_wei), "ETH")
print("Сумма + комиссия:", wei_to_eth(int(eth_transfer["value_wei"]) + fee_wei), "ETH")''')
screenshot("2.1.png", "Task 2: успешный перевод 0.0001 ETH, адреса и блок в Sepolia Etherscan.")

md(f"""## Task 3. Сообщение в блокчейне

Отправил сообщение на адрес `{recipient}`. Вместе с сообщением передал
**0.00001 ETH**, поэтому Value ненулевой. Текст был переведён в Hex с префиксом `0x`
и помещён в Input Data.

В сообщении указаны моё имя, мой Ethereum-адрес и hash перевода из Task 2:

```text
{audit['task3Decoded']['text']}
```

{transaction('Транзакция с сообщением', t3)}
""")
md("### Подготовка сообщения и проверка Input Data")
encoder = (ROOT / "task3/encode_message.py").read_text(encoding="utf-8")
encoder = encoder.split("\ndef main()", 1)[0].replace("import argparse\n", "")
code(encoder + '''

message = build_message(evidence["task3Decoded"]["name"], evidence["owner"], eth_transfer["tx_hash"])
message_hex = encode_message(message)
message_tx = evidence["task3"]
check_receipt(message_tx)
assert message_tx["from"].lower() == evidence["owner"].lower()
assert message_tx["to"].lower() == evidence["recipient"].lower()
assert int(message_tx["value_wei"]) > 0
assert message_hex == message_tx["input_data"]
assert decode_message(message_hex) == message == evidence["task3Decoded"]["text"]
print(message)
print("\\nInput Data:", message_hex)
print("Размер сообщения:", len(message.encode("utf-8")), "байт")
print("Value:", wei_to_eth(message_tx["value_wei"]), "ETH")
print("Кодирование UTF-8 → Hex → UTF-8 и совпадение с транзакцией: OK")''')
screenshot("3.1.png", "Task 3: успешная транзакция и сообщение в формате Hex в Input Data.")
screenshot("3.2.png", "То же сообщение после переключения Input Data в текстовый вид.")

md(f"""## Task 4. Собственный ERC20-токен

Полный код ERC20-контракта приведён ниже. Foundry применял для сборки и проверки,
а MetaMask — для подписи и отправки транзакций в Sepolia.

| Параметр | Значение |
| --- | --- |
| Название | **Vmk Rulit Token** |
| Символ | **VMKRULIT** |
| Decimals | **18** |
| Выпущено | **1 полный токен** |
| Минимальных единиц в 1 токене | **1000000000000000000** |

Адрес контракта: `{t4['contract']}`.

[Открыть контракт в Sepolia Etherscan](https://sepolia.etherscan.io/address/{t4['contract']}).

Сначала развернул контракт, затем выпустил 1 токен на свой адрес и перевёл его на
`{recipient}`.
""")

md("### Исходный код контракта\n\n"
   "`IERC20.sol` задаёт интерфейс, `LabToken.sol` реализует выпуск, перевод и allowance. "
   "Выпуск доступен только `owner`; суммы передаются в минимальных единицах. "
   "Эти Solidity-исходники компилируются Foundry, Python-ядро их не выполняет.\n\n"
   "**Интерфейс IERC20**\n\n```solidity\n"
   + (ROOT / "task4/src/IERC20.sol").read_text(encoding="utf-8").strip()
   + "\n```\n\n**Контракт LabToken**\n\n```solidity\n"
   + (ROOT / "task4/src/LabToken.sol").read_text(encoding="utf-8").strip() + "\n```")
md("### ABI-кодирование mint и transfer\n\n"
   "Селекторы взяты из вызовов контракта; адрес и количество дополняются до 32 байт. "
   "Полученные данные сравниваются с уже выполненными транзакциями.")
code('''token_evidence = evidence["task4"]
token_snapshot = token_evidence["token"]
decimals = token_snapshot["decimals"]
one_token = 10**decimals

def encode_address_amount(selector, address, amount):
    validate_address(address)
    if not re.fullmatch(r"0x[0-9a-fA-F]{8}", selector):
        raise ValueError("Селектор должен занимать 4 байта")
    if not 0 <= amount < 2**256:
        raise ValueError("Количество должно помещаться в uint256")
    return selector + address[2:].lower().zfill(64) + f"{amount:064x}"

mint_data = encode_address_amount("0x40c10f19", evidence["owner"], one_token)
transfer_data = encode_address_amount("0xa9059cbb", evidence["recipient"], one_token)
token_transactions = token_evidence["transactions"]
assert mint_data == token_transactions["mint"]["input_data"]
assert transfer_data == token_transactions["transfer"]["input_data"]
assert token_transactions["deploy"]["contract_address"].lower() == token_evidence["contract"].lower()
assert token_transactions["deploy"]["to"] is None
for operation, transaction in token_transactions.items():
    check_receipt(transaction)
    assert transaction["from"].lower() == evidence["owner"].lower()
    if operation != "deploy":
        assert transaction["to"].lower() == token_evidence["contract"].lower()
    print(f"{operation}: блок {transaction['block_number']}, status = 1")
print("1 токен =", one_token, "минимальных единиц")
print("mint input:", mint_data)
print("transfer input:", transfer_data)''')

md("### Развёртывание контракта\n\n" + transaction("Deployment", t4["transactions"]["deploy"]))
screenshot("4.1.png", "Task 4: контракт создан, deployment-транзакция завершилась успешно.")

md("### Выпуск токена\n\n"
   "Вызвал `mint` и выпустил **1 VMKRULIT** на свой адрес. "
   "На скриншоте выпуск показан как перевод токена с нулевого адреса.\n\n"
   + transaction("Mint", t4["transactions"]["mint"]))
screenshot("4.2.png", "Task 4: успешный mint одного VMKRULIT на мой адрес.")

md("### Перевод токена\n\n"
   f"Вызвал `transfer` и отправил **1 VMKRULIT** на `{recipient}`. "
   "Внешний To транзакции — адрес контракта токена, а получатель и количество записаны в Input Data.\n\n"
   + transaction("Transfer", t4["transactions"]["transfer"]))
screenshot("4.3.png", "Task 4: успешный перевод одного VMKRULIT на адрес из задания.")

md(f"""### Проверка результата

Транзакции дополнительно проверены через Sepolia RPC. На блоке **{t4['token']['block']}**:

| Что проверил | Результат |
| --- | --- |
| Баланс получателя | **1 VMKRULIT** (1000000000000000000 единиц) |
| Мой остаток токенов | **0** |
| Общее количество выпущенных токенов | **1 VMKRULIT** |

Таким образом, получатель получил именно один полный токен с учётом 18 decimals.
""")
code('''TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO_ADDRESS = "0x" + "0" * 40

def transfer_events(transaction):
    events = []
    for log in transaction["receipt"]["logs"]:
        if log["address"].lower() != token_evidence["contract"].lower():
            continue
        topics = log["topics"]
        if len(topics) == 3 and topics[0].lower() == TRANSFER_TOPIC:
            events.append({"from": "0x" + topics[1][-40:],
                           "to": "0x" + topics[2][-40:],
                           "amount": int(log["data"], 16)})
    return events

mint_events = transfer_events(token_transactions["mint"])
sent_events = transfer_events(token_transactions["transfer"])
assert mint_events == [{"from": ZERO_ADDRESS, "to": evidence["owner"].lower(), "amount": one_token}]
assert sent_events == [{"from": evidence["owner"].lower(),
                        "to": evidence["recipient"].lower(), "amount": one_token}]
assert token_snapshot["owner"].lower() == evidence["owner"].lower()
assert int(token_snapshot["totalSupply"]) == one_token
assert int(token_snapshot["recipientBalance"]) == one_token
assert int(token_snapshot["ownerBalance"]) == 0
print("Transfer при выпуске:", mint_events[0])
print("Transfer при отправке:", sent_events[0])
print("Блок снимка балансов:", token_snapshot["block"])
for field in ("totalSupply", "ownerBalance", "recipientBalance"):
    balance = Decimal(token_snapshot[field]) / Decimal(one_token)
    print(f"{field}: {balance} {token_snapshot['symbol']}")
print("Выпуск, перевод и балансы согласованы: OK")''')

md("""## Тесты

Локальные проверки прошли успешно:

- **23 теста Foundry:** 5 для программы Task 1 и 18 для ERC20-контракта.
- **21 Python-тест:** программа на опкодах, вспомогательные RPC-проверки и кодирование сообщения.

Для Task 1 также проверены 29 готовых примеров и 1000 случайных наборов чисел.
Для Task 2–4 реальные результаты RPC-проверки встроены в словарь `evidence` в начале отчёта.

## Результат работы

| Задание | Результат |
| --- | --- |
| Task 1 | Программа считает среднее; в Playground Cancun показаны результат и пустой стек |
| Task 2 | Тестовый ETH-перевод прошёл успешно, блок найден в Etherscan |
| Task 3 | Сообщение с именем, адресом и hash Task 2 записано в блокчейн с ненулевым Value |
| Task 4 | Собственный токен выпущен; 1 VMKRULIT переведён на нужный адрес |

Все скриншоты встроены в этот ноутбук. Для просмотра достаточно открыть сам файл `.ipynb`.
""")
code('''all_transactions = [evidence["task2"], evidence["task3"], *token_transactions.values()]
total_fee = sum(check_receipt(item) for item in all_transactions)
print("Task 1: 29 фиксированных и 1000 случайных примеров — OK")
print("Task 2: сумма, статус и комиссия ETH-перевода — OK")
print("Task 3: текст, Hex, получатель и ненулевой Value — OK")
print("Task 4: ABI, события выпуска и перевода, итоговые балансы — OK")
print("Проверено транзакций из сохранённого RPC-снимка:", len(all_transactions))
print("Общая комиссия:", total_fee, "wei =", wei_to_eth(total_fee), "ETH")''')

# Execute the exact Python cells in a fresh shared namespace and retain real stdout.
# No Jupyter packages, project imports, network, or wallet are needed by these cells.
namespace = {"__name__": "__main__"}
execution_count = 0
for cell in cells:
    if cell["cell_type"] != "code":
        continue
    execution_count += 1
    stdout = StringIO()
    with redirect_stdout(stdout):
        exec(compile("".join(cell["source"]), f"<notebook-cell-{execution_count}>", "exec"), namespace)
    cell["execution_count"] = execution_count
    if stdout.getvalue():
        cell["outputs"] = [{"output_type": "stream", "name": "stdout",
                            "text": stdout.getvalue().splitlines(keepends=True)}]

notebook = {"cells": cells, "metadata": {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "file_extension": ".py", "mimetype": "text/x-python"},
    "title": "Лабораторная работа: Ethereum и EVM — Task 1–4",
    "authors": [{"name": "Lysak Vladimir"}]}, "nbformat": 4, "nbformat_minor": 5}

output = ROOT / "Ethereum_Lab_Report.ipynb"
output.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

# Check notebook structure, actual execution results, and every original image.
saved = json.loads(output.read_text(encoding="utf-8"))
assert saved["nbformat"] == 4 and saved["nbformat_minor"] == 5
assert len({cell["id"] for cell in saved["cells"]}) == len(saved["cells"])
attached = []
for cell in saved["cells"]:
    assert cell["cell_type"] in {"markdown", "code"} and isinstance(cell["source"], list)
    if cell["cell_type"] == "code":
        assert isinstance(cell["execution_count"], int)
        assert all(item["output_type"] != "error" for item in cell["outputs"])
    assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", cell["id"])
    for filename in re.findall(r"attachment:([^\s)]+)", "".join(cell["source"])):
        data = base64.b64decode(cell["attachments"][filename]["image/png"], validate=True)
        assert data == (ROOT / "Screens" / filename).read_bytes()
        with Image.open(BytesIO(data)) as picture:
            picture.verify()
        attached.append(filename)
assert sorted(attached) == sorted(path.name for path in (ROOT / "Screens").glob("*.png"))
for item in [t2, t3, *t4["transactions"].values()]:
    assert item["tx_hash"] in output.read_text(encoding="utf-8")
print(f"Created {output.name}: {len(cells)} cells, {execution_count} executed Python cells, "
      f"{len(attached)} embedded original screenshots, "
      f"{output.stat().st_size:,} bytes. JSON, attachments and all 5 transaction hashes checked.")
