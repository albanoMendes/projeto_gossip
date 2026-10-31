# Mural Distribuído com Gossip Push-Pull (Anti-Entropia)

> **Revisores:** consulte [REVIEW.md](REVIEW.md).

Trabalho 2 — Seminários de Sistemas Distribuídos · Tema 11: **Difusão epidêmica (gossip)**.

Aplicação de exemplo que replica um **mural de avisos** entre 6 processos independentes
(nós **A–F**) usando um protocolo **gossip push-pull** na variante **anti-entropia (SI)**
sobre **UDP**. Um aviso criado em qualquer nó se espalha para os demais sem servidor
central, tolerando **perda de mensagens** e **parada de processos** (fail-stop), com
garantia de **consistência eventual**.

## Integrantes

**Grupo 7**

- Albano Mendes
- Gustavo Cunha
- Arthur Bastos

---

## 1. Requisitos de ambiente

- **Python 3.11+** (desenvolvido e testado em 3.12).
- Nenhuma dependência de runtime além da biblioteca padrão (`asyncio`, `json`, `socket`).
- Dependências apenas de teste: `pytest`, `pytest-asyncio`.
- Opcional para a demo interativa: **tmux** (cada nó em um painel próprio).

### Instalação

```bash
# na raiz do projeto
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Como executar cada processo

Cada nó é um processo independente, iniciado com o próprio `--id`. Todos leem a mesma
configuração de membership (`config/members.json`), que lista endereço e portas (gossip e
status) de A–F.

```bash
# um terminal por nó (A–F):
python -m src.aplicacao.main --id A
python -m src.aplicacao.main --id B
python -m src.aplicacao.main --id C
python -m src.aplicacao.main --id D
python -m src.aplicacao.main --id E
python -m src.aplicacao.main --id F
```

Parâmetros configuráveis (todos opcionais):

| Flag         | Padrão                 | Descrição                                        |
|--------------|------------------------|--------------------------------------------------|
| `--id`       | (obrigatório)          | Identificador do nó (A–F).                        |
| `--config`   | `config/members.json`  | Caminho do arquivo de membership.                 |
| `--interval` | `0.3`                  | Intervalo entre ciclos de gossip, em segundos.    |
| `--fanout`   | `2`                    | Número de pares contatados por ciclo.             |
| `--loss`     | `0.0`                  | Probabilidade de descarte simulado (0.0–1.0).     |

### Criar um aviso (CLI não bloqueante)

Em qualquer nó, digite no terminal:

```
post Apresentação do seminário às 10h
```

O aviso recebe o id `origem:contador` (ex.: `A:1`) e entra imediatamente nas próximas
trocas. O gossip continua rodando enquanto o nó aguarda comandos.

### Encerrar um nó (fail-stop)

`Ctrl+C` encerra o processo. O estado é mantido apenas em memória e **não** é recuperado.
Os demais nós continuam trocando informações normalmente.

---

## 3. Painel de observação (observador read-only)

```bash
python -m src.monitoramento.panel_main --interval 1.0
```

O painel consulta periodicamente a **porta de status dedicada** de cada nó e mostra, por
aviso, quais nós já o conhecem e a cobertura observada sobre os nós ativos:

```
Aviso: A:1

  Nó   Conhece?
  A    SIM
  B    SIM
  C    NÃO
  D    SIM
  E    NÃO
  F    (indisponível)

Cobertura observada: 3 de 5 nós ativos
```

O painel **não** distribui avisos, **não** escolhe pares e **não** participa da
replicação. Se o painel for encerrado, o gossip continua inalterado.

---

## 4. Demonstração com um comando (opcional)

Com **tmux** instalado, o script abre os 6 nós (cada um em um painel interativo) e o
painel em janela separada:

```bash
scripts/start_demo.sh            # interval=0.3s, loss=0.0
scripts/start_demo.sh 0.3 0.3    # interval=0.3s, loss=0.3 (30% de perda)
tmux attach -t gossip            # anexar à sessão
scripts/stop_demo.sh             # encerrar tudo
```

Sem tmux, o script sobe os processos em segundo plano com logs em `evidencias/*.log`
(nesse modo o `post` não está disponível porque não há stdin interativo).

### Roteiro sugerido para a demo ao vivo (10–12 min)

1. Suba os 6 nós + painel. Mostre o painel: "nenhum aviso ainda".
2. Em **A**, `post Reunião às 10h`. Acompanhe `A:1` se espalhando (SIM aparecendo nó a nó) até **6 de 6**.
3. Em **C**, `post Prova adiada`. Mostre dois avisos convivendo (dedup por id).
4. Suba a perda: reinicie com `scripts/start_demo.sh 0.3 0.3`. Mostre `DESCARTE_SIMULADO` nos logs e a convergência mais lenta, porém completa.
5. Encerre **F** com `Ctrl+C`. Painel mostra `F (indisponível)`; A–E continuam convergindo.
6. Encerre o painel. Mostre nos logs que o gossip dos nós continua.

---

## 5. Testes

```bash
pytest
```

A suíte cobre unidades (modelo, store/merge, codec, perda, seleção de pares, logger,
status, painel), integração (UDP real, robustez a bytes malformados) e os cenários de
aceitação ponta a ponta:

| Teste e2e                         | Cenário                                              |
|-----------------------------------|------------------------------------------------------|
| `test_e2e_propagation`            | CA-01/CA-02: aviso criado em A chega aos 6 nós        |
| `test_e2e_duplicate_multi`        | CA-03/CA-04: sem duplicata; avisos de origens distintas |
| `test_e2e_loss`                   | CA-05: convergência com ~30% de perda                 |
| `test_e2e_crash`                  | CA-06: nó parado; demais convergem; painel indisponível |
| `test_e2e_panel_independent`      | CA-07: queda do painel não afeta o gossip             |
| `test_push_pull_integration`      | CA-08: troca push-pull via UDP deixa ambos com a união |

---

## 6. Estrutura do projeto

```
.
├── src/
│   ├── aplicacao/      # config, Node (composição), CLI não bloqueante, main
│   ├── estado/         # Notice (imutável), NoticeStore (merge/dedup)
│   ├── gossip/         # PeerSelector (fanout=2), GossipEngine (push-pull + ciclo)
│   ├── comunicacao/    # codec JSON, LossSimulator, UdpTransport (asyncio)
│   └── monitoramento/  # logger, StatusServer, Panel, panel_main
├── config/members.json # membership fixo A–F (host, porta de gossip, porta de status)
├── scripts/            # start_demo.sh / stop_demo.sh
├── testes/             # pytest (unidade, integração, e2e)
└── docs/               # requirements.md, design.md, tasks.md, slides
```

---

## 7. Explicação teórica

### 7.1 Gossip / difusão epidêmica

Gossip é a troca **probabilística e repetida** de informação entre pares: a cada ciclo,
um nó escolhe aleatoriamente outro(s) e troca estado. A informação se espalha como uma
epidemia, atingindo todos os nós em **O(log N)** rounds com alta probabilidade. As
propriedades centrais são simplicidade, escalabilidade, robustez a falhas e
**comportamento convergente** (Kermarrec & van Steen).

Dois parâmetros guiam a disseminação:
- **fanout** — quantos pares um nó contata por ciclo (aqui, **2**);
- **ciclo/intervalo** — com que frequência o nó dispara gossip (aqui, **~300 ms**).

### 7.2 SI (anti-entropia) vs. SIR (rumor-mongering)

- **SI — anti-entropia (o que usamos):** os nós trocam estado **periodicamente e
  indefinidamente**; a cada troca comparam/mesclam conjuntos para **reduzir a entropia**
  entre réplicas. Converge de forma muito confiável, mas envia um número ilimitado de
  mensagens (não há término). No nosso volume pequeno, cada troca envia o **conjunto
  completo** de avisos — simples e suficiente.
- **SIR — rumor-mongering (não usamos):** um aviso é um "boato" propagado ativamente por
  alguns rounds e depois marcado como "removido" (deixa de ser espalhado). Usa menos
  banda, mas tem probabilidade não nula de **não** alcançar todos. Exigiria tombstones e
  controle de rounds — fora do escopo didático.

Referência prática: a anti-entropia "reduz a entropia entre réplicas" comparando e
corrigindo diferenças; o rumor-mongering "inunda a rede" com os updates recentes e os
expira após alguns rounds (Gossip_Medium).

### 7.3 Por que push-pull

Estratégias de troca: **push** (envio o meu estado), **pull** (peço o estado do outro) e
**push-pull** (os dois). Adotamos **push-pull**:

- É **ótimo para disseminar updates de forma rápida e confiável**: o push é eficiente na
  fase inicial (poucos nós informados) e o pull é eficiente na fase final (muitos nós já
  informados) — Gossip_Medium.
- Uma **única** troca repara diferenças nos **dois** sentidos: após `GOSSIP → REPLY`, o
  iniciador e o par ficam com a **união** dos conjuntos (modelo thread ativa + thread
  passiva de Kermarrec & van Steen).

> **Nota de projeto:** a proposta original do colega (`Docs/Albano_Design.md`) descrevia
> apenas *push* periódico e listava push-pull como fora de escopo. Trocamos para
> **push-pull** por ser a escolha academicamente mais sólida e por acelerar a convergência
> na demo. A justificativa completa está em `docs/design.md`.

### 7.4 Modelo de falha e garantia

- **Modelo de falha:** **fail-stop** (um processo pode parar e não se recupera; estado só
  em memória) + **perda de mensagens** (descarte simulado configurável em qualquer GOSSIP
  ou REPLY). Não há ACK por aviso nem retransmissão dirigida; a reparação vem das trocas
  periódicas e dos múltiplos caminhos (redundância *a priori*).
- **Garantia: consistência eventual.** Cessadas novas inserções, havendo comunicação
  suficiente e desde que ao menos um nó ativo retenha cada aviso, todos os nós ativos
  convergem para o mesmo conjunto. O merge é **união idempotente e comutativa**, base
  formal da convergência. Não se promete entrega em prazo fixo.

### Referências

- A.-M. Kermarrec, M. van Steen. *Gossiping in Distributed Systems.* (`Docs/Gossiping in Distributed Systems.md`)
- *What Is Gossip Protocol?* — visão prática de anti-entropia, rumor-mongering e push-pull. (`Docs/Gossip_Medium.md`)
- Proposta interna de design: `Docs/Albano_Design.md`.

> Conteúdo das referências foi parafraseado/resumido para fins didáticos.
