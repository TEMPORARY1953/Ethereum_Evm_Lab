"use strict";
let plan, state, provider, connected = false, busy = false;
const steps = ["deploy", "mint", "transfer"];
const previews = new Map();
const byId = id => document.getElementById(id);
const providers = [];
window.addEventListener("eip6963:announceProvider", event => {
  if (event.detail.info.rdns === "io.metamask" && !providers.includes(event.detail.provider)) providers.push(event.detail.provider);
});
window.dispatchEvent(new Event("eip6963:requestProvider"));
const storageKey = step => `task4-sepolia-${plan.planId}-${step}`;
const pendingKey = step => storageKey(step) + "-awaiting-wallet";
const confirmed = step => state.transactions[step]?.evidence?.status === "CONFIRMED SUCCESS" &&
  (state.transactions[step]?.evidence?.confirmations || 0) >= 2;
function eth(wei) {
  const value = BigInt(wei).toString().padStart(19, "0");
  return value.slice(0, -18) + "." + value.slice(-18).replace(/0+$/, "").padEnd(1, "0");
}
async function api(path, data) {
  const response = await fetch(path, data === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({...data, planId: plan.planId})
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || response.statusText);
  return result;
}
function blocked(step) {
  return !!state.transactions[step] || !!localStorage.getItem(storageKey(step)) ||
    !!localStorage.getItem(pendingKey(step)) || steps.slice(0, steps.indexOf(step)).some(previous => !confirmed(previous));
}
function render() {
  byId("approval").textContent = plan.approved ? "План разрешён. Сначала проверьте параметры, затем отдельно откройте подтверждение MetaMask." : "Отправка заблокирована.";
  for (const step of steps) {
    const item = state.transactions[step], saved = localStorage.getItem(storageKey(step));
    const pending = localStorage.getItem(pendingKey(step));
    byId(step).disabled = busy || !connected || !plan.approved || blocked(step);
    byId(step + "Send").disabled = busy || !connected || !plan.approved || blocked(step) || !previews.has(step);
    byId(step + "Status").textContent = item?.hash ? `${item.hash} · подтверждений: ${item.evidence?.confirmations || 0}` :
      saved ? `Hash сохранён: ${saved}. Проверка RPC восстановит состояние.` :
      (item || pending) ? "Есть незавершённый запрос MetaMask. Повторная отправка заблокирована; восстановите публичный hash из истории кошелька." : "Не отправлено";
  }
  byId("connect").disabled = busy;
  byId("verify").disabled = busy;
  byId("recover").disabled = busy || !plan.approved;
  byId("contract").textContent = state.contract ? `Контракт: ${state.contract}` : "";
}
async function guard() {
  if (!provider) throw new Error("Подключите MetaMask");
  if (BigInt(await provider.request({method: "eth_chainId"})) !== 11155111n)
    throw new Error("В MetaMask выберите Ethereum Sepolia");
  const accounts = await provider.request({method: "eth_accounts"});
  if (accounts.length !== 1 || accounts[0].toLowerCase() !== plan.owner.toLowerCase())
    throw new Error(`Разрешите странице только один аккаунт: ${plan.owner}`);
}
async function connect() {
  provider = providers[0] || (window.ethereum?.providers || [window.ethereum]).find(p => p?.isMetaMask);
  if (!provider) throw new Error("Откройте эту страницу в браузере с расширением MetaMask");
  await provider.request({method: "eth_requestAccounts"});
  if (BigInt(await provider.request({method: "eth_chainId"})) !== 11155111n)
    await provider.request({method: "wallet_switchEthereumChain", params: [{chainId: "0xaa36a7"}]});
  await guard();
  connected = true;
  const changed = () => { connected = false; previews.clear(); render(); };
  provider.on("accountsChanged", changed); provider.on("chainChanged", changed);
  byId("account").textContent = `Подключён только ${plan.owner} · Ethereum Sepolia`;
  byId("status").textContent = "MetaMask подключён. Нажмите «Проверить параметры deployment». Это ещё не отправляет транзакцию.";
}
async function verify() {
  for (const step of steps) {
    const saved = localStorage.getItem(storageKey(step));
    if (saved && !state.transactions[step]?.hash) state = await api("/api/record", {step, hash: saved});
  }
  state = await api("/api/verify", {});
  byId("status").textContent = state.status === "VERIFIED SEPOLIA SUCCESS" ?
    "Готово: все три операции подтверждены RPC; FINAL_REPORT.md обновлён.\n" + JSON.stringify(state.token, null, 2) :
    "RPC проверен. Следующий этап откроется после успешного receipt и 2 подтверждений. Проверка выполняется автоматически; подписи — только вручную.";
}
function validateTransaction(step, tx) {
  if (tx.from.toLowerCase() !== plan.owner.toLowerCase() || tx.chainId !== "0xaa36a7" || tx.value !== "0x0" ||
      tx.data !== (step === "deploy" ? plan.creationData : plan[step + "Data"]) ||
      tx.gas !== "0x" + plan.gasLimits[step].toString(16) ||
      BigInt(tx.maxFeePerGas) !== BigInt(plan.maxFeePerGasWei) ||
      BigInt(tx.maxPriorityFeePerGas) !== BigInt(plan.maxPriorityFeePerGasWei) ||
      (step === "deploy" ? tx.to !== undefined : tx.to?.toLowerCase() !== state.contract?.toLowerCase()))
    throw new Error("Параметры транзакции расходятся с разрешённым планом");
}
async function prepareStep(step) {
  if (!plan.approved) throw new Error("План не подтверждён");
  await guard(); await verify();
  if (blocked(step)) throw new Error("Предыдущий этап ещё не подтверждён либо операция уже отправлена/ожидает кошелька");
  const review = await api("/api/preview", {step});
  if (review.planId !== plan.planId) throw new Error("План изменился; обновите страницу");
  validateTransaction(step, review.transaction);
  previews.set(step, {review, time: Date.now()});
  byId(step + "Review").textContent = JSON.stringify(review.decoded, null, 2) +
    `\nEstimated gas: ${review.gasEstimate}\nEstimated gas fee: ${eth(review.estimatedFeeWei)} Sepolia ETH` +
    `\nМаксимальная комиссия: ${eth(review.maximumFeeWei)} Sepolia ETH\nMax fee: 1 gwei; priority: 0.001 gwei` +
    `\nОценка на блоке: ${review.estimatedAtBlock}\nCalldata: ${step === "deploy" ?
      ((review.transaction.data.length - 2) / 2) + " байт; полный bytecode — в разделе «Точные данные транзакций из Foundry»" : review.transaction.data}`;
  byId("status").textContent = "Параметры показаны. Проверьте их и нажмите отдельную кнопку подтверждения в MetaMask.";
}
async function send(step) {
  if (!plan.approved) throw new Error("План не подтверждён");
  await guard(); await verify();
  if (blocked(step)) throw new Error("Операция уже отправлена/ожидает кошелька либо предыдущий этап ещё не подтверждён");
  const prepared = previews.get(step);
  if (!prepared || Date.now() - prepared.time > 90000) throw new Error("Сначала обновите и проверьте параметры транзакции");
  const tx = prepared.review.transaction;
  validateTransaction(step, tx);
  const reserved = await api("/api/reserve", {step});
  state = reserved.state;
  localStorage.setItem(pendingKey(step), reserved.requestId);
  let requestedWallet = false, hash;
  try {
    await guard();
    requestedWallet = true;
    hash = await provider.request({method: "eth_sendTransaction", params: [tx]});
  } catch (error) {
    // Uncertain sends are never retried. Only a known rejection/pre-send failure releases the lock.
    if (!requestedWallet || error.code === 4001) {
      state = await api("/api/release", {step, requestId: reserved.requestId});
      localStorage.removeItem(pendingKey(step));
    }
    throw error;
  }
  localStorage.setItem(storageKey(step), hash);
  localStorage.removeItem(pendingKey(step));
  previews.delete(step);
  byId("status").textContent = `Отправлено: ${hash}. Повторная отправка заблокирована.`;
  state = await api("/api/record", {step, hash});
}
async function recover() {
  const step = byId("recoverStep").value, hash = byId("recoverHash").value.trim();
  if (!/^0x[0-9a-fA-F]{64}$/.test(hash)) throw new Error("Введите только публичный transaction hash из истории MetaMask");
  state = await api("/api/record", {step, hash});
  localStorage.setItem(storageKey(step), hash);
  localStorage.removeItem(pendingKey(step));
  await verify();
}
async function action(fn) {
  if (busy) return;
  busy = true; render();
  try { await fn(); } catch (error) { byId("status").textContent = error.message; }
  finally { busy = false; render(); }
}
async function init() {
  plan = await api("/api/plan"); state = plan.state;
  byId("owner").textContent = plan.owner; byId("recipient").textContent = plan.recipient;
  byId("details").textContent = JSON.stringify({planId:plan.planId, sourceSha256:plan.sourceSha256,
    name:plan.name, symbol:plan.symbol, creationData:plan.creationData,
    mintData:plan.mintData, transferData:plan.transferData, gasLimits:plan.gasLimits}, null, 2);
  byId("connect").onclick = () => action(connect);
  byId("verify").onclick = () => action(verify);
  byId("recover").onclick = () => action(recover);
  for (const step of steps) {
    byId(step).onclick = () => action(() => prepareStep(step));
    byId(step + "Send").onclick = () => action(() => send(step));
  }
  render();
  // Read-only recovery/polling. No wallet requests or automatic signing here.
  if (Object.keys(state.transactions).length) await action(verify);
  setInterval(() => {
    if (!busy && state.status !== "VERIFIED SEPOLIA SUCCESS" &&
        steps.some(step => state.transactions[step]?.hash || localStorage.getItem(storageKey(step)))) action(verify);
  }, 12000);
}
init().catch(error => { byId("status").textContent = error.message; });
