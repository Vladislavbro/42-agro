// driveUploader.js — загрузка файлов в папку "42" на Google Диск

const fs = require('fs');
const { Readable } = require('stream');
const { google } = require('googleapis');
const readline = require('readline');

const CREDENTIALS_PATH = 'credentials.json';
const TOKEN_PATH = 'token.json';
const PARENT_FOLDER_ID = '15Ka4ST-JqIhptlWHwWvknh2bGTBunYDg'; // ID новой папки

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



async function uploadToDrive(filename, buffer) {
  const auth = await authorizeGoogle();
  const drive = google.drive({ version: 'v3', auth });

  const folderId = PARENT_FOLDER_ID;

  const fileMetadata = {
    name: filename,
    parents: [folderId]
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