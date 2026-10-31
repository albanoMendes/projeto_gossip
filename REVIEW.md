# Guia de Revisão — Grupo 7

Projeto: mural distribuído com **gossip push-pull (anti-entropia)** sobre UDP.
Integrantes: Albano Mendes, Gustavo Cunha, Arthur Bastos.

Este guia é para os colegas revisores clonarem, rodarem os testes, verem a demo e
conferirem os diagramas.

## Pré-requisitos

- **Python 3.11+** (testado em 3.12).
- **tmux** (opcional) — recomendado para a demo interativa com vários nós.
- `git`.

## Setup

```bash
git clone https://github.com/albanoMendes/projeto_gossip.git
cd projeto_gossip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

> `requirements.txt` cobre o runtime (não há dependências além da stdlib para rodar os nós).
> `requirements-dev.txt` adiciona `pytest`/`pytest-asyncio` (testes) e `python-pptx`/`Pillow`
> (geração de slides e diagramas).

## Testes

```bash
pytest
```

Esperado: **74 passed**. A suíte cobre unidade, integração UDP real e os cenários de
aceitação CA-01 a CA-08 (propagação, dedup, múltiplas origens, perda, nó parado,
painel independente, troca push-pull).

## Demo interativa (tmux)

```bash
./scripts/start_demo.sh tmux
tmux attach -t gossip
```

Na sessão tmux:
1. Janela `nodes`: seis painéis (A–F). No painel do **A**, digite:
   `post Reunião às 10h`
2. Janela `panel` (troque de janela no tmux): acompanhe o aviso `A:1` aparecendo nó a
   nó até a **cobertura 6/6**.
3. Simule falha fail-stop: no painel do **F**, pressione `Ctrl+C`.
4. Crie outro aviso no **A** (`post Prova adiada`) e confira o painel convergindo entre
   os ativos (**5/5**; F aparece como `(indisponível)`).
5. Encerre tudo:
   ```bash
   ./scripts/stop_demo.sh
   ```

## Demo alternativa (sem tmux)

```bash
./scripts/start_demo.sh background
```

Sobe os 6 nós + painel em segundo plano, com logs em `evidencias/*.log`.
Nesse modo o `post` **não** está disponível (stdin não é interativo); serve para
observar os logs de gossip/convergência. Encerre com `./scripts/stop_demo.sh`.

> Também é possível passar intervalo e perda: `./scripts/start_demo.sh tmux 0.3 0.3`
> (intervalo 0.3s, 30% de perda simulada).

## Diagramas

Os blocos **Mermaid** em `docs/design.md` renderizam automaticamente na página do
GitHub (diagrama de sequência push-pull, arquitetura asyncio, topologia + painel).
As versões em imagem embutidas nos slides estão em `docs/img/*.png` (fontes `.mmd`
ao lado).

## Divisão sugerida de revisão

- **Albano** → `docs/design.md` (foco: push-pull e seção de simplificações).
- **Gustavo** → seção teórica do `README.md` (SI vs. SIR, por que push-pull, consistência eventual).
- **Todos** → `docs/slides.pptx`, `docs/slides_outline.md`, `docs/video_roteiro.md`.

## Onde olhar o código

- `src/estado/` — modelo de aviso e store (merge/dedup).
- `src/gossip/` — seleção de pares (fanout=2) e motor push-pull + ciclo.
- `src/comunicacao/` — codec JSON, perda simulada, transporte UDP (asyncio).
- `src/monitoramento/` — logging, servidor de status e painel observador.
- `src/aplicacao/` — composição do nó, CLI não bloqueante, `main.py`.
