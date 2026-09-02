import os
import base64
import re
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from auth import get_credentials

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_service():
    creds = get_credentials()
    return build('gmail', 'v1', credentials=creds)

def get_subject(headers):
    for h in headers:
        if h['name'] == 'Subject':
            return h['value']
    return '(sem assunto)'

def get_from(headers):
    for h in headers:
        if h['name'] == 'From':
            return h['value']
    return '(desconhecido)'

def get_date(headers):
    for h in headers:
        if h['name'] == 'Date':
            return h['value']
    return ''

def listar_emails(dias=7, max_results=50):
    service = get_service()
    depois = (datetime.now() - timedelta(days=dias)).strftime('%Y/%m/%d')
    query = f'after:{depois} in:inbox'

    result = service.users().messages().list(
        userId='me', q=query, maxResults=max_results
    ).execute()

    messages = result.get('messages', [])
    if not messages:
        print(f"Nenhum email nos últimos {dias} dias.")
        return []

    emails = []
    for msg in messages:
        m = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata',
            metadataHeaders=['Subject', 'From', 'Date']
        ).execute()
        emails.append({
            'id': msg['id'],
            'assunto': get_subject(m['payload']['headers']),
            'de': get_from(m['payload']['headers']),
            'data': get_date(m['payload']['headers']),
            'snippet': m.get('snippet', ''),
            'labels': m.get('labelIds', []),
        })
    return emails

def resumir_emails(dias=7):
    emails = listar_emails(dias=dias)
    if not emails:
        return

    print(f"\n{'='*60}")
    print(f"  EMAILS DOS ÚLTIMOS {dias} DIAS — {len(emails)} mensagens")
    print(f"{'='*60}\n")

    for i, e in enumerate(emails, 1):
        lido = '' if 'UNREAD' in e['labels'] else '[lido] '
        print(f"{i:2}. {lido}{e['assunto']}")
        print(f"    De: {e['de']}")
        print(f"    {e['snippet'][:100]}...")
        print()

def apagar_email(email_id):
    service = get_service()
    service.users().messages().trash(userId='me', id=email_id).execute()
    print(f"Email {email_id} movido para lixeira.")

def apagar_varios(ids):
    for eid in ids:
        apagar_email(eid)
    print(f"\n{len(ids)} emails movidos para lixeira.")

if __name__ == '__main__':
    resumir_emails(dias=7)
