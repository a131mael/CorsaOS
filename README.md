# CorsaOS

Sistema inteligente para Corsa 2001 Wind — PC embarcado com IA, voz, telemetria OBD2 e automação via ESP32.

## Arquitetura

```
Tablet (Dashboard) ←→ WiFi ←→ CorsaOS Server (Ubuntu)
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                   │
               OBD2 USB          Ollama (IA)         MQTT Broker
                    │                 │                   │
               PostgreSQL        Whisper/TTS          ESP32
               (histórico)       (voz)              (farol, relés)
```

## Módulos

| Módulo | Descrição |
|--------|-----------|
| `corsa-core` | Backend Java Spring Boot — API REST + MQTT consumer |
| `corsa-dashboard` | Frontend React — interface touchscreen |
| `corsa-ai` | Integração Ollama — IA local em português |
| `corsa-voice` | Whisper (voz→texto) + Piper TTS (texto→voz) |
| `corsa-esp32` | Firmware Arduino — controle de relés via MQTT |
| `docs` | Diagramas, esquemas elétricos, documentação |

## Hardware

- PC embarcado (Ubuntu Server **20.04** — 22.04/26.04 não bootam nesse hardware, ver docs)
- Inversor 12V→220V (alimentação da torre no carro, usando a fonte ATX original)
- Tablet Android 7" (dashboard) — ainda não comprado
- ELM327 **Bluetooth** (OBD2) — comprado, aguardando teste com hardware real
- Câmera USB (webcam genérica) — **comprada e funcionando** (vídeo via UVC, microfone embutido quebrado por firmware)
- Fone/headset com microfone (P2) — **comprado**, funcionando no jack **rosa traseiro** (Rear Mic) — ver seção Áudio abaixo
- Dongle Bluetooth USB (CSR antigo) — **comprado, mas incompatível** com o BlueZ atual (chip velho demais, sem Secure Simple Pairing). Precisa trocar por um BT 4.0+
- ESP32 + módulo relé 2 canais (automação) — ainda não comprado

## Fase 1 — Infraestrutura

- [x] Ubuntu Server 20.04 instalado
- [x] Docker + Mosquitto + PostgreSQL + Ollama
- [x] Ollama com modelo Phi-3 mini (testado, respondendo em português)
- [x] Scripts de leitura OBD2 → PostgreSQL prontos (`corsaos/obd_reader.py` no host `corsa`), aguardando dongle Bluetooth funcional pra testar com hardware real
- [x] **Câmera USB** — funcionando via `ustreamer` (systemd `corsa-camera.service`, porta 8090, MJPEG passthrough)
- [x] **Dashboard React** — rodando direto na torre (build de produção servida via `python3 -m http.server`, systemd `corsa-dashboard.service`, porta 8091). Tem toggle entre "modo câmera" (câmera grande + medidores numa coluna) e "modo clássico" (3 medidores grandes, sem câmera)
- [x] **Acesso remoto via Cloudflare Tunnel** — funciona de qualquer lugar, sem precisar estar na rede do escritório/casa:
  - `corsa.fidenatto.com.br` → SSH da torre
  - `corsacam.fidenatto.com.br` → stream MJPEG da câmera
  - `painel.fidenatto.com.br` → dashboard completo
- [x] **Voz (parcial)**: `whisper.cpp` (STT) e `espeak-ng` (TTS) instalados e testados na torre — ver seção Áudio/Voz abaixo
- [ ] Voz: trocar `espeak-ng` (robótico) por Piper TTS (voz natural em português) quando o mic estiver 100%
- [ ] Backend Java Spring Boot consumindo MQTT + expondo API REST

## Áudio / Voz — status em 2026-07-08

- **Saída de áudio**: funciona no jack de fone P2 (`amixer` control "Headphone", card 0 Intel HDA)
- **Microfone**: a placa-mãe tem 5 jacks P2 físicos (2 na frente, 3 atrás), mas só 3 aceitam entrada de microfone — os outros 2 (verdes) são só saída, nunca vão captar nada:
  | Jack | Cor | Testado |
  |---|---|---|
  | Frente | Verde | Saída (HP Out) — não serve pra mic |
  | Frente | Rosa | Sinal fraco, sem fala reconhecível |
  | Trás | Azul | Line In — sinal fraco, sem fala reconhecível |
  | Trás | Verde | Saída (Line Out) — não serve pra mic |
  | Trás | **Rosa** | ✅ **Funciona** — Whisper transcreveu fala real |
  - **Usar sempre o jack rosa traseiro (Rear Mic)** para o microfone
  - Causa provável dos outros jacks falharem: contato frouxo/mau encaixe desses cabos P2 finos de fone de celular nos jacks de PC (mais largos)
- **STT (fala→texto)**: `whisper.cpp` compilado local em `~/corsaos/whisper.cpp` (evita o crash de CPU antiga, ver seção abaixo), modelos `ggml-tiny.bin` (rápido) e `ggml-base.bin` (mais preciso, ~80s pra 15s de áudio)
- **TTS (texto→fala)**: `espeak-ng` instalado, voz `pt-br`, robótica mas funcional — script de teste completo em `~/corsaos/teste_voz.sh`
- **Microfone embutido da câmera USB**: não funciona (erro de I/O na captura, firmware capado — comum em câmeras baratas tipo "xilingding")

## Câmera USB — cuidado com reboot

A câmera **não sobrevive a reboot da torre** — na inicialização, a porta USB falha em entregar energia estável a tempo (mesmo padrão de falta de energia visto em vários testes desse hardware). Reset via software (unbind/bind do controlador EHCI) **não resolve**, testado várias vezes. Único jeito de recuperar: **desconectar e reconectar o cabo USB da câmera manualmente** depois que a torre ligar.
- Solução definitiva pendente: comprar um **hub USB com fonte própria** — dá energia estável independente do timing de boot da placa-mãe.

## Bluetooth — não funciona, precisa trocar o hardware

Dongle USB genérico "BT DONGLE10" (chipset Cambridge Silicon Radio `0a12:0001`, bem antigo) é reconhecido pelo Linux mas o `bluetoothd` nunca inicializa o controlador ("No default controller available"). Testado em 3 portas USB diferentes + reboot completo — falha **determinística** e idêntica sempre, não é problema de porta/energia. Chipset provavelmente não suporta Secure Simple Pairing, exigido pelo BlueZ 5.x. **Solução: comprar um dongle Bluetooth USB mais novo (BT 4.0+)**.

## IA remota (Claude Code) — bloqueado por hardware

Tentativa de instalar o Claude Code CLI na torre pra servir de "cérebro remoto" (via assinatura pessoal, sem custo de API por token) falhou: o Celeron E3300 só suporta até SSSE3 (sem SSE4.2/POPCNT/AVX), e o binário do Claude Code trava com `Illegal instruction`. Sem solução via software — só migrando pra um processador mais moderno (ex: o Mini PC N100 já cogitado pra Fase 2). O mesmo problema de CPU antiga foi contornado pro `whisper.cpp` compilando localmente com `-march=native` em vez de usar binário pré-compilado.
