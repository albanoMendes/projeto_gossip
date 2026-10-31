# tasks.md — Plano de Implementação (TDD)

> Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.
> Convenção TDD: para cada componente de lógica, a **primeira** tarefa escreve um teste que falha; a seguinte implementa até passar. Python 3.11+, `pytest`, `asyncio`. Identificadores/comentários em inglês; documentos em PT-BR.
>
> **Nota de dependências:** a execução deve seguir a ordem; **Task 25 depende de 6, 8, 13, 15, 17, 19, 21** e é **maior (>30 min) por composição** (exceção ao limite de 30 min).

## Fase 0 — Scaffolding
- [x] **Task 1** Estrutura de projeto (src/{aplicacao,estado,gossip,comunicacao,monitoramento}, config/, scripts/, testes/, docs/, pyproject com pytest, README stub, .gitignore). Smoke test verde.
- [x] **Task 2** Config de membership (config/members.json A–F; loader `load_members`, `Member`, `others`). Teste TDD.

## Fase 1 — Estado
- [x] **Task 3** Teste `Notice` falhando (campos, id==origem:contador, to_dict/from_dict).
- [x] **Task 4** Implementar `Notice` (dataclass frozen).
- [x] **Task 5** Teste `NoticeStore` falhando (contador sequencial; merge/dedup; idempotente/comutativo).
- [x] **Task 6** Implementar `NoticeStore` (add_local, merge, ids, all).

## Fase 2 — Comunicação
- [x] **Task 7** Teste codec JSON falhando (round-trip GOSSIP/REPLY/STATUS_*; malformado → None).
- [x] **Task 8** Implementar codec (encode/decode).
- [x] **Task 9** Teste `LossSimulator` falhando (p=0 nunca, p=1 sempre; RNG com semente).
- [x] **Task 10** Implementar `LossSimulator`.
- [x] **Task 11a** Teste loopback UDP falhando (asyncio, portas efêmeras; p=1.0 nada chega).
- [x] **Task 11b** Implementar `UdpTransport` (codec+loss+log de descarte; DatagramProtocol).
- [x] **Task 11c** Teste integração robustez — bytes malformados à porta de gossip; nó segue vivo e responde a GOSSIP válido (RF-04.3).

## Fase 3 — Seleção de pares
- [x] **Task 12** Teste `PeerSelector` fanout=2 falhando (2 distintos, nunca self, uniforme).
- [x] **Task 13** Implementar `PeerSelector` (random.sample).

## Fase 4 — Motor de gossip
- [x] **Task 14** Teste merge push-pull em um ciclo falhando (FakeTransport; união A↔B; CA-08).
- [x] **Task 15** Implementar `GossipEngine` (handle_gossip, handle_reply, send_gossip).
- [x] **Task 16** Teste ciclo periódico fanout=2 falhando (2 GOSSIP a 2 pares distintos por ciclo).
- [x] **Task 17** Implementar ciclo periódico (`run_cycle_loop` com asyncio.sleep).
- [x] **Task 17b** Teste integração push-pull com DOIS NÓS REAIS em 127.0.0.1 (CA-08 via UDP real).

## Fase 5 — Monitoramento
- [x] **Task 18** Teste logger falhando (formato `[<id>] EVENTO chave=valor`).
- [x] **Task 19** Implementar logger.
- [x] **Task 20** Teste `StatusServer` falhando (STATUS_REQUEST→STATUS_REPLY com ids; read-only).
- [x] **Task 21** Implementar `StatusServer` (DatagramProtocol separado na porta de status).
- [x] **Task 22** Teste `Panel` com timeout falhando (indisponível; cobertura sobre nós ativos).
- [x] **Task 23** Implementar `Panel` (cliente read-only, render textual).

## Fase 6 — Aplicação e integração
- [x] **Task 24** Teste CLI não bloqueante / criação falhando (`post <texto>` → add_local + CRIADO).
- [x] **Task 25** (MAIOR, depende de 6,8,13,15,17,19,21) Implementar `Node` (NoticeStore único injetado em GossipEngine e StatusServer; event loop; ciclo; CLI via asyncio.to_thread) + `main.py` (--id/--config/--interval/--fanout/--loss). `test_node_boot` sobe nó em portas efêmeras e encerra limpo.
- [x] **Task 26** Scripts de demo (`start_demo.sh` tmux/bg + `stop_demo.sh`) e `panel_main.py`.

## Fase 7 — End-to-end (critérios de aceitação)
- [x] **Task 27** CA-01/CA-02 — aviso de A alcança os 6; converge 6/6 (loopback, p=0).
- [x] **Task 28** CA-03/CA-04 — reenvio não duplica; avisos de A e B em todos.
- [x] **Task 29** CA-05 — convergência com p≈0.3 (teto amplo de ciclos + RNG com semente).
- [x] **Task 30** CA-06 — nó parado; demais convergem; painel mostra parado indisponível.
- [x] **Task 31** CA-07 — queda do painel não afeta o gossip.

## Fase 8 — Documentação e entregáveis
- [x] **Task 32** README completo (E-01/E-02): execução por processo, parâmetros, roteiro da demo, seção teórica (SI vs SIR, por que push-pull, consistência eventual) citando as referências. PT-BR, nomes dos 3 integrantes.
- [x] **Task 33a** Outline dos slides em `docs/slides_outline.md` (intro, protocolo, garantias/falha, demo; tempo por slide para 10–12 min).
- [x] **Task 33b** Slides finais `docs/slides.pptx` gerados por `scripts/make_slides.py`, com nomes dos 3 integrantes e os 3 diagramas embutidos como PNG (`scripts/make_diagrams.py` → `docs/img/*.png`).
- [x] **Task 34** Empacotamento e checklist final (E-05/E-06): `scripts/make_zip.sh` gera `Grupo7-AlbanoMendes-GustavoCunha-ArthurBastos.zip` (exclui `Docs/`, `.venv/`, caches, `.git/`; inclui `AUTHORS.md`); suíte `pytest` verde (74).
- [ ] **Task 35** Gravar o vídeo da apresentação a partir do roteiro (`docs/video_roteiro.md`); verificar duração 10–12 min e nomes visíveis; submeter no Moodle. **Requer ação manual** (gravação).

## Status da suíte
Todos os testes automatizados passam (`pytest`): unidade + integração + e2e (CA-01..CA-08).
