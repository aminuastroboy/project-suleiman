# small helper that returns HTML/JS for WebAuthn register/login
def get_webauthn_html():
    return """
<!doctype html>
<html>
  <head><meta charset='utf-8'></head>
  <body>
    <script>
      function ab2b64(buf) {
        var binary = '';
        var bytes = new Uint8Array(buf);
        var len = bytes.byteLength;
        for (var i = 0; i < len; i++) {
          binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
      }

      window.addEventListener('message', async function(e) {
        try {
          var data = e.data;
          if (!data || !data.action) return;
          if (data.action === 'register') {
            var opts = data.options;
            opts.publicKey.challenge = Uint8Array.from(atob(opts.publicKey.challenge.replace(/-/g,'+').replace(/_/g,'/')), c=>c.charCodeAt(0)).buffer;
            opts.publicKey.user.id = Uint8Array.from(atob(opts.publicKey.user.id.replace(/-/g,'+').replace(/_/g,'/')), c=>c.charCodeAt(0)).buffer;
            if (opts.publicKey.excludeCredentials) {
              opts.publicKey.excludeCredentials = opts.publicKey.excludeCredentials.map(c => ({type:c.type, id:Uint8Array.from(atob(c.id.replace(/-/g,'+').replace(/_/g,'/')), c2=>c2.charCodeAt(0)).buffer}));
            }
            const cred = await navigator.credentials.create({ publicKey: opts.publicKey });
            const out = { id: cred.id, rawId: ab2b64(cred.rawId), response: { attestationObject: ab2b64(cred.response.attestationObject), clientDataJSON: ab2b64(cred.response.clientDataJSON) }, type: cred.type };
            window.parent.postMessage({status:'ok', result: out}, '*');
          } else if (data.action === 'login') {
            var opts = data.options;
            opts.publicKey.challenge = Uint8Array.from(atob(opts.publicKey.challenge.replace(/-/g,'+').replace(/_/g,'/')), c=>c.charCodeAt(0)).buffer;
            if (opts.publicKey.allowCredentials) {
              opts.publicKey.allowCredentials = opts.publicKey.allowCredentials.map(c => ({type:c.type, id:Uint8Array.from(atob(c.id.replace(/-/g,'+').replace(/_/g,'/')), c2=>c2.charCodeAt(0)).buffer}));
            }
            const cred = await navigator.credentials.get({ publicKey: opts.publicKey });
            const out = { id: cred.id, rawId: ab2b64(cred.rawId), response: { authenticatorData: ab2b64(cred.response.authenticatorData), clientDataJSON: ab2b64(cred.response.clientDataJSON), signature: ab2b64(cred.response.signature), userHandle: cred.response.userHandle ? ab2b64(cred.response.userHandle) : null }, type: cred.type };
            window.parent.postMessage({status:'ok', result: out}, '*');
          }
        } catch (err) {
          window.parent.postMessage({status:'error', error: String(err)}, '*');
        }
      });
      window.parent.postMessage({status:'ready'}, '*');
    </script>
  </body>
</html>
"""
