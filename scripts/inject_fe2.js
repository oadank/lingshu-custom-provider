const fs = require('fs');
let s = fs.readFileSync('C:/D/opt/lingshu-work/index-final.js', 'utf8');

const edits = [
  // 1) state: 在 vb 后加 xm（拉取到的模型列表）
  ['state xm', 'f=bt(""),vb=bt(""),h=bt(!1),', 'f=bt(""),vb=bt(""),xm=bt([]),h=bt(!1),'],
  // 2) 模型版本下拉: custom 时用拉取结果 + filterable/tag 手输
  [
    'model select',
    'Ar(Ct(Rg),{value:f.value,"onUpdate:value":t[3]||(t[3]=e=>f.value=e),options:y.value,disabled:r.value},null,8,["value","options","disabled"])',
    'Ar(Ct(Rg),{value:f.value,"onUpdate:value":t[3]||(t[3]=e=>f.value=e),options:"custom"===v.value&&xm.value.length?xm.value.map(e=>({label:e,value:e})):y.value,filterable:"custom"===v.value,tag:"custom"===v.value,disabled:r.value},null,8,["value","options","filterable","tag","disabled"])',
  ],
  // 3) 接口地址输入框下加"拉取模型列表"按钮
  [
    'fetch models button',
    ',null,8,["value","disabled"])])):jr("",!0),Rr("p",tC,',
    ',null,8,["value","disabled"]),Ar(Ct(xg),{size:"tiny",quaternary:"",style:{"margin-top":"8px"},onClick:t[20]||(t[20]=()=>{iw("/api/settings/remote-models?provider=custom").then(e=>{xm.value=e.models||[]})})},{default:en(()=>[Br("拉取模型列表",-1)]),_:1})])):jr("",!0),Rr("p",tC,',
  ],
];

for (const [name, from, to] of edits) {
  const n = s.split(from).length - 1;
  if (n !== 1) { console.error('ABORT [' + name + '] count=' + n); process.exit(1); }
  s = s.replace(from, to);
  console.log('OK:', name);
}
fs.writeFileSync('C:/D/opt/lingshu-work/index-v2.js', s);
console.log('written index-v2.js', s.length);
