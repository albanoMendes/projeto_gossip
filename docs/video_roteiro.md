# Roteiro e checklist do vídeo (E-06)

> Vídeo de apresentação do Trabalho 2 — Gossip Push-Pull (anti-entropia).
> Duração-alvo: **10–12 min** (mesma da apresentação). Cada integrante deve falar.

## Divisão sugerida entre os 3 integrantes

| Trecho | Conteúdo | Slides | Tempo | Quem |
|--------|----------|--------|-------|------|
| 1 | Título + problema + introdução a gossip | 1–3 | ~3:00 | Albano Mendes |
| 2 | SI vs SIR + por que push-pull + protocolo em alto nível + garantias/falha | 4–7 | ~4:00 | Gustavo Cunha |
| 3 | Arquitetura + demonstração ao vivo + conclusão | 8–10 | ~4:00 | Arthur Bastos |

Ajustar para somar 10–12 min; ensaiar uma vez cronometrando.

## Roteiro de narração da demo (trecho 3)

1. "Subimos os seis nós A–F e o painel observador." — rodar `scripts/start_demo.sh` e `tmux attach -t gossip`.
2. "Nenhum aviso ainda." — mostrar o painel vazio.
3. "Crio um aviso no nó A." — no painel do A: `post Reunião às 10h`. Narrar o `A:1` aparecendo nó a nó no painel até **6 de 6**.
4. "Avisos de origens diferentes convivem." — no C: `post Prova adiada`; mostrar os dois no painel.
5. "Agora com 30% de perda." — parar, `scripts/start_demo.sh 0.3 0.3`, mostrar `DESCARTE_SIMULADO` nos logs e a convergência mais lenta porém completa.
6. "Falha fail-stop." — `Ctrl+C` no F; painel marca `F (indisponível)`; A–E continuam convergindo.
7. "O painel é só observador." — encerrar o painel; mostrar nos logs que o gossip dos nós continua.

## Checklist de gravação

- [ ] Nomes dos 3 integrantes visíveis (slide de título e/ou na tela).
- [ ] Áudio claro; terminal com fonte legível.
- [ ] Mostrar os logs `[X] ENVIADO/NOVO/DESCARTE_SIMULADO` durante a demo.
- [ ] Mostrar o painel convergindo para a cobertura total.
- [ ] Duração final entre 10 e 12 minutos.
- [ ] Exportar em formato comum (MP4) e enviar pelo Moodle junto com slides e código.

## Comando de gravação de tela (exemplos — ação manual)

- Linux (ffmpeg + X11): `ffmpeg -video_size 1920x1080 -framerate 25 -f x11grab -i :0.0 -f pulse -i default apresentacao.mp4`
- Ou usar OBS Studio / gravador do sistema operacional.

> A gravação em si é uma ação manual do grupo; este roteiro serve de guia.
