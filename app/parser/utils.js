const crypto = require('crypto');

function generateHash(str) {
    return crypto.createHash('sha256').update(str).digest('hex');
}

function isToday(date) {
    const now = new Date();
    return date.getDate() === now.getDate() &&
           date.getMonth() === now.getMonth() &&
           date.getFullYear() === now.getFullYear();
}

module.exports = { generateHash, isToday };