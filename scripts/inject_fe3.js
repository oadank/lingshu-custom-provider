const fs = require('fs');
let s = fs.readFileSync('C:/D/opt/lingshu-work/index-v2.js', 'utf8');
const from = 'p.value="deepseek",v.value="deepseek",k("deepseek"),vb.value=i.value?.llm_base_url||"",c.value=!x.value';
const to = 'v.value=i.value?.llm_provider||"deepseek",p.value="other"===(s.value.find(e=>e.id===v.value)||{}).group?"other":"primary",k(v.value),vb.value=i.value?.llm_base_url||"",c.value=!x.value';
const n = s.split(from).length - 1;
if (n !== 1) { console.error('ABORT count=' + n); process.exit(1); }
s = s.replace(from, to);
fs.writeFileSync('C:/D/opt/lingshu-work/index-v3.js', s);
console.log('OK: settings page follows saved provider | bytes:', s.length);
