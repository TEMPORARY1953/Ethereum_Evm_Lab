# Task 2 — отдельный тестовый кошелёк, MetaMask и Sepolia

**Состояние:** кошелёк ещё не создан, ETH не получены, транзакции не отправлены.
Адрес коллеги неизвестен: `<COLLEAGUE_ADDRESS>`. Нельзя заменять его случайным адресом.
По исходным требованиям агент не создаёт реальные кошельки и не отправляет публичные
транзакции. Все описанные ниже операции с MetaMask, faucet и Sepolia выполняет пользователь.

## Установить инструменты

Выполнить [.tools/README.md](../.tools/README.md). Терминал этой среды не может
подключиться ни к реестру npm, ни к GitHub, ни к публичному Sepolia RPC.
Поэтому установка пользователем сейчас — необходимое действие, а не уже выполненный этап.

## Безопасная локальная подпись

Предпочтительный путь — новый отдельный encrypted JSON keystore, который можно
импортировать в MetaMask Extension. Запустить **самостоятельно в интерактивном терминале**
из корня проекта после установки Cast:

```powershell
New-Item -ItemType Directory -Force .secrets | Out-Null
& ./.tools/bin/cast.exe wallet new ./.secrets
```

Cast запросит пароль локально и создаст зашифрованный keystore. Пароль вводится в терминале,
в чат не передаётся, в аргументы команд и файлы не записывается. Путь keystore находится
внутри проекта; `.secrets/` исключён через `.gitignore`. Не применять `wallet new` без
каталога: такой режим может вывести незашифрованный ключ. Никакой открытый ключ-секрет
экспортировать не требуется. Не использовать этот учебный адрес для реальных активов.

Запишите только **публичный адрес** и путь файла в локальные переменные:

```powershell
$SENDER = '<YOUR_TEST_ADDRESS>'
$KEYSTORE = (Resolve-Path './.secrets/<CREATED_KEYSTORE_FILENAME>').Path
$RPC = 'https://ethereum-sepolia-rpc.publicnode.com'
$COLLEAGUE = '<COLLEAGUE_ADDRESS>'
```

Общий принцип подписания: `cast send ... --keystore $KEYSTORE --from $SENDER`.
Разблокировка — интерактивным запросом пароля; открытый приватный ключ в команду не передаётся.
Создание keystore не является получением ETH: новый адрес имеет нулевой баланс.

## MetaMask

1. Открыть [официальную страницу установки](https://metamask.io/download/) и перейти
   по ссылке на расширение для своего браузера. Установить именно официальное расширение.
   Ориентир: [инструкция MetaMask](https://support.metamask.io/start/getting-started-with-metamask/).
2. При необходимости первоначальной настройки выбрать создание нового кошелька в интерфейсе.
   Локальный пароль и recovery phrase сохранить самостоятельно вне отчёта и чата.
   См. [создание кошелька](https://support.metamask.io/start/creating-a-new-wallet).
3. Для общего адреса с Cast: selector аккаунтов → Add wallet → Import account →
   Select type → **JSON File**, выбрать созданный encrypted keystore и ввести его пароль
   локально. Это пароль файла, не обязательно пароль MetaMask.
   [Официальная инструкция импорта JSON](https://support.metamask.io/start/use-an-existing-wallet/).
4. Меню → Networks → внизу включить **Show test networks**, выбрать **Sepolia**.
   В другой версии переключатель может быть в списке сетей или настройках.
   [Инструкция тестовых сетей](https://support.metamask.io/configure/networks/how-to-view-testnets-in-metamask/).
5. Проверить chain ID **11155111** (hex `0xaa36a7`), валюту ETH и explorer
   `https://sepolia.etherscan.io`. Это именно Ethereum Sepolia, не L2 Sepolia.
6. Сравнить публичный адрес импортированного аккаунта с `$SENDER`.

## Получить тестовые ETH

Выбрать faucet из [списка Ethereum.org](https://ethereum.org/developers/docs/networks/#sepolia),
например [Google Cloud Web3 Sepolia Faucet](https://cloud.google.com/application/web3/faucet/ethereum/sepolia)
или [Alchemy Sepolia Faucet](https://www.alchemy.com/faucets/ethereum-sepolia).
Условия, лимиты, необходимость входа и доступность могут меняться.

На сайте выбрать Ethereum Sepolia, ввести только публичный тестовый адрес, выполнить
требуемые вход/CAPTCHA вручную и запросить ETH. Не обходить ограничения faucet.
Дождаться появления средств в MetaMask либо проверить `cast balance $SENDER --rpc-url $RPC`.
Сейчас faucet не запрашивался: адреса ещё нет.

## Оценка и ручная отправка

После получения адреса коллеги и ETH:

```powershell
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task2/transaction_plan.json plan --sender $SENDER --recipient $COLLEAGUE --value-wei 10000000000000
```

План только читает RPC. Сумма **0.00001 test ETH** = `10000000000000 wei`.
Он проверяет chain ID, оценивает gas, вычисляет верхний бюджет комиссии с запасом,
проверяет баланс и наличие кода у получателя. Пользователю нужно проверить адрес,
сумму, gas limit и max fee перед самостоятельной отправкой. При недоступности RPC
числовую комиссию определить невозможно; в отчёте она не выдумана.

**Следующая команда предназначена только для ручного запуска пользователем в Sepolia.
Агент её не выполняет:**

```powershell
& ./.tools/bin/cast.exe send $COLLEAGUE --value 0.00001ether --rpc-url $RPC --chain 11155111 --from $SENDER --keystore $KEYSTORE --gas-limit <PLAN_GAS_LIMIT> --gas-price <PLAN_MAX_FEE_WEI> --priority-gas-price <PLAN_PRIORITY_FEE_WEI> --json
```

Cast запрашивает пароль и ожидает receipt. Можно вместо этого отправить через MetaMask:
Sepolia → Send → адрес коллеги → 0.00001 ETH → проверить комиссию → Confirm.
Не отправлять обеими командами одну и ту же учебную операцию повторно.

## Реальное подтверждение и отчёт

```powershell
python -B task2/sepolia_rpc.py --rpc-url $RPC --output task2/receipt.json receipt --tx-hash <REAL_TASK2_TX_HASH>
```

Проверяются receipt status, соответствие хеша, canonical block hash, block number,
число подтверждений. `NOT MINED OR UNKNOWN` не является успехом. При pending подождать
и повторить проверку; при failed не переходить к Task 3 без успешного Task 2.

Открыть [Sepolia Etherscan](https://sepolia.etherscan.io/), вставить настоящий hash
в поиск, проверить **Success**, From, To, Value и Block. Клик по Block открывает
страницу блока. Сравнить номер и хеш блока с RPC. Заполнить
[report_template.md](report_template.md); никаких вымышленных хешей.

## Локальные тесты вспомогательных инструментов

```powershell
python -B -m unittest discover -s task2 -v
```

Используется подставной RPC **только для unit-тестов**. Эти тестовые данные
не являются результатами Sepolia и не заносятся в отчёт как реальные транзакции.
