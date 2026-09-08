// Tab switching
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');
    event.currentTarget.classList.add('active');
}

// Live secret input hint
document.getElementById('secret-input').addEventListener('input', function() {
    const val = this.value;
    const charLen = val.length;
    const bitLen = charLen * 8;
    document.getElementById('secret-hint').innerText = `${charLen} characters | ${bitLen} bits`;
});

// Auto-generate Cover Text
async function handleGenerateCover() {
    try {
        const res = await fetch('/api/generate-cover', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paragraphs_count: 3 })
        });
        const data = await res.json();
        if (data.success) {
            document.getElementById('cover-input').value = data.cover_text;
        } else {
            alert('Failed to generate cover text: ' + data.detail);
        }
    } catch (err) {
        alert('Error connecting to server: ' + err.message);
    }
}

// Encode Message
async function handleEncode() {
    const secretText = document.getElementById('secret-input').value.trim();
    const coverText = document.getElementById('cover-input').value.trim();
    const password = document.getElementById('password-input').value.trim();
    const autoExpand = document.getElementById('auto-expand-check').checked;

    if (!secretText) {
        alert('Please enter a secret message to encode.');
        return;
    }

    const encodeBtn = document.getElementById('encode-btn');
    encodeBtn.innerText = '⏳ Encoding...';
    encodeBtn.disabled = true;

    try {
        const res = await fetch('/api/encode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                secret_text: secretText,
                cover_text: coverText,
                password: password,
                auto_expand: autoExpand
            })
        });

        const data = await res.json();
        if (!res.ok) {
            alert('Encoding Error: ' + (data.detail || 'Failed to encode'));
            return;
        }

        // Update metrics
        document.getElementById('metric-bleu').innerText = data.metrics.bleu_score;
        document.getElementById('metric-entropy').innerText = data.metrics.shannon_entropy;
        document.getElementById('metric-capacity').innerText = data.metrics.total_capacity_bits;
        document.getElementById('metric-carriers').innerText = data.metrics.total_carriers;

        // Update outputs
        document.getElementById('stego-output').value = data.stego_text;
        document.getElementById('key-output').value = JSON.stringify(data.key_data, null, 2);

        // Update modifications list
        const modBox = document.getElementById('mod-list');
        document.getElementById('mod-count').innerText = data.modifications.length;
        modBox.innerHTML = '';

        if (data.modifications.length === 0) {
            modBox.innerHTML = '<div style="color: var(--text-secondary); text-align: center; padding: 8px;">No words substituted</div>';
        } else {
            data.modifications.forEach(m => {
                const item = document.createElement('div');
                item.className = 'sub-item';
                item.innerHTML = `
                    <span>Pos ${m.position}: <span class="sub-orig">${m.original}</span> ➔ <span class="sub-new">${m.substituted}</span></span>
                    <span class="sub-bits">bits: ${m.bits}</span>
                `;
                modBox.appendChild(item);
            });
        }

        // Reveal result card
        document.getElementById('encode-placeholder').classList.add('hidden');
        document.getElementById('encode-output').classList.remove('hidden');

    } catch (err) {
        alert('Server error: ' + err.message);
    } finally {
        encodeBtn.innerText = '🚀 Encode & Embed Secret';
        encodeBtn.disabled = false;
    }
}

// Decode Message
async function handleDecode() {
    const stegoText = document.getElementById('decode-stego-input').value.trim();
    const keyRaw = document.getElementById('decode-key-input').value.trim();
    const password = document.getElementById('decode-password-input').value.trim();

    if (!stegoText || !keyRaw) {
        alert('Please provide both stego text and key JSON.');
        return;
    }

    let keyData;
    try {
        keyData = JSON.parse(keyRaw);
    } catch (e) {
        alert('Invalid JSON in Extraction Key field. Please check format.');
        return;
    }

    const decodeBtn = document.getElementById('decode-btn');
    decodeBtn.innerText = '⏳ Decoding...';
    decodeBtn.disabled = true;

    try {
        const res = await fetch('/api/decode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                stego_text: stegoText,
                key_data: keyData,
                password: password
            })
        });

        const data = await res.json();
        if (!res.ok) {
            alert('Decoding Error: ' + (data.detail || 'Failed to decode'));
            return;
        }

        document.getElementById('decoded-secret-output').value = data.secret_text;
        document.getElementById('decode-placeholder').classList.add('hidden');
        document.getElementById('decode-output').classList.remove('hidden');

    } catch (err) {
        alert('Server error: ' + err.message);
    } finally {
        decodeBtn.innerText = '🔓 Extract & Decode Secret';
        decodeBtn.disabled = false;
    }
}

// Copy helper
function copyToClipboard(elementId) {
    const el = document.getElementById(elementId);
    if (!el || !el.value) return;

    navigator.clipboard.writeText(el.value).then(() => {
        alert('Copied to clipboard!');
    }).catch(err => {
        alert('Failed to copy: ' + err);
    });
}
