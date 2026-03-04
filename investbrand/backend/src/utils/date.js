/**
 * Core Date Utility to enforce Indian Standard Time (IST) 
 * across the application, irrespective of the server's timezone.
 */

// Returns exactly YYYY-MM-DD in IST
const getIstDateString = (date = new Date()) => {
    // IST is UTC + 5:30
    const istOffsetMs = 5.5 * 60 * 60 * 1000;
    const istDate = new Date(date.getTime() + istOffsetMs);
    return istDate.toISOString().split('T')[0];
};

module.exports = {
    getIstDateString
};
