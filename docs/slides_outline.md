# Roteiro dos Slides — Difusão Epidêmica (Gossip) Push-Pull

> Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.
> Duração-alvo: **10–12 min**. Estrutura do enunciado: (a) introdução, (b) protocolo em alto nível, (c) garantias e modelo de falha, (d) demonstração.
> Os nomes dos 3 integrantes DEVEM aparecer no slide de título (E-05).

---

## Slide 1 — Título (0:30)
- Título: "Mural Distribuído com Gossip Push-Pull (Anti-Entropia)".
- Subtítulo: Trabalho 2 — Difusão epidêmica (gossip).
- Nomes dos 3 integrantes, grupo, disciplina, data.

## Slide 2 — O problema (1:00)
- Mural de avisos replicado entre 6 processos (A–F), sem servidor central.
- Um aviso criado em qualquer nó deve chegar aos demais.
- Falhas reais: mensagens se perdem, processos param.
- Pergunta-guia: como espalhar informação de forma simples, robusta e escalável?

## Slide 3 — Introdução: o que é gossip / epidemia (1:30)
- Troca **probabilística e repetida** entre pares; a informação se espalha como uma epidemia.
- Atinge todos os nós em **O(log N)** rounds com alta probabilidade.
- Propriedades: simples, escalável, robusto, convergente, descentralizado (Kermarrec & van Steen; Gossip_Medium).
- Parâmetros: **fanout** (pares por ciclo) e **ciclo/intervalo**.

## Slide 4 — SI vs. SIR (1:00)
- **SI — anti-entropia (usamos):** troca periódica e indefinida; mescla conjuntos e reduz a entropia entre réplicas; muito confiável; envia o conjunto completo (volume pequeno).
- **SIR — rumor-mongering:** propaga "boatos" por alguns rounds e expira (tombstones); menos banda, mas pode não alcançar todos.
- Justificar a escolha de SI para o cenário didático.

## Slide 5 — Por que push-pull (1:00)
- push (envio) / pull (peço) / **push-pull** (ambos).
- Push-pull é ótimo para disseminar rápido e confiável: push eficiente na fase inicial, pull na final.
- Uma troca repara diferenças nos dois sentidos → iniciador e par ficam com a **união**.
- Nota honesta: a proposta original era push-only; refinamos para push-pull (academicamente mais sólido).

## Slide 6 — Protocolo em alto nível (1:30)
- Diagrama de sequência push-pull com fanout=2 (reaproveitar o Mermaid do design.md).
- Modelo de mensagem JSON sobre UDP: `{type, sender, notices}`.
- Ciclo (~300 ms): seleciona 2 pares distintos → 2 trocas `GOSSIP → REPLY` independentes.
- Aviso imutável `origem:contador`; merge = união por id (dedup natural).

## Slide 7 — Garantias e modelo de falha (1:30)
- **Modelo de falha:** fail-stop (sem recuperação, estado só em memória) + perda de mensagens (descarte simulado).
- Sem ACK/retransmissão dirigida; reparação por trocas periódicas + redundância (fanout).
- **Garantia:** consistência eventual (merge idempotente/comutativo reduz entropia).
- Limites: sem prazo fixo; sem BFT; sem detector de falhas.

## Slide 8 — Arquitetura (1:00)
- Módulos: estado / gossip / comunicacao / monitoramento / aplicacao.
- Concorrência: um event loop asyncio por nó; `NoticeStore` único compartilhado; painel observer read-only em porta de status separada.
- Mencionar a cobertura de testes (unidade + integração + e2e, CA-01..CA-08).

## Slide 9 — Demonstração ao vivo (2:30)
Roteiro (também no README):
1. Subir 6 nós + painel; painel vazio.
2. `post` em A → acompanhar `A:1` indo a 6/6.
3. `post` em C → dois avisos convivendo (dedup).
4. Religar com `loss=0.3` → mostrar `DESCARTE_SIMULADO` e convergência mais lenta, porém completa.
5. `Ctrl+C` em F → painel `F (indisponível)`; A–E seguem convergindo.
6. Encerrar o painel → gossip dos nós continua.
- Plano B (se a demo ao vivo falhar): mostrar logs/painel gravados em vídeo.

## Slide 10 — Conclusão (0:30)
- Gossip push-pull: simples, robusto, convergente; ótimo para disseminação.
- Trade-offs: consistência eventual, banda redundante, difícil de depurar.
- Encerramento + abertura para perguntas (cada integrante responde — exigência do enunciado).

---

### Soma de tempo
0:30 + 1:00 + 1:30 + 1:00 + 1:00 + 1:30 + 1:30 + 1:00 + 2:30 + 0:30 = **12:00** (margem para ~10–11 min cortando detalhes dos slides 3/8 se necessário).

### Checklist de produção dos slides (Task 33b)
- [ ] Nomes dos 3 integrantes no slide de título.
- [ ] Reaproveitar diagramas Mermaid do `design.md` (exportar como imagem).
- [ ] 1 ideia central por slide; pouco texto, favorecer o diagrama e a demo.
- [ ] Ensaiar para caber em 10–12 min.
