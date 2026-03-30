const fs = require('fs');
const jsauthPath = '../Login_Frontend/node_modules/jsauth/src/jsauth.js';
let content = fs.readFileSync(jsauthPath, 'utf8');

// Insert const ALLOWED_OUTLETS_KEY = "allowed-outlets"; after ALLOWED_DATA_KEY
if (!content.includes('ALLOWED_OUTLETS_KEY')) {
    content = content.replace('const ALLOWED_DATA_KEY = "allowed-data";', 'const ALLOWED_DATA_KEY = "allowed-data";\n    const ALLOWED_OUTLETS_KEY = "allowed-outlets";');
}

// Insert _allowed_outlets: unverified[ALLOWED_OUTLETS_KEY] || [],
if (!content.includes('_allowed_outlets')) {
    content = content.replace('_allowed_data: unverified[ALLOWED_DATA_KEY] || [],', '_allowed_data: unverified[ALLOWED_DATA_KEY] || [],\n        _allowed_outlets: unverified[ALLOWED_OUTLETS_KEY] || [],');
}

// Insert allowedOutlets: function () { return this._allowed_outlets; },
if (!content.includes('allowedOutlets:')) {
    content = content.replace('allowedData: function () {\n            return this._allowed_data;\n        },', 'allowedData: function () {\n            return this._allowed_data;\n        },\n        allowedOutlets: function () {\n            return this._allowed_outlets;\n        },');
}

fs.writeFileSync(jsauthPath, content);
console.log("Successfully patched JSAuth with allowed-outlets");
