from collections import deque

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QCloseEvent, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from audio import AudioEvento
from cenario import CenarioAutografos, PixelView
from models import AutorWorker, Fa, LeitorWorker, TravaLeitoresEscritores


class JanelaAutografos(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.trava = TravaLeitoresEscritores()
        self.autografos: list[str] = []
        self._lista_exibida: tuple[str, ...] = ()
        self.fila: deque[Fa] = deque()
        self._proximo_fa_id = 1
        self._proximo_leitor_id = 1
        self._numero_leitores_ativos = 0
        self._leitores_aguardando: set[int] = set()
        self._limite_leitores: int | None = None
        self._workers: set[object] = set()
        self._escritor_ocupado = False

        self.setWindowTitle("Noite de autografos - Leitores e escritores")
        self.setMinimumSize(1040, 760)
        self.setStyleSheet(
            """
            QWidget {
                background: #211e39;
                color: #f2e8c9;
                font-family: Consolas, monospace;
                font-size: 13px;
            }
            QLabel#titulo { color: #ffe28a; font-size: 22px; font-weight: bold; }
            QLabel#subtitulo { color: #c0badc; }
            QLabel#estado {
                background: #312944;
                color: #ffe28a;
                border: 3px solid #e6a858;
                padding: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QGroupBox {
                color: #ffe28a;
                border: 2px solid #6d5b79;
                margin-top: 8px;
                padding: 7px;
                font-size: 14px;
                font-weight: bold;
            }
            QSpinBox {
                background: #17172c;
                color: #fff3d4;
                border: 2px solid #6d5b79;
                padding: 5px;
                min-width: 90px;
                font-size: 15px;
            }
            QPushButton {
                background: #a34f68;
                color: #fff3d4;
                border: 3px solid #e6a858;
                padding: 10px 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #bd6175; }
            QPushButton:disabled {
                background: #51475d;
                color: #aaa1ad;
                border-color: #786779;
            }
            QTextEdit {
                background: #17172c;
                color: #d7edcf;
                border: 3px solid #6d5b79;
                padding: 7px;
                selection-background-color: #80506c;
            }
            """
        )

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(14)

        area_evento = QVBoxLayout()
        area_evento.setSpacing(10)
        layout.addLayout(area_evento, stretch=1)

        titulo = QLabel("NOITE DE AUTOGRAFOS")
        titulo.setObjectName("titulo")
        subtitulo = QLabel(
            "Leitores consultam juntos; o autor atualiza a lista com acesso exclusivo."
        )
        subtitulo.setObjectName("subtitulo")
        area_evento.addWidget(titulo)
        area_evento.addWidget(subtitulo)

        painel_lateral = QWidget()
        painel_lateral.setFixedWidth(300)
        controles_laterais = QVBoxLayout(painel_lateral)
        controles_laterais.setContentsMargins(0, 0, 0, 0)
        controles_laterais.setSpacing(10)

        painel_tempos = QGroupBox("DURAÇÃO DAS AÇÕES")
        controles_tempos = QVBoxLayout(painel_tempos)
        controles_tempos.addWidget(QLabel("Consulta da lista:"))
        self.tempo_leitura = QSpinBox()
        self.tempo_leitura.setRange(2, 30)
        self.tempo_leitura.setValue(5)
        self.tempo_leitura.setSuffix(" s")
        self.tempo_leitura.setToolTip(
            "Tempo em que os leitores mantêm a lista aberta."
        )
        controles_tempos.addWidget(self.tempo_leitura)
        controles_tempos.addWidget(QLabel("Autógrafo:"))
        self.tempo_escrita = QSpinBox()
        self.tempo_escrita.setRange(2, 30)
        self.tempo_escrita.setValue(4)
        self.tempo_escrita.setSuffix(" s")
        self.tempo_escrita.setToolTip(
            "Tempo em que o autor mantém a lista bloqueada para escrever."
        )
        controles_tempos.addWidget(self.tempo_escrita)
        controles_laterais.addWidget(painel_tempos)

        painel_leitores = QGroupBox("CONTROLE DE LEITORES")
        controles_leitores = QVBoxLayout(painel_leitores)
        linha_limite = QHBoxLayout()
        linha_limite.addWidget(QLabel("Máximo simultâneo:"))
        self.limite_leitores = QSpinBox()
        self.limite_leitores.setRange(1, 3)
        self.limite_leitores.setValue(2)
        self.limite_leitores.setToolTip(
            "Limita a quantidade de consultas simultâneas entre 1 e 3."
        )
        linha_limite.addWidget(self.limite_leitores)
        controles_leitores.addLayout(linha_limite)
        self.botao_limitar = QPushButton("APLICAR LIMITE")
        self.botao_ilimitado = QPushButton("SEM LIMITE")
        self.botao_musica = QPushButton("MÚSICA: LIGADA")
        self.botao_limitar.clicked.connect(self._aplicar_limite_leitores)
        self.botao_ilimitado.clicked.connect(self._liberar_limite_leitores)
        self.botao_musica.clicked.connect(self._alternar_musica)
        controles_leitores.addWidget(self.botao_limitar)
        controles_leitores.addWidget(self.botao_ilimitado)
        controles_leitores.addWidget(self.botao_musica)
        controles_laterais.addWidget(painel_leitores)

        self.cenario = CenarioAutografos()
        self.visao = PixelView(self.cenario)
        self.visao.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.visao.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        self.visao.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.visao.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.visao.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.visao.setMinimumHeight(380)
        self.visao.setStyleSheet("border: 3px solid #6d5b79;")
        area_evento.addWidget(self.visao, stretch=1)

        painel_acoes = QGroupBox("AÇÕES DO EVENTO")
        botoes = QVBoxLayout(painel_acoes)
        self.botao_adicionar = QPushButton("ADICIONAR FÃ À FILA")
        self.botao_autografo = QPushButton("AUTOGRAFAR PRÓXIMO")
        self.botao_consulta = QPushButton("CONSULTAR LISTA")
        self.botao_adicionar.clicked.connect(self.adicionar_fa)
        self.botao_autografo.clicked.connect(self.autografar_proximo)
        self.botao_consulta.clicked.connect(self.consultar_lista)
        botoes.addWidget(self.botao_adicionar)
        botoes.addWidget(self.botao_autografo)
        botoes.addWidget(self.botao_consulta)
        controles_laterais.addWidget(painel_acoes)
        controles_laterais.addStretch(1)
        layout.addWidget(painel_lateral)

        self.estado = QLabel("Evento aberto. Os fãs aguardam na fila.")
        self.estado.setObjectName("estado")
        self.estado.setWordWrap(True)
        area_evento.addWidget(self.estado)
        self.registro = QTextEdit()
        self.registro.setReadOnly(True)
        self.registro.setMaximumHeight(95)
        self.registro.setPlaceholderText("As ações do evento aparecerão aqui.")
        area_evento.addWidget(self.registro)

        self.setCentralWidget(central)
        self.setMinimumSize(1200, 760)
        self.resize(1480, 850)

        self.audio = AudioEvento()
        self.audio.erro.connect(
            lambda mensagem: self._registrar(mensagem, "#ff6262")
        )
        if self.audio.aviso:
            self._registrar(self.audio.aviso, "#ff6262")
        else:
            self.audio.definir_musica(True)
        estado_musica = "LIGADA" if self.audio.musica_ativa else "DESLIGADA"
        self.botao_musica.setText(f"MÚSICA: {estado_musica}")
        self.botao_musica.setEnabled(self.audio.disponivel)
        botoes_com_som = (
            self.botao_adicionar,
            self.botao_autografo,
            self.botao_consulta,
            self.botao_limitar,
            self.botao_ilimitado,
            self.botao_musica,
        )
        for botao in botoes_com_som:
            botao.clicked.connect(lambda: self.audio.tocar("clique"))

        for _ in range(4):
            self.adicionar_fa(animar=False, registrar=False)
        self._registrar("Evento iniciado: quatro fãs aguardam o autógrafo.")

    def _registrar(self, mensagem: str, cor: str = "#d7edcf") -> None:
        cursor = self.registro.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        formato = self.registro.currentCharFormat()
        formato.setForeground(QColor(cor))
        cursor.insertText(mensagem + "\n", formato)
        self.registro.setTextCursor(cursor)
        self.registro.ensureCursorVisible()

    def _acompanhar_worker(self, worker) -> None:
        self._workers.add(worker)
        worker.finished.connect(self._remover_worker)
        worker.start()

    def _remover_worker(self) -> None:
        worker = self.sender()
        if hasattr(worker, "isRunning"):
            self._workers.discard(worker)
            worker.deleteLater()

    def adicionar_fa(self, animar: bool = True, registrar: bool = True) -> None:
        fa = Fa(
            id=self._proximo_fa_id,
            nome=f"Fã {self._proximo_fa_id}",
            aparencia=self._proximo_fa_id - 1,
        )
        self._proximo_fa_id += 1
        self.fila.append(fa)
        self.cenario.sincronizar_fila(list(self.fila), animar=animar)
        if registrar:
            self.audio.tocar("chegada")
        self.botao_autografo.setEnabled(
            bool(self.fila) and not self._escritor_ocupado
        )
        if len(self.fila) == 1 and not self._escritor_ocupado:
            self.cenario.atualizar_estado_fa(
                f"{fa.nome.upper()}: AGUARDANDO PARA SER AUTOGRAFADO",
                "#f5c66a",
            )
        if registrar:
            self._registrar(f"{fa.nome} entrou no fim da fila.")
        self._atualizar_estado()

    def _aplicar_limite_leitores(self) -> None:
        self._limite_leitores = self.limite_leitores.value()
        self._registrar(
            f"Limite aplicado: até {self._limite_leitores} leitor(es) "
            "simultâneo(s)."
        )

    def _liberar_limite_leitores(self) -> None:
        self._limite_leitores = None
        self._registrar("Limite removido: consultas sem limite configurado.")

    def _alternar_musica(self) -> None:
        ativa = self.audio.definir_musica(not self.audio.musica_ativa)
        estado = "LIGADA" if ativa else "DESLIGADA"
        self.botao_musica.setText(f"MÚSICA: {estado}")

    def consultar_lista(self) -> None:
        quantidade_reservada = (
            self._numero_leitores_ativos + len(self._leitores_aguardando)
        )
        if (
            self._limite_leitores is not None
            and quantidade_reservada >= self._limite_leitores
        ):
            self._registrar(
                "Máximo de Leitores alcançado. Aguarde ao menos 1 leitor "
                "terminar a consulta.",
                "#ff6262",
            )
            return

        leitor_id = self._proximo_leitor_id
        self._proximo_leitor_id += 1
        duracao = self.tempo_leitura.value()
        self._leitores_aguardando.add(leitor_id)
        self.cenario.atualizar_estado_leitor(
            f"LEITOR {leitor_id}: AGUARDANDO ACESSO",
            "#f5c66a",
        )
        self.estado.setText(
            f"LEITOR {leitor_id}: AGUARDANDO ACESSO À LISTA"
        )
        worker = LeitorWorker(
            leitor_id, self.trava, self.autografos, duracao
        )
        worker.mensagem.connect(self._registrar)
        worker.entrou.connect(self._leitor_entrou)
        worker.consulta_concluida.connect(self._consulta_concluida)
        self._acompanhar_worker(worker)

    def _leitor_entrou(self, leitor_id: int, duracao: int) -> None:
        self._leitores_aguardando.discard(leitor_id)
        self._numero_leitores_ativos += 1
        self.audio.tocar("passos")
        self.audio.tocar("consulta")
        self.cenario.atualizar_leitores(self._numero_leitores_ativos)
        self.cenario.iniciar_consulta(leitor_id, duracao)
        self.cenario.atualizar_estado_leitor(
            f"LEITOR {leitor_id}: CONSULTANDO LISTA",
            "#256044",
        )
        if self._leitores_aguardando:
            self.estado.setText(
                f"LEITOR {min(self._leitores_aguardando)}: "
                "AGUARDANDO ACESSO À LISTA"
            )
        else:
            self.estado.setText(
                f"LEITOR {leitor_id}: CONSULTANDO A LISTA"
            )

    def _consulta_concluida(
        self, leitor_id: int, autografos: tuple[str, ...]
    ) -> None:
        self._leitores_aguardando.discard(leitor_id)
        if len(autografos) >= len(self._lista_exibida):
            self._lista_exibida = autografos
        self.cenario.atualizar_lista(self._lista_exibida)
        self._numero_leitores_ativos = max(0, self._numero_leitores_ativos - 1)
        self.cenario.atualizar_leitores(self._numero_leitores_ativos)
        if self._leitores_aguardando:
            self.cenario.atualizar_estado_leitor(
                f"LEITOR {min(self._leitores_aguardando)}: AGUARDANDO ACESSO",
                "#f5c66a",
            )
        elif self._numero_leitores_ativos:
            self.cenario.atualizar_estado_leitor(
                f"{self._numero_leitores_ativos} LEITOR(ES): CONSULTANDO",
                "#256044",
            )
        else:
            self.cenario.atualizar_estado_leitor(
                "LEITOR: CONSULTA CONCLUÍDA",
                "#385d68",
            )
        conteudo = (
            ", ".join(autografos)
            if autografos
            else "a lista ainda esta vazia"
        )
        self._registrar(f"Consulta concluída: {conteudo}.")
        self._atualizar_estado()

    def autografar_proximo(self) -> None:
        if self._escritor_ocupado or not self.fila:
            return

        fa = self.fila[0]
        self._escritor_ocupado = True
        self.botao_autografo.setEnabled(False)
        self.cenario.atualizar_estado_fa(
            f"{fa.nome.upper()}: AGUARDANDO PARA SER AUTOGRAFADO",
            "#f5c66a",
        )
        self.cenario.atualizar_escritor("AGUARDANDO", "#f5c66a")
        self.estado.setText(f"O autor aguarda para autografar para {fa.nome}.")

        worker = AutorWorker(
            fa,
            self.trava,
            self.autografos,
            self.tempo_escrita.value(),
        )
        worker.mensagem.connect(self._registrar)
        worker.comecou_a_assinar.connect(self._autor_comecou)
        worker.autografo_concluido.connect(self._autografo_concluido)
        self._acompanhar_worker(worker)

    def _autor_comecou(self, fa_id: int, nome: str) -> None:
        self.audio.iniciar_escrita()
        self.cenario.iniciar_autografo(fa_id, nome)
        if self._leitores_aguardando:
            self.estado.setText(
                f"LEITOR {min(self._leitores_aguardando)}: "
                "AGUARDANDO ACESSO À LISTA"
            )
        else:
            self.estado.setText(f"O autor está autografando para {nome}.")

    def _autografo_concluido(
        self,
        fa_id: int,
        nome: str,
        autografos: tuple[str, ...],
    ) -> None:
        if not self.fila or self.fila[0].id != fa_id:
            raise RuntimeError("A ordem da fila mudou durante o autógrafo.")

        self.audio.parar_escrita()
        self.fila.popleft()
        self._escritor_ocupado = False
        self._lista_exibida = autografos
        self.cenario.finalizar_autografo(
            fa_id, list(self.fila), self._lista_exibida
        )
        if self.fila:
            self.cenario.atualizar_estado_fa(
                f"{self.fila[0].nome.upper()}: AGUARDANDO PARA SER AUTOGRAFADO",
                "#f5c66a",
            )
        else:
            self.cenario.atualizar_estado_fa(
                "FILA VAZIA: ADICIONE UM FÃ",
                "#c7c5e8",
            )
        self._registrar(
            f"{nome} recebeu o autógrafo. Total: {len(autografos)}."
        )
        self.botao_autografo.setEnabled(bool(self.fila))
        self._atualizar_estado()

    def _atualizar_estado(self) -> None:
        if self._escritor_ocupado:
            return
        if self._leitores_aguardando:
            self.estado.setText(
                f"LEITOR {min(self._leitores_aguardando)}: "
                "AGUARDANDO ACESSO À LISTA"
            )
            return
        if self._numero_leitores_ativos:
            self.estado.setText(
                f"{self._numero_leitores_ativos} leitor(es) consultando; "
                f"{len(self.autografos)} autógrafo(s) na lista."
            )
        elif self.fila:
            self.estado.setText(
                f"{self.fila[0].nome.upper()}: AGUARDANDO PARA SER AUTOGRAFADO"
            )
        else:
            self.estado.setText("Fila vazia. Adicione um fã para continuar.")

    def closeEvent(self, event: QCloseEvent) -> None:
        if any(worker.isRunning() for worker in self._workers):
            self.estado.setText("Aguarde as consultas e o autógrafo terminarem.")
            event.ignore()
            return
        self.audio.encerrar()
        event.accept()
