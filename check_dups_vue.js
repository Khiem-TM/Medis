const fs = require('fs');
const content = fs.readFileSync('frontend/src/views/LandingView.vue', 'utf8');

const { parse } = require('@vue/compiler-sfc');
try {
  parse(content);
  console.log("No parse error");
} catch(e) {
  console.log("Parse error:", e.message, e.loc);
}
