const https = require('https');

https.get('https://investcraft-ui-9514347926.us-central1.run.app', (res) => {
    let data = '';
    res.on('data', (d) => data += d);
    res.on('end', () => {
        // Look for the main JS file inside index.html
        const scriptMatch = data.match(/src="(\/static\/js\/main\.[a-z0-9]+\.js)"/);
        if (scriptMatch) {
            console.log('Found script tag:', scriptMatch[1]);
            const jsUrl = 'https://investcraft-ui-9514347926.us-central1.run.app' + scriptMatch[1];

            https.get(jsUrl, (jsRes) => {
                let jsData = '';
                jsRes.on('data', (d) => jsData += d);
                jsRes.on('end', () => {
                    console.log('JS Bundle Downloaded. Size:', jsData.length);
                    console.log('Contains "rounded-xl cursor-grab"?:', jsData.includes('rounded-xl cursor-grab'));
                    console.log('Contains "dayOfYear % NIFTY50_BRANDS"?:', jsData.includes('dayOfYear') && jsData.includes('NIFTY50_BRANDS'));

                    if (!jsData.includes('rounded-xl cursor-grab')) {
                        console.log('WARNING: The rounded-xl fix is MISSING from production!');
                    } else {
                        console.log('SUCCESS: The rounded-xl fix is present in production!');
                    }
                });
            });
        } else {
            console.log('Could not find main script tag in HTML');
        }
    });
}).on('error', (e) => {
    console.error("Error fetching homepage:", e);
});
