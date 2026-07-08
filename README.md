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
- ELM327 **Bluetooth** (OBD2) — comprado
- Adaptador USB Bluetooth para a torre — ainda não comprado (torre não tem Bluetooth/WiFi de fábrica)
- ESP32 + módulo relé 2 canais (automação) — ainda não comprado

## Fase 1 — Infraestrutura

- [x] Ubuntu Server 20.04 instalado
- [x] Docker + Mosquitto + PostgreSQL + Ollama
- [x] Ollama com modelo Phi-3 mini (testado, respondendo em português)
- [x] Scripts de leitura OBD2 → PostgreSQL prontos (`corsaos/obd_reader.py` no host `corsa`), aguardando dongle Bluetooth USB pra testar com hardware real
- [ ] Dashboard básico React
- [ ] Voz: Whisper + Piper TTS

## Fase 2 — Automação

- [ ] ESP32 controlando farol via MQTT
- [ ] Farol desliga automático quando motor para
- [ ] Sensores de temperatura/umidade interna
- [ ] Relé de ignição ligando/desligando o inversor automaticamente (hoje é manual)

## IA remota (Claude Code) — bloqueado por hardware

Tentativa de instalar o Claude Code CLI na torre pra servir de "cérebro remoto" (via assinatura pessoal, sem custo de API por token) falhou: o Celeron E3300 só suporta até SSSE3 (sem SSE4.2/POPCNT/AVX), e o binário do Claude Code trava com `Illegal instruction`. Sem solução via software — só migrando pra um processador mais moderno (ex: o Mini PC N100 já cogitado pra Fase 2).
