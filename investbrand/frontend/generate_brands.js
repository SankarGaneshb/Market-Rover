const fs = require('fs');

// We use Wikipedia Special:FilePath for robust, immutable access to authentic logos.
// No hash paths, no DNS blocks, just direct filename resolution.

const nifty50 = [
    { company: "Reliance Industries", ticker: "RELIANCE", sector: "Energy", logo: "Reliance Industries Logo.svg", brands: ["Jio", "Reliance Retail"], insight: "From textiles in 1958 to a digital powerhouse today, Reliance's Jio led India's 4G revolution." },
    { company: "Tata Consultancy Services", ticker: "TCS", sector: "IT", logo: "TATA Consultancy Services Logo blue.svg", brands: ["TCS"], insight: "Founded in 1968, TCS pioneered India's IT sector and was the first in India to reach a $100B valuation." },
    { company: "HDFC Bank", ticker: "HDFCBANK", sector: "Financials", logo: "HDFC Bank Logo.svg", brands: ["HDFC Bank"], insight: "Starting with a single branch in 1995, HDFC Bank recently completed a historic mega-merger with its parent." },
    { company: "ICICI Bank", ticker: "ICICIBANK", sector: "Financials", logo: "ICICI Bank Logo.svg", brands: ["ICICI Bank", "iMobile"] },
    { company: "Infosys", ticker: "INFY", sector: "IT", logo: "Infosys Consulting logo.svg", brands: ["Infosys"] },
    { company: "State Bank of India", ticker: "SBIN", sector: "Financials", logo: "State Bank of India logo.svg", brands: ["SBI", "YONO"] },
    { company: "Bharti Airtel", ticker: "BHARTIARTL", sector: "Telecom", logo: "Bharti Airtel logo.svg", brands: ["Airtel", "Wynk Music"] },
    { company: "Hindustan Unilever", ticker: "HINDUNILVR", sector: "FMCG", logo: "Hindustan Unilever Logo.svg", brands: ["Dove", "Surf Excel", "Lifebuoy", "Lux"] },
    { company: "ITC Limited", ticker: "ITC", sector: "FMCG", logo: "ITC Limited Logo.svg", brands: ["Aashirvaad", "Sunfeast", "Bingo!", "Classmate", "Savlon"] },
    { company: "Larsen & Toubro", ticker: "LT", sector: "Industrial", logo: "Larsen-&-Toubro-Logo.svg", brands: ["L&T"] },
    { company: "Bajaj Finance", ticker: "BAJFINANCE", sector: "Financials", logo: "Bajaj Finance Logo.svg", brands: ["Bajaj Finserv"] },
    { company: "HCL Technologies", ticker: "HCLTECH", sector: "IT", logo: "HCL Technologies logo.svg", brands: ["HCLTech"] },
    { company: "Maruti Suzuki", ticker: "MARUTI", sector: "Automobile", logo: "Maruti Suzuki logo (2009).svg", brands: ["Maruti Suzuki", "NEXA", "Arena"] },
    { company: "Sun Pharmaceutical", ticker: "SUNPHARMA", sector: "Healthcare", logo: "Sun Pharmaceutical logo.svg", brands: ["Volini", "Revital"] },
    { company: "Tata Motors", ticker: "TATAMOTORS", sector: "Automobile", logo: "Tata Motors Logo.svg", brands: ["Tata Motors", "Jaguar", "Land Rover", "Nexon"] },
    { company: "Mahindra & Mahindra", ticker: "M&M", sector: "Automobile", logo: "Mahindra Rise New Logo.svg", brands: ["Mahindra", "Scorpio", "Thar", "XUV700"] },
    { company: "Asian Paints", ticker: "ASIANPAINT", sector: "Consumer", logo: "Asian Paints Logo.svg", brands: ["Asian Paints", "Royale"] },
    { company: "NTPC", ticker: "NTPC", sector: "Energy", logo: "National Thermal Power logo.svg", brands: ["NTPC"] },
    { company: "Tata Steel", ticker: "TATASTEEL", sector: "Metals", logo: "Tata Steel Logo.svg", brands: ["Tata Tiscon"] },
    { company: "Kotak Mahindra Bank", ticker: "KOTAKBANK", sector: "Financials", logo: "Kotak Mahindra Bank logo.svg", brands: ["Kotak Bank", "Kotak 811"] },
    { company: "Axis Bank", ticker: "AXISBANK", sector: "Financials", logo: "Axis Bank logo.svg", brands: ["Axis Bank"] },
    { company: "UltraTech Cement", ticker: "ULTRACEMCO", sector: "Materials", logo: "Ultratech Cement Logo.svg", brands: ["UltraTech"] },
    { company: "Titan Company", ticker: "TITAN", sector: "Consumer", logo: "Logo of Titan Company, May 2018.svg", brands: ["Titan", "Tanishq", "Fastrack"] },
    { company: "Wipro", ticker: "WIPRO", sector: "IT", logo: "Wipro Primary Logo Color RGB.svg", brands: ["Wipro", "Santoore"] },
    { company: "Nestle India", ticker: "NESTLEIND", sector: "FMCG", logo: "Nestlé logo.svg", brands: ["Maggi", "Nescafe", "KitKat"] },
    { company: "Power Grid", ticker: "POWERGRID", sector: "Energy", logo: "Power Grid Corporation of India Logo.svg", brands: ["PowerGrid"] },
    { company: "Bajaj Auto", ticker: "BAJAJ-AUTO", sector: "Automobile", logo: "Bajaj auto logo.svg", brands: ["Pulsar", "Dominar", "Chetak"] },
    { company: "ONGC", ticker: "ONGC", sector: "Energy", logo: "ONGC Logo.svg", brands: ["ONGC"] },
    { company: "Adani Enterprises", ticker: "ADANIENT", sector: "Industrial", logo: "Adani Group logo.svg", brands: ["Adani Airports", "Adani Wilmar"] },
    { company: "Adani Ports", ticker: "ADANIPORTS", sector: "Infrastructure", logo: "Adani Ports Logo.svg", brands: ["Adani Ports"] },
    { company: "Hindalco", ticker: "HINDALCO", sector: "Metals", logo: "Hindalco Logo.svg", brands: ["Hindalco", "Novelis", "Freshwrapp"] },
    { company: "Grasim Industries", ticker: "GRASIM", sector: "Materials", logo: "Aditya Birla Grasim Logo.svg", brands: ["Grasim", "UltraTech", "Liva"] },
    { company: "Tech Mahindra", ticker: "TECHM", sector: "IT", logo: "Tech Mahindra New Logo.svg", brands: ["Tech Mahindra"] },
    { company: "Dr. Reddy's", ticker: "DRREDDY", sector: "Healthcare", logo: "Dr. Reddy's Laboratories logo.svg", brands: ["Omez", "Nise"] },
    { company: "Coal India", ticker: "COALINDIA", sector: "Metals", logo: "Coal India Logo.svg", brands: ["Coal India"] },
    { company: "SBI Life", ticker: "SBILIFE", sector: "Financials", logo: "SBI Life Insurance 2022 Logo.svg", brands: ["SBI Life"] },
    { company: "Apollo Hospitals", ticker: "APOLLOHOSP", sector: "Healthcare", logo: "Apollo Hospitals Logo.svg", brands: ["Apollo Hospitals", "Apollo Pharmacy"] },
    { company: "Tata Consumer", ticker: "TATACONSUM", sector: "FMCG", logo: "Tata Consumer Products Logo.svg", brands: ["Tata Tea", "Tata Salt", "Starbucks India"] },
    { company: "Britannia Industries", ticker: "BRITANNIA", sector: "FMCG", logo: "Britannia Industries logo with motto.svg", brands: ["Good Day", "Marie Gold", "Tiger", "NutriChoice"] },
    { company: "Eicher Motors", ticker: "EICHERMOT", sector: "Automobile", logo: "Eicher Logo.svg", brands: ["Royal Enfield", "Bullet", "Classic 350"] },
    { company: "Divi's Lab", ticker: "DIVISLAB", sector: "Healthcare", logo: "Divis Laboratories logo.svg", brands: ["Divis Labs"] },
    { company: "Cipla", ticker: "CIPLA", sector: "Healthcare", logo: "Cipla logo.svg", brands: ["Cipla", "Nicotex", "Omnigel"] },
    { company: "Hero MotoCorp", ticker: "HEROMOTOCO", sector: "Automobile", logo: "Hero MotoCorp Logo.svg", brands: ["Splendor", "Passion", "Xtreme"] },
    { company: "BPCL", ticker: "BPCL", sector: "Energy", logo: "Bharat Petroleum logo.svg", brands: ["BPCL", "Speed", "Mak Lubricants"] }
];

const niftyNext50 = [
    { company: "Zomato", ticker: "ZOMATO", sector: "Consumer", logo: "Zomato logo.svg", brands: ["Zomato", "Blinkit"] },
    { company: "Bharat Electronics", ticker: "BEL", sector: "Defence", logo: "Bharat Electronics logo.svg", brands: ["BEL"] },
    { company: "Trent", ticker: "TRENT", sector: "Consumer", logo: "Trent University Logo.svg", brands: ["Westside", "Zudio", "Star Bazaar"] },
    { company: "Hindustan Aeronautics", ticker: "HAL", sector: "Defence", logo: "Hindustan Aeronautics Limited Logo.svg", brands: ["HAL", "Tejas"] },
    { company: "DLF", ticker: "DLF", sector: "Real Estate", logo: "DLF logo.svg", brands: ["DLF", "CyberHub"] },
    { company: "Siemens", ticker: "SIEMENS", sector: "Industrial", logo: "Siemens AG logo.svg", brands: ["Siemens"] },
    { company: "Varun Beverages", ticker: "VBL", sector: "FMCG", logo: "Varun Beverages.svg", brands: ["Pepsi India", "Sting", "Seven-Up", "Mirinda"] },
    { company: "Pidilite Industries", ticker: "PIDILITIND", sector: "Chemicals", logo: "Pidilite logo.svg", brands: ["Fevicol", "Dr. Fixit", "Fevi Kwik", "M-Seal"] },
    { company: "Ambuja Cements", ticker: "AMBUJACEM", sector: "Materials", logo: "Ambuja Cements.svg", brands: ["Ambuja Cement"] },
    { company: "Dabur India", ticker: "DABUR", sector: "FMCG", logo: "Dabur_India_logo.svg", brands: ["Dabur Amla", "Real Juice", "Vatika", "Hajmola", "Odonil"] },
    { company: "Godrej Consumer", ticker: "GODREJCP", sector: "FMCG", logo: "Godrej Group logo.svg", brands: ["Good Knight", "Hit", "Cinthol", "Godrej Expert"] },
    { company: "Marico", ticker: "MARICO", sector: "FMCG", logo: "Marico Logo.svg", brands: ["Parachute", "Saffola", "Set Wet", "Livon"] },
    { company: "Havells India", ticker: "HAVELLS", sector: "Consumer", logo: "Havells Logo.svg", brands: ["Havells", "Lloyd", "Crabtree"] },
    { company: "IndiGo", ticker: "INDIGO", sector: "Aviation", logo: "IndiGo logo.svg", brands: ["IndiGo"] },
    { company: "TVS Motor", ticker: "TVSMOTOR", sector: "Automobile", logo: "TVS Motor logo.svg", brands: ["Apache", "Jupiter", "NTORQ"] }
];

const niftyMidcap = [
    { company: "Voltas", ticker: "VOLTAS", sector: "Consumer", logo: "Voltas logo.svg", brands: ["Voltas", "Beko"] },
    { company: "Polycab India", ticker: "POLYCAB", sector: "Industrial", logo: "Polycab logo.svg", brands: ["Polycab"] },
    { company: "Ashok Leyland", ticker: "ASHOKLEY", sector: "Automobile", logo: "Ashok Leyland logo.svg", brands: ["Ashok Leyland"] },
    { company: "MRF", ticker: "MRF", sector: "Automobile", logo: "Madras Rubber Factory Logo.svg", brands: ["MRF Tyres"] },
    { company: "Page Industries", ticker: "PAGEIND", sector: "Textiles", logo: "Jockey International logo.svg", brands: ["Jockey"] },
    { company: "Indian Hotels", ticker: "INDHOTEL", sector: "Hospitality", logo: "Indian Hotels Company Limited logo.svg", brands: ["Taj Hotels", "Vivanta", "Ginger"] },
    { company: "Zee Entertainment", ticker: "ZEEL", sector: "Media", logo: "Zee entertainment enterprises logo.svg", brands: ["Zee TV", "Zee5", "Zee Cinema"] },
    { company: "Paytm", ticker: "PAYTM", sector: "Financials", logo: "Paytm Logo (standalone).svg", brands: ["Paytm"] },
    { company: "Nykaa", ticker: "NYKAA", sector: "Consumer", logo: "Nykaa New Logo.svg", brands: ["Nykaa", "Nykaa Fashion"] },
    { company: "IRCTC", ticker: "IRCTC", sector: "Services", logo: "IRCTC Logo.svg", brands: ["IRCTC", "Maharajas' Express"] },
    { company: "Balkrishna Industries", ticker: "BALKRISIND", sector: "Automobile", logo: "Balkrishna Tyres Logo.svg", brands: ["BKT Tyres"] }
];

const combinedBrands = [];
let idCounter = 1;

function processIndex(indexData, indexName) {
    for (const company of indexData) {
        for (const brand of company.brands) {
            const safeFilename = encodeURIComponent(company.logo);
            const logoUrlStr = `https://en.wikipedia.org/wiki/Special:FilePath/${safeFilename}`;

            combinedBrands.push({
                id: idCounter++,
                index: indexName,
                company: company.company,
                ticker: company.ticker,
                brand: brand,
                sector: company.sector,
                logoUrl: logoUrlStr,
                insight: company.insight || `${brand} is a trusted brand owned by ${company.company} (${company.ticker}) listed in the ${indexName}.`
            });
        }
    }
}

processIndex(nifty50, "Nifty 50");
processIndex(niftyNext50, "Nifty Next 50");
processIndex(niftyMidcap, "Nifty Midcap");

const fileContent = 'export const NIFTY50_BRANDS = ' + JSON.stringify(combinedBrands, null, 2) + ';\n';
fs.writeFileSync('src/data/brands.js', fileContent);
console.log(`Successfully generated brands.js with ${combinedBrands.length} brands!`);
