const fs = require('fs');
const jsauthPath = '../Login_Frontend/node_modules/jsauth/src/jsauth.js';
let content = fs.readFileSync(jsauthPath, 'utf8');

// Insert payload: unverified,
if (!content.includes('payload: unverified')) {
    content = content.replace('tokenId: function () {\n            return this._jti;\n        },', 'tokenId: function () {\n            return this._jti;\n        },\n        payload: unverified,');
}

fs.writeFileSync(jsauthPath, content);
console.log("Successfully patched JSAuth with payload");
