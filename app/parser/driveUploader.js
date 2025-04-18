// driveUploader.js — загрузка файлов в папку "42" на Google Диск

const fs = require('fs');
const { Readable } = require('stream');
const { google } = require('googleapis');
const readline = require('readline');

const CREDENTIALS_PATH = 'credentials.json';
const TOKEN_PATH = 'token.json';
// const PARENT_FOLDER_ID = '15Ka4ST-JqIhptlWHwWvknh2bGTBunYDg'; // Удаляем жестко заданный ID

function askQuestion(query) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise(resolve => rl.question(query, answer => { rl.close(); resolve(answer); }));
}

async function authorizeGoogle() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH));
  const { client_secret, client_id, redirect_uris } = credentials.installed;
  const oAuth2Client = new google.auth.OAuth2(client_id, client_secret, redirect_uris[0]);

  if (fs.existsSync(TOKEN_PATH)) {
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH));
    oAuth2Client.setCredentials(token);
    return oAuth2Client;
  }

  const authUrl = oAuth2Client.generateAuthUrl({ access_type: 'offline', scope: ['https://www.googleapis.com/auth/drive.file'] });
  console.log('🔗 Открой ссылку для авторизации в браузере:', authUrl);
  const code = await askQuestion('🔑 Введите код авторизации: ');
  const { tokens } = await oAuth2Client.getToken(code);
  oAuth2Client.setCredentials(tokens);
  fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens));
  return oAuth2Client;
}

function extractFolderIdFromUrl(url) {
    // Ищем ID папки после /folders/
    const match = url.match(/\/folders\/([a-zA-Z0-9_-]+)/);
    if (match && match[1]) {
        return match[1];
    }
    // Если не нашли, возможно URL старого формата или невалидный
    console.warn(`Не удалось извлечь ID папки из URL: ${url}. Попытка использовать базовый URL.`);
    // Можно добавить фолбэк или выбросить ошибку
    return null; 
}

async function uploadToDrive(filename, buffer, googleDriveFolderUrl) { // Добавляем URL как аргумент
  const auth = await authorizeGoogle();
  const drive = google.drive({ version: 'v3', auth });

  // Извлекаем ID папки из URL
  const folderId = extractFolderIdFromUrl(googleDriveFolderUrl);

  if (!folderId) {
      throw new Error(`Не удалось определить ID папки Google Drive из URL: ${googleDriveFolderUrl}`);
  }

  const fileMetadata = {
    name: filename,
    parents: [folderId] // Используем извлеченный ID
  };

  const media = {
    mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    body: Readable.from(buffer)
  };

  await drive.files.create({
    requestBody: fileMetadata,
    media,
    fields: 'id'
  });
}

module.exports = { uploadToDrive };