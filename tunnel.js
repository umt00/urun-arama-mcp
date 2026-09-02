const localtunnel = require('./node_modules/localtunnel');
const fs = require('fs');

(async () => {
  try {
    const tunnel = await localtunnel({ port: 8008 });
    console.log('PUBLIC_MCP_URL: ' + tunnel.url);
    fs.writeFileSync('tunnel_url.txt', tunnel.url);
    
    tunnel.on('close', () => {
      console.log('Tunnel closed');
    });
  } catch (err) {
    console.error('Tunnel error:', err);
  }
})();
