// Provider/DOM doubles only: this test never connects to a wallet or network.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

async function setup(approved) {
  const plan = JSON.parse(fs.readFileSync(path.join(__dirname, '../sepolia_plan.json'), 'utf8'));
  plan.approved = approved;
  const state = {chainId:11155111, transactions:{}};
  plan.state = state;
  const elements = new Map(), storage = new Map(), sent = [];
  let account = plan.owner, chain = '0xaa36a7', failure = null, extraAccount = false, tamper = false;
  const provider = {isMetaMask:true, on(){}, async request({method, params}) {
    if (method === 'eth_requestAccounts' || method === 'eth_accounts') return extraAccount ? [account, '0x'+'2'.repeat(40)] : [account];
    if (method === 'eth_chainId') return chain;
    if (method === 'eth_estimateGas') return '0x7a120';
    if (method === 'eth_getBlockByNumber') return {baseFeePerGas:'0x1'};
    if (method === 'eth_getBalance') return '0x16345785d8a0000';
    if (method === 'eth_sendTransaction') {
      if (failure) throw failure;
      sent.push(params[0]); return '0x' + '1'.repeat(64);
    }
    throw Error('Unexpected provider method: ' + method);
  }};
  const context = vm.createContext({console, Date, BigInt, JSON, Error, setInterval(){},
    document:{getElementById(id){
      if (!elements.has(id)) elements.set(id, {});
      return elements.get(id);
    }},
    localStorage:{getItem:k=>storage.get(k)||null, setItem:(k,v)=>storage.set(k,v), removeItem:k=>storage.delete(k)},
    window:{ethereum:provider, addEventListener(){}, dispatchEvent(){}},
    Event:class {},
    fetch:async (url, options)=>{
      let result;
      if (url === '/api/plan') result = plan;
      else if (url === '/api/verify') result = state;
      else if (url === '/api/preview') {
        const {step} = JSON.parse(options.body);
        const transaction = {from:plan.owner, chainId:'0xaa36a7', value:'0x0',
          data:step==='deploy'?plan.creationData:plan[step+'Data'],
          gas:'0x'+plan.gasLimits[step].toString(16), maxFeePerGas:'0x'+BigInt(plan.maxFeePerGasWei).toString(16),
          maxPriorityFeePerGas:'0x'+BigInt(plan.maxPriorityFeePerGasWei).toString(16)};
        if (step !== 'deploy') transaction.to = state.contract;
        if (tamper) transaction.value = '0x1';
        result = {step, planId:plan.planId, transaction, decoded:{symbol:plan.symbol},
          gasEstimate:500000,estimatedFeeWei:'500000000000',maximumFeeWei:'4500000000000000',estimatedAtBlock:1};
      }
      else if (url === '/api/reserve') {
        const {step} = JSON.parse(options.body);
        assert.equal(state.transactions[step],undefined);
        state.transactions[step] = {requestId:'local-test-reservation',status:'AWAITING_METAMASK'};
        result = {requestId:'local-test-reservation',state};
      }
      else if (url === '/api/release') {
        const {step,requestId} = JSON.parse(options.body);
        assert.equal(state.transactions[step].requestId,requestId);
        delete state.transactions[step]; result = state;
      }
      else if (url === '/api/record') {
        const payload = JSON.parse(options.body);
        state.transactions[payload.step] = {hash:payload.hash}; result = state;
      } else throw Error('Unexpected endpoint: ' + url);
      return {ok:true,json:async()=>result};
    }
  });
  vm.runInContext(fs.readFileSync(path.join(__dirname, 'sepolia_signer.js'), 'utf8'), context);
  await new Promise(resolve=>setImmediate(resolve));
  return {plan, state, elements, storage, sent,
    evaluate:code=>vm.runInContext(code,context),
    setAccount:value=>{account=value}, setChain:value=>{chain=value}, setFailure:value=>{failure=value},
    setExtraAccount:value=>{extraAccount=value}, setTamper:value=>{tamper=value}};
}

async function main() {
  let ui = await setup(false);
  await assert.rejects(ui.evaluate('send("deploy")'), /подтверждён/);
  assert.equal(ui.sent.length,0);
  ui = await setup(true);
  await ui.evaluate('connect()');
  ui.setAccount('0x' + '2'.repeat(40));
  await assert.rejects(ui.evaluate('prepareStep("deploy")'), /один аккаунт/);
  ui.setAccount(ui.plan.owner); ui.setChain('0x1');
  await assert.rejects(ui.evaluate('send("deploy")'), /Sepolia/);
  ui.setChain('0xaa36a7');
  ui.setExtraAccount(true);
  await assert.rejects(ui.evaluate('prepareStep("deploy")'), /один аккаунт/);
  ui.setExtraAccount(false);
  await assert.rejects(ui.evaluate('prepareStep("mint")'), /Предыдущий/);
  assert.equal(ui.sent.length,0);
  await assert.rejects(ui.evaluate('send("deploy")'), /Сначала/);
  ui.setTamper(true);
  await assert.rejects(ui.evaluate('prepareStep("deploy")'), /расходятся/);
  ui.setTamper(false);
  await ui.evaluate('prepareStep("deploy")');
  assert.match(ui.elements.get('deployReview').textContent,/Estimated gas fee/);
  assert.equal(ui.sent.length,0, 'Preview must never sign/send');
  await ui.evaluate('send("deploy")');
  assert.equal(ui.sent.length,1);
  assert.equal(ui.sent[0].data,ui.plan.creationData);
  assert.equal(ui.sent[0].value,'0x0');
  assert.equal(ui.sent[0].from,ui.plan.owner);
  assert.equal(ui.sent[0].to,undefined);
  await assert.rejects(ui.evaluate('send("deploy")'), /уже отправлена/);
  assert.equal(ui.sent.length,1);
  // Uncertain wallet errors persist an in-flight guard across reloads.
  ui = await setup(true); await ui.evaluate('connect()');
  await ui.evaluate('prepareStep("deploy")');
  ui.setFailure(Error('Wallet disconnected'));
  await assert.rejects(ui.evaluate('send("deploy")'), /disconnected/);
  assert.equal([...ui.storage.keys()].filter(k=>k.endsWith('-awaiting-wallet')).length,1);
  ui.setFailure(null);
  await assert.rejects(ui.evaluate('send("deploy")'), /уже отправлена/);
  assert.equal(ui.sent.length,0);
  // Explicit rejection permits a later deliberate retry.
  ui = await setup(true); await ui.evaluate('connect()');
  await ui.evaluate('prepareStep("deploy")');
  const rejected = Error('Rejected'); rejected.code = 4001; ui.setFailure(rejected);
  await assert.rejects(ui.evaluate('send("deploy")'), /Rejected/);
  assert.equal(ui.storage.size,0);
  assert.equal(Object.keys(ui.state.transactions).length,0);
  console.log('PASS UI doubles: approval lock, exact one account + chain, step order, mandatory fee preview without signing, tampered value rejection, exact deploy payload, server reservation, duplicate/interrupted-wallet protection, explicit rejection release.');
}
main().catch(error=>{console.error(error);process.exitCode=1});
