# Proposta de implementação — Mural distribuído com Gossip

## 1. Problema

Implementar um mural de avisos replicado entre seis processos independentes. Um aviso criado em qualquer processo deve se espalhar pelos demais sem depender de um servidor central responsável por distribuí-lo.

Cada processo mantém seu próprio conjunto de avisos em memória. Durante a propagação, os conjuntos podem ser diferentes; após trocas suficientes, os processos ativos devem conhecer os mesmos avisos, desde que a comunicação permita a disseminação.

O objetivo é demonstrar o funcionamento do protocolo gossip, e não desenvolver um sistema completo de mensagens.

## 2. Ideia da solução

Cada processo representa um nó do sistema, identificado por uma letra de A a F e configurado com um endereço e uma porta UDP ou TCP.

A cada segundo, cada nó:

1. Escolhe aleatoriamente outro participante.
2. Envia o conjunto de avisos que conhece.
3. Continua recebendo mensagens dos demais participantes.

Ao receber uma mensagem, o nó adiciona somente os avisos que ainda não conhece. Os avisos recebidos passam a fazer parte das próximas trocas.

Assim, um nó que aprendeu um aviso também ajuda a propagá-lo.

## 3. O que será replicado

Serão replicados avisos pequenos e imutáveis.

Cada aviso contém:

- Identificador único.
- Nó de origem.
- Contador local da origem.
- Texto.

Exemplo:

    id: A:1
    origem: A
    contador: 1
    texto: Apresentação do seminário às 10h.

O próximo aviso criado em A será A:2. Um aviso criado em B poderá ter o identificador B:1.

Não haverá edição nem exclusão. Isso mantém a demonstração concentrada na disseminação, sem exigir resolução de conflitos entre alterações.

### Regra de incorporação

    Se o identificador ainda não existe:
        adicionar o aviso ao conjunto local.

    Se o identificador já existe:
        ignorar a duplicata.

Receber o mesmo aviso várias vezes não cria novas cópias no mural.

## 4. Funcionamento do protocolo

### Criação de um aviso

O usuário insere um aviso somente em A:

    A: {A:1}
    B: {}
    C: {}
    D: {}
    E: {}
    F: {}

### Propagação

Uma sequência possível de contatos é:

    A ── envia A:1 ──> B
    B ── envia A:1 ──> D
    A ── envia A:1 ──> C
    D ── envia A:1 ──> F
    C ── envia A:1 ──> E

Ao final:

    A: {A:1}
    B: {A:1}
    C: {A:1}
    D: {A:1}
    E: {A:1}
    F: {A:1}

Essa sequência é ilustrativa. A seleção aleatória pode repetir destinatários, e mensagens podem ser perdidas. Portanto, não existe um número fixo de ciclos para concluir a propagação.

### Troca com mais de um aviso

Antes da comunicação:

    A: {A:1, B:1}
    C: {B:1}

A envia seu conjunto para C:

    A ── {A:1, B:1} ──> C

C adiciona A:1 e ignora B:1, que já conhece:

    C: {A:1, B:1}

A repetição periódica dessas trocas permite reparar diferenças entre os conjuntos locais.

## 5. Perdas e falhas demonstradas

### Perda de mensagens

Será possível configurar uma probabilidade de descarte simulado no envio.

Exemplo:

    A tenta enviar para C.
    A mensagem é descartada.

    Depois:
    A envia para B.
    B aprende o aviso.
    B envia para C.
    C aprende o aviso.

Não haverá ACK por aviso nem retransmissão dirigida como no Stop-and-Wait. A recuperação de perdas ocorrerá pelas próximas trocas periódicas e por diferentes caminhos de propagação.

### Parada de um processo

Um participante poderá ser encerrado durante a demonstração:

    F é encerrado.
    A, B, C, D e E continuam trocando informações.

O objetivo será mostrar a propagação entre os processos que permanecem ativos. Não será implementado um detector de falhas: os demais nós poderão continuar escolhendo F como destinatário.

Se um nó criar um aviso e parar antes de compartilhar qualquer cópia, o aviso será perdido, pois o estado será mantido somente em memória.

## 6. Visualização da demonstração

Cada nó registrará eventos simples:

    [A] CRIADO aviso=A:1
    [A] ENVIADO destino=B avisos=1
    [B] NOVO aviso=A:1 recebido_de=A
    [B] ENVIADO destino=D avisos=1
    [D] NOVO aviso=A:1 recebido_de=B
    [A] DESCARTE_SIMULADO destino=C

Um painel textual apresentará o estado observado:

    Aviso: A:1

    Nó    Conhece o aviso?
    A     SIM
    B     SIM
    C     NÃO
    D     SIM
    E     NÃO
    F     NÃO

    Cobertura observada: 3 de 6 nós

O painel será apenas um observador. Ele não distribuirá avisos, não escolherá os pares e não participará da replicação. Se o painel parar, o gossip continuará funcionando.



## 7. O que será implementado

- Seis processos com estados locais independentes.
- Lista fixa de participantes.
- Criação de avisos em qualquer nó.
- Identificação dos avisos por origem e contador.
- Comunicação UDP.
- Escolha aleatória de um destinatário por ciclo.
- Envio periódico do conjunto completo de avisos.
- Incorporação de avisos desconhecidos.
- Tratamento de duplicatas.
- Limites pequenos de tamanho e quantidade de avisos.
- Simulação de perda de mensagens.
- Demonstração com um processo encerrado.
- Logs e painel textual.
- Instruções de execução e roteiro de testes.

## 8. O que ficará de fora

| Funcionalidade                                | Motivo                                                           |
|-----------------------------------------------|------------------------------------------------------------------|
| Entrada e saída dinâmica de participantes     | O grupo será definido na inicialização                           |
| Recuperação após reinício                     | O estado será mantido somente em memória                         |
| Persistência em banco ou arquivos             | Não é necessária para demonstrar a propagação                    |
| Edição e exclusão de avisos                   | Evita acrescentar resolução de conflitos                         |
| Eleição de líder e consenso                   | Não fazem parte do objetivo da difusão                           |
| Detector de falhas                            | Parar um processo não exige implementar suspeitas ou heartbeats  |
| ACK por aviso                                 | A reparação ocorrerá por trocas periódicas                       |
| Pull e push-pull                              | Será implementada apenas a variante de envio periódico           |
| Resumos, hashes e envio somente de diferenças | O conjunto pequeno permite enviar o estado completo              |
| Criptografia e autenticação                   | Fora do escopo didático proposto                                 |
| Interface gráfica ou aplicação web            | Logs e painel textual serão suficientes                          |
| Grandes volumes de dados                      | O exemplo utilizará poucos avisos pequenos                       |

## 9. Condições e limitações

A demonstração considera processos não maliciosos, mensagens que podem ser perdidas e processos que podem parar.

Espera-se convergência quando:

- Pelo menos um nó ativo conserva cada aviso.
- Os nós ativos conseguem se comunicar.
- As trocas periódicas continuam.
- A escolha dos pares e a entrega permitem que os avisos alcancem os participantes.

Não será prometida entrega em um prazo fixo. Uma execução bem-sucedida demonstra o comportamento naquele cenário, mas não prova entrega sob qualquer condição de rede.

## 10. Estrutura de diretórios

    projeto_gossip/
    ├── src/
    │   ├── aplicacao/ Inicialização dos nós e comandos locais
    │   ├── estado/ Avisos, identificadores e incorporação sem duplicatas
    │   ├── gossip/ Ciclo periódico e seleção aleatória de pares
    │   ├── comunicacao/  UDP ou TCP, mensagens e perdas simuladas
    │   └── monitoramento/ Logs e painel de observação
    ├── config/ Participantes, endereços, portas e parâmetros
    ├── scripts/ Inicialização e encerramento da demonstração
    ├── testes/   Cenários e procedimentos de verificação
    ├── docs/ Material explicativo e slides
    └── evidencias/ Registros dos testes executados

## 11. Cenários mínimos de teste

| Cenário                           | Resultado esperado                           |
|-----------------------------------|----------------------------------------------|
| Aviso criado em A                 | O aviso aparece inicialmente somente em A    |
| Propagação normal                 | Os seis nós passam a conhecer o aviso        |
| Recepção repetida                 | O aviso não é duplicado no estado local      |
| Avisos criados em nós diferentes  | Os conjuntos locais passam a conter ambos    |
| Perda simulada de mensagens       | Trocas futuras permitem disseminar os avisos |
| Um nó encerrado                   | Os demais continuam propagando               |
| Painel encerrado                  | A comunicação entre os nós continua          |

## 12. Resultado esperado

A implementação deve permitir observar uma informação inicialmente local se espalhando por contatos aleatórios entre processos independentes.

O público deve conseguir identificar:

1. Onde o aviso foi criado.
2. Como ele passou de um nó para outro.
3. Por que mensagens repetidas não duplicam o estado.
4. Como trocas futuras compensam perdas.
5. Por que os nós podem divergir temporariamente antes de convergir.