# Sessao de autografos

Exemplo visual do problema dos leitores e escritores, feito com PySide6.

- Execute `python main.py` para abrir o evento.
- Use **ADICIONAR FÃ A FILA** para colocar mais fas no evento. A fila nao tem limite.
- Use **AUTOGRAFAR PRÓXIMO** para o autor assinar para o primeiro fa. A escrita aguarda as consultas ativas e bloqueia novas consultas enquanto houver escritor esperando.
- Use **CONSULTAR LISTA** para iniciar um leitor independente; varios leitores podem consultar ao mesmo tempo.
- Em **CONTROLE DE LEITORES**, escolha um limite de 1 a 3 e aplique-o. Consultas excedentes sao recusadas com um aviso vermelho; leitores ja aceitos terminam normalmente. **SEM LIMITE** restaura o comportamento sem limite configurado.
- A musica original do evento toca em segundo plano; use **MÚSICA: LIGADA/DESLIGADA** para controlá-la. Efeitos originais acompanham cliques, chegada de fãs, consultas e autógrafos.
- Ajuste **DURACAO DAS ACOES** para escolher o tempo de leitura e de escrita (2 a 30 segundos; inicia em 5 e 4 segundos, respectivamente). Os valores selecionados se aplicam a cada nova acao.

Instale a dependencia com `python -m pip install -r PySide6`.

A lista de autografos e o recurso compartilhado: os leitores consultam seu conteudo, e o autor o atualiza com acesso exclusivo. Os estados de espera do leitor e do fã da vez ficam destacados na tela. Os personagens caminham quando entram ou avancam na fila; o autor anima o braco enquanto assina; e cada consulta anima um leitor ate a lista e de volta. O quadro do cenario mostra as seis assinaturas mais recentes, enquanto a consulta registra a lista completa.

As faixas e os efeitos sonoros sao sintetizados localmente pelo programa; nao e necessario baixar arquivos de audio.
