import os
import re
import json
import signal
import subprocess
from datetime import datetime

import requests
from flask import Flask, jsonify
from groq import Groq
import psycopg2

import gmail
import zoho

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WHISPER_DIR = os.path.expanduser('~/corsaos/whisper.cpp')
PIPER_BIN = os.path.expanduser('~/corsaos/piper/piper/piper')
PIPER_VOICE = os.path.expanduser('~/corsaos/piper/vozes/pt_BR-faber-medium.onnx')
AUDIO_FILE = '/tmp/corsa_fala.wav'
PID_FILE = '/tmp/corsa_arecord.pid'
MIC_DEVICE = 'plughw:0,0'

with open(os.path.join(BASE_DIR, 'config.json')) as f:
    CONFIG = json.load(f)

groq_client = Groq(api_key=CONFIG['groq_api_key'])

WHATSAPP_URL = CONFIG['whatsapp_url']
WHATSAPP_APIKEY = CONFIG['whatsapp_apikey']
WHATSAPP_INSTANCE = CONFIG['whatsapp_instance']

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

DB_DSN = "host=localhost port=5432 dbname=corsaos user=corsa password=safeliand"


def db():
    return psycopg2.connect(DB_DSN)


def falar(texto):
    piper = subprocess.Popen(
        [PIPER_BIN, '-m', PIPER_VOICE, '--output_raw'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    aplay = subprocess.Popen(
        ['aplay', '-q', '-D', MIC_DEVICE, '-r', '22050', '-f', 'S16_LE', '-t', 'raw'],
        stdin=piper.stdout, stderr=subprocess.DEVNULL
    )
    piper.stdout.close()
    piper.stdin.write(texto.encode('utf-8'))
    piper.stdin.close()
    aplay.wait()
    piper.wait()


def normalizar_telefone(numero):
    digitos = re.sub(r'\D', '', numero)
    if digitos.startswith('55') and len(digitos) >= 12:
        return '+' + digitos
    if len(digitos) in (8, 9):
        digitos = '48' + digitos
    if not digitos.startswith('55'):
        digitos = '55' + digitos
    return '+' + digitos


def transcrever():
    cmd = [
        f'{WHISPER_DIR}/build/bin/whisper-cli',
        '-m', f'{WHISPER_DIR}/models/ggml-tiny.bin',
        '-f', AUDIO_FILE,
        '-l', 'pt', '--best-of', '1', '--beam-size', '1', '-nt'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    linhas = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
    return linhas[-1] if linhas else ''


def classificar_intencao(texto):
    agora = datetime.now().strftime('%A, %d/%m/%Y %H:%M')
    system = f"""Você é o roteador de comandos de voz do assistente do carro Corsa. Data/hora atual: {agora} (America/Sao_Paulo).

Dado o texto transcrito da fala do motorista, retorne APENAS um JSON com a intenção detectada.

Intenções possíveis:
- "compromissos_hoje": perguntar sobre compromissos, agenda, lembretes de hoje ou pendências importantes
- "resumo_email": pedir pra checar/resumir email
- "salvar_verdade": pedir pra guardar uma informação importante na memória (ex: "lembra que...", "adiciona isso na memória", "guarda essa informação")
- "salvar_contato": pedir pra salvar um contato (ex: "salva o contato fulano, número tal")
- "adicionar_compromisso": marcar um compromisso/lembrete/rotina novo
- "resumo_whatsapp": pedir pra checar o WhatsApp, ver se tem mensagem/conversa pendente
- "enviar_whatsapp": pedir pra mandar uma mensagem de WhatsApp pra alguém
- "desconhecido": qualquer outra coisa

Campos por intenção:
- salvar_verdade: {{"conteudo": "..."}}
- salvar_contato: {{"nome": "...", "telefone": "..."}} (telefone como foi falado, dígitos)
- adicionar_compromisso: {{"titulo": "...", "data_hora": "YYYY-MM-DD HH:MM ou null", "prioridade": "alta|media|baixa", "recorrencia": "diaria|semanal|mensal|nome do dia da semana|null"}}
- enviar_whatsapp: {{"destinatario": "nome da pessoa", "mensagem": "texto a enviar"}}

Responda SOMENTE com JSON: {{"intent": "...", "params": {{...}}}}"""

    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": texto},
        ],
        temperature=0,
        max_tokens=300,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"intent": "desconhecido", "params": {}}


def acao_compromissos_hoje():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT titulo, data_hora, prioridade, tipo, recorrencia
        FROM compromissos
        WHERE status = 'pendente' AND (
            data_hora::date = CURRENT_DATE
            OR (data_hora IS NULL AND recorrencia IS NOT NULL)
            OR prioridade = 'alta'
        )
        ORDER BY prioridade DESC, data_hora ASC NULLS LAST
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return "Sem compromissos pra hoje, e nada importante pendente."

    partes = []
    for titulo, data_hora, prioridade, tipo, recorrencia in rows:
        quando = data_hora.strftime('às %H:%M') if data_hora else (f"({recorrencia})" if recorrencia else "sem hora marcada")
        urgencia = " — prioridade alta" if prioridade == 'alta' else ""
        partes.append(f"{titulo} {quando}{urgencia}")
    return "Você tem: " + "; ".join(partes) + "."


def acao_resumo_email():
    gmail_emails = gmail.listar_emails(dias=3, max_results=30)
    zoho_emails = zoho.listar_emails(max_results=30)

    def fmt(emails, fonte):
        linhas = []
        for e in emails:
            lido = e.get('lido')
            if lido is None:
                lido = 'UNREAD' not in e.get('labels', [])
            flag = 'NAO LIDO' if not lido else 'lido'
            linhas.append(f"- [{flag}] De: {e['de']} | Assunto: {e['assunto']} | {e['snippet'][:120]}")
        return f"=== {fonte} ===\n" + ("\n".join(linhas) if linhas else "Nenhum email.")

    contexto = fmt(gmail_emails, "GMAIL PESSOAL") + "\n\n" + fmt(zoho_emails, "ZOHO PROFISSIONAL")

    prompt = f"""Resuma os emails abaixo pro Abimael ouvir em voz alta no carro. Seja MUITO direto: no máximo 4 frases faladas, sem markdown, sem listas, só o que é urgente ou importante (boletos, vencimentos, cobranças, algo que precisa de ação hoje). Se não tiver nada urgente, diga isso em uma frase.

{contexto}"""

    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


def acao_salvar_verdade(params):
    conteudo = params.get('conteudo', '').strip()
    if not conteudo:
        return "Não entendi o que guardar."
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO verdades (conteudo) VALUES (%s)", (conteudo,))
    conn.commit()
    cur.close()
    conn.close()
    return "Guardado."


def acao_salvar_contato(params):
    nome = params.get('nome', '').strip()
    telefone = params.get('telefone', '').strip()
    if not nome or not telefone:
        return "Faltou nome ou telefone."
    telefone_normalizado = normalizar_telefone(telefone)
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO contatos (nome, telefone) VALUES (%s, %s)", (nome, telefone_normalizado))
    conn.commit()
    cur.close()
    conn.close()
    return f"Contato {nome} salvo."


def acao_adicionar_compromisso(params):
    titulo = params.get('titulo', '').strip()
    if not titulo:
        return "Não entendi o compromisso."
    data_hora = params.get('data_hora') or None
    prioridade = params.get('prioridade') or 'media'
    recorrencia = params.get('recorrencia') or None
    tipo = 'compromisso' if data_hora else ('rotina' if recorrencia else 'lembrete')
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO compromissos (titulo, data_hora, prioridade, recorrencia, tipo) VALUES (%s, %s, %s, %s, %s)",
        (titulo, data_hora, prioridade, recorrencia, tipo)
    )
    conn.commit()
    cur.close()
    conn.close()
    return f"{titulo}, anotado."


def buscar_contato(nome):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT nome, telefone FROM contatos WHERE nome ILIKE %s ORDER BY id LIMIT 1", (nome.strip(),))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def acao_enviar_whatsapp(params):
    destinatario = params.get('destinatario', '').strip()
    mensagem = params.get('mensagem', '').strip()
    if not destinatario or not mensagem:
        return "Faltou pra quem ou o que mandar."

    contato = buscar_contato(destinatario)
    if not contato:
        return f"Não tenho o contato de {destinatario} salvo."

    nome_real, telefone = contato
    numero = telefone.lstrip('+')
    try:
        r = requests.post(
            f"{WHATSAPP_URL}/message/sendText/{WHATSAPP_INSTANCE}",
            headers={"apikey": WHATSAPP_APIKEY, "Content-Type": "application/json"},
            json={"number": numero, "textMessage": {"text": mensagem}},
            timeout=15,
        )
        r.raise_for_status()
        return f"Mensagem enviada pra {nome_real}."
    except Exception as e:
        return f"Não consegui enviar pra {nome_real}: {e}"


def _nome_por_telefone(jid):
    numero = jid.split('@')[0]
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT nome FROM contatos WHERE telefone LIKE %s LIMIT 1", (f"%{numero[-8:]}",))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else numero


def acao_resumo_whatsapp():
    try:
        r = requests.get(
            f"{WHATSAPP_URL}/chat/findChats/{WHATSAPP_INSTANCE}",
            headers={"apikey": WHATSAPP_APIKEY},
            timeout=15,
        )
        r.raise_for_status()
        chats = r.json()
    except Exception as e:
        return f"Não consegui checar o WhatsApp: {e}"

    individuais = [c['id'] for c in chats if c.get('id', '').endswith('@s.whatsapp.net') and c['id'] != '0@s.whatsapp.net']

    pendentes = []
    for jid in individuais[:20]:
        try:
            r = requests.post(
                f"{WHATSAPP_URL}/chat/findMessages/{WHATSAPP_INSTANCE}",
                headers={"apikey": WHATSAPP_APIKEY, "Content-Type": "application/json"},
                json={"where": {"key.remoteJid": jid}, "limit": 1},
                timeout=10,
            )
            msgs = r.json()
        except Exception:
            continue
        if not msgs:
            continue
        m = msgs[0]
        if m.get('key', {}).get('fromMe'):
            continue
        texto = m.get('message', {}).get('conversation') or m.get('message', {}).get('extendedTextMessage', {}).get('text', '')
        if not texto:
            continue
        nome = _nome_por_telefone(jid)
        pendentes.append((nome, texto))

    if not pendentes:
        return "Sem mensagens pendentes no WhatsApp."

    partes = [f"{nome}: {texto[:60]}" for nome, texto in pendentes[:5]]
    return f"Você tem {len(pendentes)} conversa(s) esperando resposta: " + "; ".join(partes) + "."


def processar(texto):
    resultado = classificar_intencao(texto)
    intent = resultado.get('intent', 'desconhecido')
    params = resultado.get('params', {})

    if intent == 'compromissos_hoje':
        return acao_compromissos_hoje()
    if intent == 'resumo_email':
        return acao_resumo_email()
    if intent == 'salvar_verdade':
        return acao_salvar_verdade(params)
    if intent == 'salvar_contato':
        return acao_salvar_contato(params)
    if intent == 'adicionar_compromisso':
        return acao_adicionar_compromisso(params)
    if intent == 'resumo_whatsapp':
        return acao_resumo_whatsapp()
    if intent == 'enviar_whatsapp':
        return acao_enviar_whatsapp(params)
    return "Ainda não sei fazer isso."


@app.route('/mic/start', methods=['POST'])
def mic_start():
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)
    proc = subprocess.Popen([
        'arecord', '-D', MIC_DEVICE, '-f', 'S16_LE', '-r', '16000', '-c', '1', AUDIO_FILE
    ])
    with open(PID_FILE, 'w') as f:
        f.write(str(proc.pid))
    return jsonify({"ok": True})


@app.route('/mic/stop', methods=['POST'])
def mic_stop():
    if not os.path.exists(PID_FILE):
        return jsonify({"ok": False, "erro": "gravação não estava ativa"}), 400
    with open(PID_FILE) as f:
        pid = int(f.read().strip())
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    os.remove(PID_FILE)

    import time
    time.sleep(0.5)

    try:
        texto = transcrever()
    except Exception as e:
        return jsonify({"ok": False, "erro": f"transcrição falhou: {e}"}), 500

    if not texto:
        return jsonify({"ok": True, "transcript": "", "resposta": "Não ouvi nada."})

    try:
        resposta = processar(texto)
    except Exception as e:
        resposta = f"Deu erro processando: {e}"

    falar(resposta)
    return jsonify({"ok": True, "transcript": texto, "resposta": resposta})


@app.route('/system/reboot', methods=['POST'])
def system_reboot():
    """Reinicia a torre. Requer sudoers.d/corsa-reboot liberando 'reboot' sem senha
    pro usuário corsa (feito uma vez na instalação, não é permissão geral de sudo)."""
    try:
        subprocess.Popen(['sudo', '-n', '/sbin/reboot'])
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500
    return jsonify({"ok": True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8094)
