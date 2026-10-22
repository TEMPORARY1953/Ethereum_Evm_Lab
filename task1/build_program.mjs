// Offline assembler for this program only. The final program.evm has no macros or labels.
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const source = `
PUSH0
CALLDATALOAD
PUSH0
MSTORE
PUSH0
PUSH0
MLOAD
SGT
ISZERO
PUSH2 @bad
JUMPI
PUSH1 0x40
CALLDATASIZE
LT
PUSH2 @bad
JUMPI
CALLDATASIZE
PUSH1 0x1f
AND
PUSH2 @bad
JUMPI
PUSH1 0x20
CALLDATASIZE
DIV
PUSH1 0x01
SWAP1
SUB
PUSH0
MLOAD
EQ
ISZERO
PUSH2 @bad
JUMPI
PUSH0
PUSH1 0x20
MSTORE
PUSH1 0x20
PUSH1 0x40
MSTORE
loop:
JUMPDEST
CALLDATASIZE
PUSH1 0x40
MLOAD
EQ
PUSH2 @done
JUMPI
PUSH1 0x40
MLOAD
CALLDATALOAD
PUSH1 0x60
MSTORE
PUSH1 0x20
MLOAD
PUSH1 0x60
MLOAD
ADD
PUSH1 0x80
MSTORE
PUSH1 0x20
MLOAD
PUSH1 0x80
MLOAD
XOR
PUSH1 0x60
MLOAD
PUSH1 0x80
MLOAD
XOR
AND
PUSH1 0xff
SHR
PUSH2 @bad
JUMPI
PUSH1 0x80
MLOAD
PUSH1 0x20
MSTORE
PUSH1 0x20
PUSH1 0x40
MLOAD
ADD
PUSH1 0x40
MSTORE
PUSH2 @loop
JUMP
done:
JUMPDEST
PUSH0
MLOAD
PUSH1 0x20
MLOAD
SDIV
PUSH0
MSTORE
PUSH1 0x20
PUSH0
RETURN
bad:
JUMPDEST
PUSH0
PUSH0
REVERT
`.trim().split('\n');

const labels = new Map();
let pc = 0;
for (const line of source) {
  if (line.endsWith(':')) labels.set(line.slice(0, -1), pc);
  else pc += 1 + (/^PUSH\d+ /.test(line) ? Number(line.split(' ')[0].slice(4)) : 0);
}
const output = source.filter(line => !line.endsWith(':')).map(line =>
  line.replace(/@(\w+)/g, (_, name) => {
    if (!labels.has(name)) throw new Error(`Unknown label: ${name}`);
    return `0x${labels.get(name).toString(16).padStart(4, '0')}`;
  })
).join('\n') + '\n';
const target = fileURLToPath(new URL('./program.evm', import.meta.url));
if (process.argv.includes('--check')) {
  if (fs.readFileSync(target, 'utf8') !== output) throw new Error('program.evm differs from assembler output');
} else fs.writeFileSync(target, output);
console.log(`Program: ${pc} bytes. Jump destinations: ${JSON.stringify(Object.fromEntries(labels))}`);
