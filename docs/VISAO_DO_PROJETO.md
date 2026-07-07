# CorsaOS — Visão do Projeto

## O que é

CorsaOS é um sistema operacional embarcado para o Corsa 2001 Wind do Abimael.
O objetivo é transformar um carro popular em um veículo inteligente, com IA local, voz, telemetria em tempo real e automação elétrica — tudo desenvolvido do zero, sem depender de soluções comerciais.

## O objetivo

Criar um "cérebro" para o carro que:

- **Conhece o carro** — sabe o histórico de manutenção, consumo, falhas, viagens
- **Conversa** — você fala, ele responde em voz alta em português
- **Monitora** — RPM, velocidade, temperatura, bateria em tempo real via OBD2
- **Age** — liga farol, desliga automaticamente quando o motor para, futuras automações
- **Aprende** — registra padrões e avisa sobre anomalias antes que virem problema

## A visão final

Você entra no carro. A tela acende. O Corsa fala:

> "Boa tarde, Abimael. Bateria em 12.6V, motor frio. Você tem 1/4 de tanque.
> Na semana passada seu consumo caiu para 10.6 km/L — vale checar a pressão dos pneus."

Você fala:

> "Corsa, liga o farol."

Ele liga. Quando você desliga o motor, o farol apaga sozinho.

Meses depois você pergunta:

> "Quando troquei o óleo?"

Ele responde com data, quilometragem e observações — porque ele lembra de tudo.

## Hardware

| Item | Função |
|------|--------|
| PC velho (Ubuntu Server) | Cérebro do sistema |
| Tablet Android 7" | Tela touchscreen no painel |
| ELM327 USB | Leitura OBD2 — RPM, velocidade, temperatura, bateria |
| ESP32 + relé 2 canais | Automação elétrica — farol, travas, etc |
| Microfone USB / tablet | Entrada de voz |
| Caixa de som / tablet | Saída de voz |

## Stack de software

| Camada | Tecnologia | Por quê |
|--------|-----------|---------|
| Sistema | Ubuntu Server 22.04 | Leve, estável, perfeito para Docker |
| Containers | Docker | Isolamento, fácil migração para hardware melhor |
| MQTT | Mosquitto | Comunicação em tempo real com ESP32 |
| Banco | PostgreSQL | Histórico completo do carro |
| Backend | Java Spring Boot | Linguagem que o Abimael já domina |
| Dashboard | React | Interface HUD profissional no tablet |
| IA | Ollama + Phi-3 mini | Roda offline, sem internet, responde rápido |
| Voz entrada | Whisper | Converte fala em texto localmente |
| Voz saída | Piper TTS | Voz masculina em português, offline |
| ESP32 | Arduino/C++ | Firmware leve para controle dos relés |

## Arquitetura

```
                    INTERNET (opcional)
                          │
               ┌──────────┴──────────┐
               │                     │
         IA Remota               ChatGPT/OpenAI
         (opcional)

─────────────────────────────────────────────────

              CorsaOS Server (PC no carro)
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                   │
  OBD2 USB           Ollama (IA)        MQTT Broker
       │                  │                   │
  PostgreSQL         Whisper/TTS           ESP32
  (histórico)        (voz)              (relés/farol)
       │
  API REST
       │
  Dashboard React
       │
  Tablet Android
```

## Fases de desenvolvimento

### Fase 1 — Infraestrutura
- [ ] Ubuntu Server 22.04 instalado no PC
- [ ] Docker + Mosquitto + PostgreSQL + Ollama
- [ ] Leitura OBD2 salvando dados no banco
- [ ] API REST básica
- [ ] Dashboard React mostrando dados em tempo real
- [ ] Voz: Whisper (entrada) + Piper TTS (saída)
- [ ] IA respondendo perguntas sobre o carro

### Fase 2 — Automação
- [ ] ESP32 recebendo comandos via MQTT
- [ ] Farol liga/desliga por voz
- [ ] Farol desliga automático quando motor para (RPM=0)
- [ ] Sensores de temperatura e umidade interna

### Fase 3 — Inteligência
- [ ] IA com acesso ao histórico do banco
- [ ] Registro de manutenções por voz
- [ ] Detecção de padrões anômalos
- [ ] Alertas proativos ("consumo caiu essa semana")

### Fase 4 — Expansão
- [ ] GPS integrado
- [ ] Diagnóstico automático de falhas (códigos OBD2)
- [ ] App mobile
- [ ] Câmera de ré
- [ ] Upgrade para Mini PC mais potente com GPU

## Princípios do projeto

1. **Offline first** — tudo funciona sem internet
2. **Java no backend** — mesma stack que o Abimael já usa profissionalmente
3. **Docker desde o início** — fácil migrar para hardware melhor no futuro
4. **Modular** — cada serviço independente, um problema não derruba o resto
5. **Open source** — organizado para poder compartilhar ou evoluir para produto

## Arquitetura detalhada — ESP32 e sensores

```
              ESP32 (Power)
                    │
              Wi-Fi / MQTT
                    │
        ┌───────────┴───────────┐
        │                       │
    ESP32 (Motor)          ESP32 (Painel)
        │                       │
        └───────────┬───────────┘
                    │
             CorsaOS Server
             (Ubuntu Linux)
                    │
 ┌──────────────────────────────────────────┐
 │ MQTT │ Banco │ IA │ Dashboard │ API │ Logs│
 └──────────────────────────────────────────┘
                    │
      Tela / Celular / Tablet
```

O PC é o **cérebro** — não conversa diretamente com sensores. Quem faz isso são os ESP32. O PC **pensa**.

## Fluxo MQTT

ESP32 publica dados em tópicos:

```
corsa/power/battery     → 12.54
corsa/motor/rpm         → 1800
corsa/motor/temp        → 92
corsa/interior/humidity → 65
```

O backend Java recebe → salva no banco → IA processa → dashboard atualiza. Tudo ao mesmo tempo.

## Banco de dados — o que o carro vai lembrar

O PostgreSQL vai guardar:

- Histórico de bateria
- Consumo por viagem
- Temperatura do motor ao longo do tempo
- Falhas e códigos OBD2
- Manutenções registradas por voz
- Hábitos de direção

**O carro vai ter memória.**

## IA — dois cérebros

```
                INTERNET
                    │
         ┌──────────┴──────────┐
         │                     │
   IA Remota (opcional)   ChatGPT/OpenAI

─────────────────────────────────────────
         │
      CorsaOS
 (PC dentro do carro)
         │
  IA Local (sempre disponível)
         │
─────────────────────────────────────────
         │
      MQTT Broker
         │
 ESP32 + Sensores
```

**Comportamento:**

- "Corsa, quanto de combustível tenho?" → IA local responde em menos de 1 segundo
- "Por que o motor Ecotec carboniza válvulas?" → consulta IA remota se tiver internet
- "Quanto gastei com manutenção esse ano?" → IA consulta o banco do próprio carro

## Voz — fluxo completo

```
Microfone → Whisper → Texto → Java → IA → Resposta → Piper TTS → Alto-falante
```

Exemplo completo:

> Você: "Corsa, como está a bateria?"
> Corsa: "Bateria em 12.6 volts, nível normal."

Tudo offline, sem internet, em português.

## IA com memória do carro

Exemplo de interação meses depois de uso:

> Você: "Quando troquei o óleo?"
> Corsa: "Troca registrada em 15 de março de 2026, aos 120.000 km."

> Você: "Estou gastando mais combustível?"
> Corsa: "Sim. Nas últimas três semanas seu consumo caiu de 12.8 km/L para 10.6 km/L.
>          A principal suspeita é pressão insuficiente nos pneus ou filtro de ar sujo."

A IA aprende padrões. Exemplo:

> "Quando chove muito, o farol direito costuma falhar."

Ela registra. Meses depois, se perguntar se o problema já aconteceu, ela responde usando o histórico.

## Hardware recomendado para upgrade futuro

| Fase | Hardware | RAM |
|------|---------|-----|
| Fase 1 | PC velho | 4-8GB |
| Fase 2 | Mini PC Intel N100 | 16GB |
| Fase 3 | Mini PC + GPU NVIDIA | 32GB |

Modelo de IA por fase:
- Fase 1: Phi-3 mini (3.8B) — roda em CPU fraca
- Fase 2: Qwen2 7B — Mini PC
- Fase 3: modelo 13B+ com GPU

## Repositório

https://github.com/a131mael/CorsaOS
