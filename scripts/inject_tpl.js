const fs = require('fs');
let s = fs.readFileSync('C:/D/opt/lingshu-work/index-logic.js', 'utf8');
const A = '["value","options","disabled"])]),Rr("p",tC,';
const first = s.indexOf(A);
if (first < 0 || s.indexOf(A, first + 1) !== -1) { console.error('anchor problem at', first); process.exit(1); }
const head = '["value","options","disabled"])]),';
const COND = '"custom"===v.value?(Cr(),Pr("label",eC,[Rr("span",null,"接口地址",-1),Ar(Ct(pg),{value:vb.value,"onUpdate:value":t[19]||(t[19]=e=>vb.value=e),placeholder:"https://your-proxy.example.com/v1",clearable:"",disabled:r.value},null,8,["value","disabled"])])):jr("",!0),';
const out = s.slice(0, first + head.length) + COND + 'Rr("p",tC,' + s.slice(first + A.length);
fs.writeFileSync('C:/D/opt/lingshu-work/index-final.js', out);
console.log('injected at', first, '| bytes:', out.length);
