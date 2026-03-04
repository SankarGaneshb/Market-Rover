const fs = require('fs');
const https = require('https');
const path = require('path');

// We will read the current generate_brands.js
const generateBrandsPath = path.join(__dirname, 'generate_brands.js');
let content = fs.readFileSync(generateBrandsPath, 'utf8');

// We need to extract all companies and their properties
// Since it's a JS file, we can't easily parse it as JSON without eval, but we can match the objects
const regex = /{ company: "([^"]+)", ticker: "([^"]+)", sector: "([^"]+)", domain: "([^"]+)", brands: (\[[^\]]+\]) }/g;

let matches = [...content.matchAll(regex)];

async function getWikiLogo(company) {
    // 1. First try exactly the company name + " logo SVG"
    let titles = await search(`"${company}" logo SVG`);
    if (titles.length > 0) return titles[0];

    // 2. Try company name + " logo"
    titles = await search(`"${company}" logo`);
    if (titles.length > 0) return titles[0];

    // 3. Try just the company name
    titles = await search(`${company} logo`);
    if (titles.length > 0) return titles[0];

    return null; // fallback needed
}

function search(query) {
    return new Promise((resolve) => {
        const url = 'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=' + encodeURIComponent(query) + '&utf8=&format=json&srnamespace=6';
        https.get(url, { headers: { 'User-Agent': 'Node/14' } }, (res) => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try {
                    let json = JSON.parse(data);
                    if (json.query && json.query.search) {
                        resolve(json.query.search.map(s => s.title.replace('File:', '')));
                    } else {
                        resolve([]);
                    }
                } catch (e) {
                    resolve([]);
                }
            });
        }).on('error', () => resolve([]));
    });
}

async function run() {
    let replacedContent = content;
    console.log(`Found ${matches.length} companies to process`);
    for (const match of matches) {
        const fullMatch = match[0];
        const company = match[1];
        const ticker = match[2];
        const sector = match[3];
        const domain = match[4];
        const brands = match[5];

        let logoFile = await getWikiLogo(company);
        if (!logoFile) {
            console.log(`[WARN] Could not find logo for ${company}, using fallback`);
            logoFile = `${company.replace(/ /g, '_')}_logo.svg`;
        } else {
            console.log(`[OK] ${company} -> ${logoFile}`);
            // If the file returned is an SVG or PNG, we accept it.
            // If it's a PDF or JPG, we might still accept it. Wikipedia resolves them.
        }

        // Replace `domain: "..."` with `logo: "..."` in the original file content
        const newText = `{ company: "${company}", ticker: "${ticker}", sector: "${sector}", logo: "${logoFile}", brands: ${brands} }`;
        replacedContent = replacedContent.replace(fullMatch, newText);

        // Let's add built-in delay to avoid API rate limits
        await new Promise(r => setTimeout(r, 200));
    }

    // Now, replace the processIndex function to use Wikipedia again.
    const oldFuncUrlRegex = /const logoUrlStr = `https:\/\/t2\.gstatic\.com\/faviconV2\?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=http:\/\/\$\{company\.domain\}&size=128`;/;
    const newFuncUrlText = `const safeFilename = encodeURIComponent(company.logo);\n            const logoUrlStr = \`https://en.wikipedia.org/wiki/Special:FilePath/\${safeFilename}\`;`;

    replacedContent = replacedContent.replace(oldFuncUrlRegex, newFuncUrlText);

    // Also remove the comment describing Google API
    replacedContent = replacedContent.replace(/\/\/ Using Google's highly reliable gstatic favicon\/brand extraction API.\n\s+\/\/ When scaling to size 128\/256, it returns the authentic, high-res Apple Touch Icon or Web Manifest Logo \n\s+\/\/ directly from the company's root page metadata instead of a tiny 16px favicon./,
        '// Generate Wikipedia File URL using Special:FilePath which handles resolution automatically');

    fs.writeFileSync(generateBrandsPath, replacedContent);
    console.log('Successfully updated generate_brands.js to use exact Wikipedia file paths!');
}

run();
