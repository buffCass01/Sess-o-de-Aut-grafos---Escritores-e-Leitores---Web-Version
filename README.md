# Noite de autógrafos — versão web

Versão para navegador da simulação de leitores e escritores da aplicação PySide6. Não requer Python, instalação de pacotes, conexão com a internet nem ferramentas de build.

## Como abrir

- Abra `index.html` diretamente em um navegador moderno; ou

- hospede esta pasta em qualquer servidor estático, servindo `index.html` como página inicial; ou

- Clique no link hospedado no GitHub Pages.

- [Hospedagem no GitHub Pages](https://buffcass01.github.io/Sess-o-de-Aut-grafos---Escritores-e-Leitores---Web-Version/)

## Recursos

- A fila começa com quatro fãs e pode crescer sem limite.
- O botão **AUTOGRAFAR PRÓXIMO** atende o primeiro fã e usa exclusão mútua para atualizar a lista. A escrita aguarda leitores ativos e bloqueia novas consultas enquanto estiver esperando.
- **CONSULTAR LISTA** permite consultas simultâneas. O limite é opcional e, quando aplicado, varia de 1 a 3 leitores.
- Os tempos de consulta e autógrafo podem ser definidos entre 2 e 30 segundos.
- O cenário pixel art, a lista compartilhada, os estados e o registro são atualizados durante a simulação.
- Música e efeitos são sintetizados no navegador. Devido às políticas de reprodução automática dos navegadores, o áudio começa após a primeira interação com a página.

O navegador executa as ações com temporizadores JavaScript em vez de threads do Python. A fila de acesso mantém a mesma regra de prioridade para escritores e permite leitores simultâneos.
