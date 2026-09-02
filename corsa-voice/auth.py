import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            print("\n=== AUTENTICAÇÃO GMAIL ===")
            print("Abrindo servidor local na porta 8080...")
            print("Se o browser não abrir, copie a URL abaixo e abra no Windows:\n")
            creds = flow.run_local_server(port=0, open_browser=False,
                                          success_message='Autenticado! Pode fechar esta aba.')
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds

if __name__ == '__main__':
    get_credentials()
    print("\nAutenticação concluída! token.json salvo.")
