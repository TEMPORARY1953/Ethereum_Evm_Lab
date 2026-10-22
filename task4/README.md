# Task 4 — ERC20 Vmk Rulit Token (VMKRULIT)

## Актуальное финальное выполнение

Foundry/solc уже установлены, **23 теста PASS**. Существующий контракт подходит для задания.
Подготовлены Foundry-артефакты, симуляция Sepolia и локальная страница подписи существующим
MetaMask без раскрытия ключа. До явного подтверждения пользователя отправка заблокирована.
План и точные действия: **[SEPOLIA_SIGNING.md](SEPOLIA_SIGNING.md)**.
Текущий сетевой статус: [FINAL_REPORT.md](../FINAL_REPORT.md).

**Далее — прежние инструкции и исторический статус до установки Foundry.
Для текущего выполнения используйте SEPOLIA_SIGNING.md.**

**Реализовано локально:** контракт, интерфейс ERC20, Foundry-конфигурация, unit/fuzz-тесты,
deploy script и сценарий Anvil. **Не выполнено:** компиляция, запуск Foundry/Anvil,
deployment, mint и transfer в Sepolia. Локальные Foundry/Anvil заблокированы отсутствием
инструментов и недоступной загрузкой. **Все публичные операции оставлены пользователю
по исходному заданию; агент их не выполняет.**

## Контракт

- `src/IERC20.sol` задаёт полный интерфейс: totalSupply, balanceOf, transfer,
  allowance, approve, transferFrom, события Transfer и Approval.
- `src/LabToken.sol` реализует этот интерфейс, метаданные и owner-only mint.
- Имя и символ — параметры конструктора; согласовано **Vmk Rulit Token / VMKRULIT**.
- Decimals = **18**; один полный токен = **1000000000000000000** минимальных единиц.
  `mint(to, 1)` выпускает только `10^-18` токена.
- Начальный totalSupply = 0, выпуск выполняется явно. Mint доступен immutable owner.
- Transfer не меняет totalSupply; нехватка баланса/allowance вызывает revert.
- Поддерживаются нулевые переводы, self-transfer, overwrite approve и unlimited allowance.
- Mint и transfer испускают Transfer, approve — Approval. Уменьшение allowance при
  transferFrom не испускает Approval: стандарт этого не требует.
- Solidity 0.8.28 проверяет арифметические переполнения; операции откатываются атомарно.
- Нулевые адреса owner/получателей/spender отклоняются.

Это собственная учебная реализация по [ERC-20](https://eips.ethereum.org/EIPS/eip-20),
без внешних зависимостей и без поддельных OpenZeppelin/forge-std модулей.
Она не проходила независимый аудит; предназначена для лабораторной в тестовой сети.

## Локальные тесты Foundry

Установить бинарники **в проект** по [.tools/README.md](../.tools/README.md):

Из корня можно выполнить автоматическую установку и все локальные этапы одной командой:
`powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_local.ps1`.
Установщик уже запускался агентом, но загрузка заблокирована sandbox; результат
в `checks/install_results.json`. Ниже отдельные команды после успешной установки:

```powershell
Push-Location task4
& ../.tools/bin/forge.exe build
& ../.tools/bin/forge.exe test -vv
Pop-Location
```

`test/LabToken.t.sol` содержит 18 тестов, включая fuzz (256 запусков):
метаданные, decimals, начальное состояние, mint, supply/balance, стандартный transfer,
события, недостаточный баланс, owner-only mint, zero/self-transfer, approve/allowance,
transferFrom, нехватку allowance, атомарность, бесконечный allowance, нулевые адреса,
пустые метаданные, overflow и сохранение supply.

`test/AverageProgram.t.sol` содержит ещё 5 тестов Task 1, включая fuzz (256 запусков).
Foundry выполняет оригинальный runtime bytecode посредством `vm.etch` и `staticcall`,
без переписывания алгоритма на Solidity.

Реальных результатов этих тестов сейчас нет. Локальные Python-проверки Task 1
не заменяют Foundry-тесты контракта. `verify.ps1` явно сообщает BLOCKED, если forge отсутствует.

## Anvil: развёртывание, mint и передача

Из корня:

```powershell
./task4/scripts/local_demo.ps1
```

Сценарий сначала запускает Foundry-тесты, затем создаёт собственный Anvil только на
`127.0.0.1`, chain ID 31337, hardfork Cancun. Занятый порт не используется.
Ключи в файлы не записываются, вывод Anvil подавлен. Используется unlocked локальный
аккаунт. Создаются контракт и один полный токен; токен передаётся на тот же 20-байтовый
адрес, который указан в задании, **в локальной сети**. Проверяется balanceOf = 10^18.
Результат сохраняется в `local_demo_result.json`, Anvil останавливается в finally.
Локальные hash/address нельзя выдавать за Sepolia.

## Подготовка Sepolia

Сначала выполнить создание encrypted keystore и получение test ETH по
[Task 2](../task2/README.md). Проверить доступность RPC и chain ID **11155111**.
Открытый приватный ключ, recovery phrase и пароль нигде не нужны в коде.

В корне проекта установить `$SENDER`, `$KEYSTORE`, `$RPC` из Task 2. Скомпилировать:

```powershell
$env:LAB_OWNER = $SENDER
$env:TOKEN_NAME = 'Vmk Rulit Token'
$env:TOKEN_SYMBOL = 'VMKRULIT'
Push-Location task4
& ../.tools/bin/forge.exe test -vv
if ($LASTEXITCODE -ne 0) { throw 'Tests must pass before deployment' }
$artifact = Get-Content out/LabToken.sol/LabToken.json -Raw | ConvertFrom-Json
$constructor = & ../.tools/bin/cast.exe abi-encode 'constructor(string,string,address)' 'Vmk Rulit Token' 'VMKRULIT' $SENDER
if ($LASTEXITCODE -ne 0) { throw 'Constructor encoding failed' }
$CREATION = $artifact.bytecode.object + $constructor.Trim().Substring(2)
Pop-Location
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task4/deployment_plan.json plan --sender $SENDER --value-wei 0 --data $CREATION
```

Перед самостоятельной отправкой проверить: Sepolia, deploy данного bytecode
с owner `$SENDER`, mint `10^18` owner, transfer `10^18` получателю
`0x4A097D48ef380B479773EB609511a49CF17020f4`, ETH value каждой операции = 0.
Gas следующих вызовов оценивается после deployment. Числовые комиссии в текущем
отчёте отсутствуют: RPC недоступен. Оценка — только подготовка к ручной операции.

## Последующее развёртывание — только вручную

Ниже команды для пользователя **отправляют реальные Sepolia-транзакции**.
Агент их не выполняет. Placeholders лимитов заменить результатами оценки;
не применять `--unlocked` к публичному RPC.

```powershell
Push-Location task4
& ../.tools/bin/forge.exe create src/LabToken.sol:LabToken --rpc-url $RPC --chain 11155111 --from $SENDER --keystore $KEYSTORE --broadcast --json --gas-limit <DEPLOY_GAS_LIMIT> --gas-price <MAX_FEE_WEI> --priority-gas-price <PRIORITY_FEE_WEI> --constructor-args 'Vmk Rulit Token' 'VMKRULIT' $SENDER
Pop-Location
```

Сохранить `transactionHash` и `deployedTo` из настоящего результата.
Альтернатива — `forge script script/Deploy.s.sol:Deploy --rpc-url $RPC --keystore $KEYSTORE
--sender $SENDER --broadcast` в task4, но **не запускать оба способа**.
Без `--broadcast` script только симулирует и не доказывает deployment.
Он защищён от chain ID кроме Anvil/Sepolia.

```powershell
$TOKEN = '<REAL_DEPLOYED_CONTRACT_ADDRESS>'
$DEPLOY_HASH = '<REAL_DEPLOY_TX_HASH>'
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task4/deployment_receipt.json receipt --tx-hash $DEPLOY_HASH
& ./.tools/bin/cast.exe call $TOKEN 'owner()(address)' --rpc-url $RPC
& ./.tools/bin/cast.exe call $TOKEN 'decimals()(uint8)' --rpc-url $RPC
& ./.tools/bin/cast.exe call $TOKEN 'name()(string)' --rpc-url $RPC
& ./.tools/bin/cast.exe call $TOKEN 'symbol()(string)' --rpc-url $RPC
```

После успешного ручного deployment оценить и самостоятельно выполнить mint:

```powershell
$MINT_DATA = & ./.tools/bin/cast.exe calldata 'mint(address,uint256)' $SENDER 1000000000000000000
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task4/mint_plan.json plan --sender $SENDER --recipient $TOKEN --value-wei 0 --data $MINT_DATA
& ./.tools/bin/cast.exe send $TOKEN 'mint(address,uint256)' $SENDER 1000000000000000000 --rpc-url $RPC --chain 11155111 --from $SENDER --keystore $KEYSTORE --gas-limit <MINT_GAS_LIMIT> --gas-price <MAX_FEE_WEI> --priority-gas-price <PRIORITY_FEE_WEI> --json
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task4/mint_receipt.json receipt --tx-hash <REAL_MINT_TX_HASH>
```

После подтверждённого mint — перевод и проверка:

```powershell
$RECIPIENT = '0x4a097d48ef380b479773eb609511a49cf17020f4'
$TRANSFER_DATA = & ./.tools/bin/cast.exe calldata 'transfer(address,uint256)' $RECIPIENT 1000000000000000000
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task4/transfer_plan.json plan --sender $SENDER --recipient $TOKEN --value-wei 0 --data $TRANSFER_DATA
& ./.tools/bin/cast.exe send $TOKEN 'transfer(address,uint256)' $RECIPIENT 1000000000000000000 --rpc-url $RPC --chain 11155111 --from $SENDER --keystore $KEYSTORE --gas-limit <TRANSFER_GAS_LIMIT> --gas-price <MAX_FEE_WEI> --priority-gas-price <PRIORITY_FEE_WEI> --json
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task4/transfer_receipt.json receipt --tx-hash <REAL_TRANSFER_TX_HASH>
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task4/recipient_balance.json balance --token $TOKEN --address $RECIPIENT
& ./.tools/bin/cast.exe call $TOKEN 'totalSupply()(uint256)' --rpc-url $RPC
```

Для каждой операции нужны status=Success и canonical block. Проверить получателя,
Transfer event, фактическое количество, name/symbol/decimals и balanceOf >= 10^18.
Ссылки: `https://sepolia.etherscan.io/address/<REAL_TOKEN_ADDRESS>` и
`https://sepolia.etherscan.io/tx/<REAL_TX_HASH>`. Исходники на GitHub и в explorer
публиковать не нужно. В рамках текущей работы исходники, bytecode и результаты
никуда не загружались; публичный deployment описан только как последующий ручной шаг.
