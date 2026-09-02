import json
import os
import requests
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, 'zoho_token.json')

def load_tokens():
    with open(TOKEN_FILE) as f:
        return json.load(f)

def save_tokens(data):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_access_token():
    tokens = load_tokens()
    # Tenta usar o access token atual
    test = requests.get(
        "https://mail.zoho.com/api/accounts",
        headers={'Authorization': f"Zoho-oauthtoken {tokens['access_token']}"}
    )
    if test.status_code == 200:
        return tokens['access_token']
    # Renova com refresh token
    r = requests.post('https://accounts.zoho.com/oauth/v2/token', data={
        'grant_type': 'refresh_token',
        'client_id': tokens['client_id'],
        'client_secret': tokens['client_secret'],
        'refresh_token': tokens['refresh_token'],
    })
    new_tokens = r.json()
    tokens['access_token'] = new_tokens['access_token']
    save_tokens(tokens)
    return tokens['access_token']

def get_account_id():
    token = get_access_token()
    tokens = load_tokens()
    r = requests.get(
        "https://mail.zoho.com/api/accounts",
        headers={'Authorization': f"Zoho-oauthtoken {token}"}
    )
    accounts = r.json().get('data', [])
    if accounts:
        return str(accounts[0].get('accountId', ''))
    return None

def listar_emails(dias=7, max_results=50):
    token = get_access_token()
    tokens = load_tokens()
    account_id = get_account_id()
    if not account_id:
        print("Conta Zoho não encontrada.")
        return []

    r = requests.get(
        f"https://mail.zoho.com/api/accounts/{account_id}/messages/view",
        headers={'Authorization': f"Zoho-oauthtoken {token}"},
        params={'limit': max_results, 'start': 0}
    )
    data = r.json()
    emails = []
    for msg in data.get('data', []):
        if not isinstance(msg, dict):
            continue
        emails.append({
            'id': msg.get('messageId'),
            'assunto': msg.get('subject', '(sem assunto)'),
            'de': msg.get('fromAddress', ''),
            'data': msg.get('receivedTime', ''),
            'snippet': msg.get('summary', ''),
            'lido': msg.get('status', '0') == '1',
            'anexo': msg.get('hasAttachment', '0') == '1',
        })
    return emails

def resumir_emails():
    emails = listar_emails()
    if not emails:
        print("Nenhum email encontrado.")
        return

    print(f"\n{'='*60}")
    print(f"  ZOHO MAIL — {len(emails)} mensagens recentes")
    print(f"{'='*60}\n")

    for i, e in enumerate(emails, 1):
        lido = '[lido] ' if e['lido'] else ''
        anexo = ' [anexo]' if e['anexo'] else ''
        print(f"{i:2}. {lido}{e['assunto']}{anexo}")
        print(f"    De: {e['de']}")
        if e['snippet']:
            print(f"    {e['snippet'][:100]}...")
        print()

if __name__ == '__main__':
    resumir_emails()
