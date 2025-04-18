const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('messages.db');

function initDb() {
    db.serialize(() => {
        db.run(`
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                chat TEXT,
                text TEXT,
                timestamp TEXT,
                processed_at TEXT DEFAULT NULL
            )
        `);
        db.run("ALTER TABLE messages ADD COLUMN processed_at TEXT DEFAULT NULL", (err) => {
            if (err && !err.message.includes('duplicate column name')) {
                console.error("Ошибка при добавлении столбца processed_at:", err);
            }
        });
    });
}

function isMessageProcessed(id) {
    return new Promise((resolve, reject) => {
        db.get('SELECT 1 FROM messages WHERE id = ?', [id], (err, row) => {
            if (err) return reject(err);
            resolve(!!row);
        });
    });
}

function saveMessage(id, chat, text, timestamp) {
    return new Promise((resolve, reject) => {
        db.run(
            'INSERT INTO messages (id, chat, text, timestamp) VALUES (?, ?, ?, ?)',
            [id, chat, text, timestamp.toISOString()],
            (err) => {
                if (err) return reject(err);
                resolve();
            }
        );
    });
}

module.exports = { initDb, isMessageProcessed, saveMessage };