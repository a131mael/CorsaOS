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

- PC embarcado (Ubuntu Server 22.04)
- Tablet Android 7" (dashboard)
- ELM327 USB (OBD2)
- ESP32 + módulo relé 2 canais (automação)

## Fase 1 — Infraestrutura

- [ ] Ubuntu Server 22.04 instalado
- [ ] Docker + Mosquitto + PostgreSQL
- [ ] Ollama com modelo Phi-3 mini
- [ ] Leitura OBD2 → banco de dados
- [ ] Dashboard básico React
- [ ] Voz: Whisper + Piper TTS

## Fase 2 — Automação

- [ ] ESP32 controlando farol via MQTT
- [ ] Farol desliga automático quando motor para
- [ ] Sensores de temperatura/umidade interna
