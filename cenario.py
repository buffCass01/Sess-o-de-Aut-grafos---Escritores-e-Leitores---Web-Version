from PySide6.QtCore import (
    QEasingCurve,
    QPauseAnimation,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QPointF,
    QRectF,
    Qt,
    QTimer,
)
from PySide6.QtGui import QBrush, QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QGraphicsObject,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
)


class PersonagemPixel(QGraphicsObject):
    PIXEL = 4
    LARGURA = 17 * PIXEL
    ALTURA = 25 * PIXEL

    PALETAS = (
        {
            "pele": "#f0b68f",
            "cabelo": "#392b35",
            "camisa": "#4c8f89",
            "detalhe": "#e9c85d",
            "calca": "#3e507b",
            "sapato": "#4c332d",
        },
        {
            "pele": "#d99b76",
            "cabelo": "#472b62",
            "camisa": "#ca668c",
            "detalhe": "#f3d9a1",
            "calca": "#633e72",
            "sapato": "#382c43",
        },
        {
            "pele": "#f4cba3",
            "cabelo": "#d8873e",
            "camisa": "#4187a1",
            "detalhe": "#f2df6f",
            "calca": "#466c75",
            "sapato": "#48352c",
        },
        {
            "pele": "#b8785c",
            "cabelo": "#263d54",
            "camisa": "#bd5967",
            "detalhe": "#f2c8a4",
            "calca": "#455074",
            "sapato": "#332d43",
        },
        {
            "pele": "#edc3a2",
            "cabelo": "#246b78",
            "camisa": "#d68b45",
            "detalhe": "#f4de7a",
            "calca": "#506c58",
            "sapato": "#3b3546",
        },
    )

    def __init__(
        self,
        aparencia: int,
        nome: str | None = None,
        papel: str = "fa",
    ) -> None:
        super().__init__()
        self.aparencia = aparencia % len(self.PALETAS)
        self.estilo_cabelo = aparencia % 4
        self.papel = papel
        self.pose = "parado"
        self.andando = False
        self.quadro = 0
        self.setZValue(10)

        self._rotulo: QGraphicsSimpleTextItem | None = None
        if nome is not None:
            self._rotulo = QGraphicsSimpleTextItem(nome, self)
            self._rotulo.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
            self._rotulo.setBrush(QBrush("#fff0c2"))
            largura_texto = self._rotulo.boundingRect().width()
            self._rotulo.setPos((self.LARGURA - largura_texto) / 2, 101)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.LARGURA, 124)

    def set_pose(self, pose: str) -> None:
        self.pose = pose
        self.update()

    def set_andando(self, andando: bool) -> None:
        self.andando = andando
        self.update()

    def avancar_quadro(self) -> None:
        self.quadro = 1 - self.quadro
        if self.andando or self.pose == "autografando":
            self.update()

    def _pixel(self, painter: QPainter, x: int, y: int, cor: str) -> None:
        escala = self.PIXEL
        painter.fillRect(
            QRectF(x * escala, y * escala, escala, escala), QColor(cor)
        )

    def _faixa(
        self, painter: QPainter, y: int, inicio: int, fim: int, cor: str
    ) -> None:
        for x in range(inicio, fim + 1):
            self._pixel(painter, x, y, cor)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        del option, widget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        paleta = self.PALETAS[self.aparencia]
        pele = paleta["pele"]
        cabelo = paleta["cabelo"]
        camisa = paleta["camisa"]
        detalhe = paleta["detalhe"]
        calca = paleta["calca"]

        for y, inicio, fim in (
            (0, 6, 10),
            (1, 4, 12),
            (2, 3, 13),
            (3, 3, 13),
        ):
            self._faixa(painter, y, inicio, fim, cabelo)

        if self.estilo_cabelo == 2:
            self._faixa(painter, 3, 13, 15, cabelo)
            self._faixa(painter, 4, 14, 15, cabelo)
            self._faixa(painter, 5, 14, 15, cabelo)
        elif self.estilo_cabelo == 3:
            self._faixa(painter, 1, 2, 4, cabelo)
            self._faixa(painter, 1, 12, 14, cabelo)
            self._faixa(painter, 2, 1, 3, cabelo)
            self._faixa(painter, 2, 13, 15, cabelo)

        for y in range(4, 12):
            self._faixa(painter, y, 4, 12, pele)
        self._pixel(painter, 3, 7, pele)
        self._pixel(painter, 13, 7, pele)

        if self.estilo_cabelo in (1, 3):
            for y in range(4, 15):
                self._pixel(painter, 3, y, cabelo)
                self._pixel(painter, 13, y, cabelo)
        else:
            for y in range(4, 9):
                self._pixel(painter, 3, y, cabelo)
                self._pixel(painter, 13, y, cabelo)
        if self.estilo_cabelo == 0:
            self._faixa(painter, 4, 5, 7, cabelo)
            self._faixa(painter, 5, 9, 11, cabelo)
        elif self.estilo_cabelo == 1:
            self._faixa(painter, 4, 5, 11, cabelo)
        elif self.estilo_cabelo == 2:
            self._faixa(painter, 4, 5, 9, cabelo)
            self._faixa(painter, 5, 10, 12, cabelo)
        else:
            self._faixa(painter, 4, 4, 10, cabelo)
            self._pixel(painter, 11, 5, cabelo)

        for x in (6, 10):
            self._pixel(painter, x, 6, cabelo)
            self._pixel(painter, x, 7, "#fff5df")
            self._pixel(painter, x, 8, "#24243d")
        self._pixel(painter, 8, 9, "#c77e69")
        self._pixel(painter, 7, 10, "#743d4b")
        self._pixel(painter, 8, 10, "#743d4b")
        self._pixel(painter, 9, 10, "#743d4b")
        self._pixel(painter, 5, 9, "#e99b86")
        self._pixel(painter, 11, 9, "#e99b86")
        if self.estilo_cabelo == 1:
            for x in (5, 7, 9, 11):
                self._pixel(painter, x, 7, "#382b42")
            self._pixel(painter, 8, 7, "#382b42")
        elif self.estilo_cabelo == 3:
            self._pixel(painter, 5, 9, "#8c5749")
            self._pixel(painter, 11, 9, "#8c5749")

        self._faixa(painter, 12, 7, 9, pele)
        self._faixa(painter, 13, 6, 10, camisa)
        for y in range(14, 19):
            self._faixa(painter, y, 4, 12, camisa)

        deslocamento_braco = self.quadro if self.andando else 0
        for y in range(14, 19):
            self._pixel(painter, 3, y + deslocamento_braco, pele)
            self._pixel(painter, 13, y - deslocamento_braco, pele)
        self._pixel(painter, 4, 15, detalhe)
        self._pixel(painter, 12, 15, detalhe)
        self._faixa(painter, 16, 7, 9, detalhe)

        if self.papel == "autor":
            self._faixa(painter, 19, 5, 11, calca)
            self._faixa(painter, 20, 6, 12, calca)
            self._faixa(painter, 21, 9, 13, paleta["sapato"])
            self._pixel(painter, 13, 15, pele)
            self._pixel(painter, 14, 15, pele)
            caneta_y = 16 + self.quadro
            self._pixel(painter, 15, caneta_y, "#332b42")
            self._pixel(painter, 14, caneta_y, detalhe)
            return

        if self.pose == "lendo":
            self._faixa(painter, 15, 13, 15, pele)
            self._faixa(painter, 16, 14, 15, "#584c7b")
            self._faixa(painter, 17, 14, 15, "#fff2c8")
            self._faixa(painter, 18, 14, 15, "#fff2c8")
            self._pixel(painter, 15, 17, "#ce6c78")
        else:
            perna_esquerda = -self.quadro if self.andando else 0
            perna_direita = self.quadro if self.andando else 0
            for y in (19, 20, 21):
                self._pixel(painter, 6 + perna_esquerda, y, calca)
                self._pixel(painter, 7 + perna_esquerda, y, calca)
                self._pixel(painter, 10 + perna_direita, y, calca)
                self._pixel(painter, 11 + perna_direita, y, calca)
            self._faixa(painter, 22, 5 + perna_esquerda, 7 + perna_esquerda, paleta["sapato"])
            self._faixa(painter, 22, 10 + perna_direita, 12 + perna_direita, paleta["sapato"])


class CenarioAutografos(QGraphicsScene):
    MAX_FAS_VISIVEIS = 5
    X_FRENTE = 500
    PASSO_FILA = 95
    Y_FILA = 235
    X_ASSINATURA = 590

    def __init__(self) -> None:
        super().__init__(0, 0, 1260, 480)
        self._personagens_fila: dict[int, PersonagemPixel] = {}
        self._personagens_leitores: dict[int, PersonagemPixel] = {}
        self._animacoes_movimento: dict[PersonagemPixel, QPropertyAnimation] = {}
        self._grupos_leitura: dict[int, QSequentialAnimationGroup] = {}
        self._id_assinando: int | None = None
        self._itens_assinaturas: list[QGraphicsSimpleTextItem] = []
        self._desenhar_cenario()

        self.autor = PersonagemPixel(4, papel="autor")
        self.autor.setPos(675, 164)
        self.addItem(self.autor)

        self._relogio = QTimer(self)
        self._relogio.timeout.connect(self._avancar_animacoes)
        self._relogio.start(150)

    def _retangulo(
        self, x: int, y: int, largura: int, altura: int, cor: str
    ) -> None:
        self.addRect(
            x,
            y,
            largura,
            altura,
            Qt.PenStyle.NoPen,
            QBrush(cor),
        )

    def _texto(
        self,
        texto: str,
        x: int,
        y: int,
        cor: str = "#f8e7a1",
        tamanho: int = 12,
    ) -> QGraphicsSimpleTextItem:
        item = self.addSimpleText(
            texto, QFont("Consolas", tamanho, QFont.Weight.Bold)
        )
        item.setBrush(QBrush(cor))
        item.setPos(x, y)
        return item

    def _desenhar_cenario(self) -> None:
        self._retangulo(0, 0, 1260, 480, "#282447")
        for x in range(0, 1260, 40):
            self._retangulo(x, 82, 20, 7, "#37345c")
            self._retangulo(x + 18, 184, 22, 7, "#37345c")

        self._retangulo(0, 365, 1260, 115, "#583e50")
        for x in range(0, 1260, 48):
            self._retangulo(x, 365, 2, 115, "#76505a")
        self._retangulo(0, 365, 1260, 4, "#e6a858")

        for x in range(80, 1190, 48):
            self._retangulo(x, 40, 8, 8, "#f8d875")
            self._retangulo(x + 8, 48, 8, 8, "#e98668")
        self._texto("LIVRARIA PIXEL - EVENTO DE LANCAMENTO", 405, 58, "#c7c5e8", 15)

        self._texto("FILA DE FAS", 106, 175, "#a8d7e8", 12)
        self._retangulo(90, 351, 455, 3, "#edbf61")
        for x in (180, 280, 380, 480):
            self._retangulo(x, 347, 5, 10, "#edbf61")
            self._retangulo(x + 5, 352, 5, 5, "#edbf61")
        self._item_fila = self._texto("FILA: 0", 105, 192, "#fff0c2", 10)
        self._item_estado_fa = self._texto(
            "FÃ DA VEZ: AGUARDANDO AUTÓGRAFO",
            105,
            211,
            "#f5c66a",
            13,
        )

        self._texto("AUTOR", 695, 100, "#a8d7e8", 12)
        self._retangulo(687, 205, 62, 84, "#76505a")
        self._retangulo(677, 201, 82, 10, "#e6a858")
        self._retangulo(695, 230, 10, 37, "#c78150")
        self._retangulo(737, 230, 10, 37, "#c78150")
        self._retangulo(633, 285, 193, 16, "#d18a4d")
        self._retangulo(646, 301, 14, 54, "#9a5d40")
        self._retangulo(797, 301, 14, 54, "#9a5d40")
        self._retangulo(614, 273, 52, 9, "#fff5d6")
        self._texto("LIVRO DE AUTOGRAFOS", 605, 319, "#fff0c2", 9)
        self._item_estado_escritor = self._texto(
            "ESCRITOR: LIVRE", 663, 371, "#9fe0a2", 12
        )

        self._retangulo(890, 93, 330, 268, "#17172c")
        self._retangulo(898, 101, 314, 252, "#e4c78c")
        self._retangulo(905, 108, 300, 29, "#65466b")
        self._texto("LISTA DE AUTOGRAFOS", 925, 114, "#fff0b0", 12)
        self._texto("CONSULTA COMPARTILHADA", 919, 143, "#59485e", 9)
        self._item_estado_leitor = self._texto(
            "LEITOR: LIVRE", 918, 293, "#385d68", 12
        )
        self._retangulo(912, 308, 284, 2, "#b69a69")
        self._item_total = self._texto("TOTAL: 0", 918, 315, "#385d68", 12)
        self._item_leitores = self._texto(
            "LEITORES ATIVOS: 0", 918, 335, "#385d68", 12
        )
        self._item_anteriores: QGraphicsSimpleTextItem | None = None

    def _avancar_animacoes(self) -> None:
        self.autor.avancar_quadro()
        for personagem in (
            *self._personagens_fila.values(),
            *self._personagens_leitores.values(),
        ):
            personagem.avancar_quadro()

    def atualizar_contagem_fila(self, quantidade: int) -> None:
        fora_da_cena = max(0, quantidade - self.MAX_FAS_VISIVEIS)
        texto = f"FILA: {quantidade}"
        if fora_da_cena:
            texto += f"  (+{fora_da_cena} aguardando)"
        self._item_fila.setText(texto)

    def atualizar_leitores(self, quantidade: int) -> None:
        self._item_leitores.setText(f"LEITORES ATIVOS: {quantidade}")

    def atualizar_estado_fa(self, texto: str, cor: str) -> None:
        self._item_estado_fa.setText(texto)
        self._item_estado_fa.setBrush(QBrush(cor))

    def atualizar_estado_leitor(self, texto: str, cor: str) -> None:
        self._item_estado_leitor.setText(texto)
        self._item_estado_leitor.setBrush(QBrush(cor))

    def atualizar_lista(self, autografos: tuple[str, ...]) -> None:
        for item in self._itens_assinaturas:
            self.removeItem(item)
        self._itens_assinaturas.clear()
        if self._item_anteriores is not None:
            self.removeItem(self._item_anteriores)
            self._item_anteriores = None

        anteriores = max(0, len(autografos) - 6)
        if anteriores:
            self._item_anteriores = self._texto(
                f"... {anteriores} autografos anteriores",
                921,
                163,
                "#68586a",
                9,
            )
        recentes = autografos[-6:]
        for indice, nome in enumerate(recentes):
            item = self._texto(
                f"OK  {nome}",
                921,
                164 + (indice + bool(anteriores)) * 19,
                "#256044",
                10,
            )
            self._itens_assinaturas.append(item)
        self._item_total.setText(f"TOTAL: {len(autografos)}")

    def sincronizar_fila(
        self,
        fila: list,
        animar: bool = False,
        atendido_id: int | None = None,
    ) -> None:
        visiveis = fila[: self.MAX_FAS_VISIVEIS]
        ids_visiveis = {fa.id for fa in visiveis}

        for fa_id in tuple(self._personagens_fila):
            if fa_id in ids_visiveis or fa_id == self._id_assinando:
                continue
            personagem = self._personagens_fila.pop(fa_id)
            if fa_id == atendido_id and animar:
                personagem.set_pose("andando")
                self._mover(
                    personagem,
                    835,
                    self.Y_FILA,
                    520,
                    lambda personagem=personagem: self._remover_personagem(
                        personagem
                    ),
                )
            else:
                self.removeItem(personagem)

        for indice, fa in enumerate(visiveis):
            personagem = self._personagens_fila.get(fa.id)
            destino_x = self.X_FRENTE - indice * self.PASSO_FILA
            if personagem is None:
                personagem = PersonagemPixel(fa.aparencia, fa.nome)
                self._personagens_fila[fa.id] = personagem
                self.addItem(personagem)
                if animar:
                    personagem.setPos(62, self.Y_FILA)
                    personagem.set_pose("andando")
                    self._mover(
                        personagem,
                        destino_x,
                        self.Y_FILA,
                        650,
                    )
                else:
                    personagem.setPos(destino_x, self.Y_FILA)
            elif fa.id != self._id_assinando:
                if animar and abs(personagem.pos().x() - destino_x) > 1:
                    personagem.set_pose("andando")
                    self._mover(
                        personagem,
                        destino_x,
                        self.Y_FILA,
                        620,
                    )
                else:
                    personagem.setPos(destino_x, self.Y_FILA)

        self.atualizar_contagem_fila(len(fila))

    def iniciar_autografo(self, fa_id: int, nome: str) -> None:
        personagem = self._personagens_fila.get(fa_id)
        if personagem is None:
            raise RuntimeError("O proximo fa nao esta visivel na fila.")

        self._id_assinando = fa_id
        personagem.set_pose("andando")
        self.autor.set_pose("autografando")
        self.atualizar_estado_fa(
            f"{nome.upper()}: SENDO AUTOGRAFADO", "#f17b61"
        )
        self.atualizar_escritor("AUTOGRAFANDO", "#f17b61")
        self._mover(
            personagem,
            self.X_ASSINATURA,
            self.Y_FILA,
            520,
            lambda personagem=personagem: personagem.set_pose("recebendo"),
        )

    def finalizar_autografo(
        self,
        fa_id: int,
        fila: list,
        autografos: tuple[str, ...],
    ) -> None:
        self.autor.set_pose("parado")
        self.atualizar_escritor("LIVRE", "#9fe0a2")
        self.atualizar_lista(autografos)
        self._id_assinando = None
        self.sincronizar_fila(fila, animar=True, atendido_id=fa_id)

    def iniciar_consulta(self, leitor_id: int, duracao_segundos: int) -> None:
        personagem = PersonagemPixel(leitor_id + 2, papel="leitor")
        personagem.setPos(1070, 238 + (leitor_id % 2) * 18)
        personagem.set_pose("andando")
        self._personagens_leitores[leitor_id] = personagem
        self.addItem(personagem)

        tempo_deslocamento = 500
        tempo_total = max(2000, duracao_segundos * 1000)
        chegada = QPropertyAnimation(personagem, b"pos")
        chegada.setDuration(tempo_deslocamento)
        chegada.setStartValue(personagem.pos())
        chegada.setEndValue(QPointF(817, personagem.pos().y()))
        pausa = QPauseAnimation(tempo_total - 2 * tempo_deslocamento)
        saida = QPropertyAnimation(personagem, b"pos")
        saida.setDuration(tempo_deslocamento)
        saida.setStartValue(QPointF(817, personagem.pos().y()))
        saida.setEndValue(QPointF(1070, personagem.pos().y()))

        grupo = QSequentialAnimationGroup(self)
        grupo.addAnimation(chegada)
        grupo.addAnimation(pausa)
        grupo.addAnimation(saida)
        grupo.currentAnimationChanged.connect(
            lambda atual, personagem=personagem, pausa=pausa: self._mudar_pose_leitor(
                personagem, atual, pausa
            )
        )
        grupo.finished.connect(
            lambda leitor_id=leitor_id, personagem=personagem: self._fim_consulta_visual(
                leitor_id, personagem
            )
        )
        self._grupos_leitura[leitor_id] = grupo
        grupo.start()

    @staticmethod
    def _mudar_pose_leitor(
        personagem: PersonagemPixel,
        animacao_atual,
        pausa: QPauseAnimation,
    ) -> None:
        lendo = animacao_atual is pausa
        personagem.set_pose("lendo" if lendo else "andando")
        personagem.set_andando(not lendo)

    def _fim_consulta_visual(
        self, leitor_id: int, personagem: PersonagemPixel
    ) -> None:
        self._personagens_leitores.pop(leitor_id, None)
        self.removeItem(personagem)
        grupo = self._grupos_leitura.pop(leitor_id, None)
        if grupo is not None:
            grupo.deleteLater()

    def atualizar_escritor(self, estado: str, cor: str) -> None:
        self._item_estado_escritor.setText(f"ESCRITOR: {estado}")
        self._item_estado_escritor.setBrush(QBrush(cor))

    def _mover(
        self,
        personagem: PersonagemPixel,
        x: float,
        y: float,
        duracao: int,
        ao_terminar=None,
    ) -> None:
        animacao_anterior = self._animacoes_movimento.pop(personagem, None)
        if animacao_anterior is not None:
            animacao_anterior.stop()
            animacao_anterior.deleteLater()

        animacao = QPropertyAnimation(personagem, b"pos", self)
        animacao.setDuration(duracao)
        animacao.setStartValue(personagem.pos())
        animacao.setEndValue(QPointF(x, y))
        animacao.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animacoes_movimento[personagem] = animacao

        def concluir() -> None:
            if self._animacoes_movimento.get(personagem) is animacao:
                self._animacoes_movimento.pop(personagem, None)
            personagem.set_andando(False)
            animacao.deleteLater()
            if ao_terminar is not None:
                ao_terminar()

        personagem.set_andando(True)
        animacao.finished.connect(concluir)
        animacao.start()

    def _remover_personagem(self, personagem: PersonagemPixel) -> None:
        animacao = self._animacoes_movimento.pop(personagem, None)
        if animacao is not None:
            animacao.deleteLater()
        self.removeItem(personagem)


class PixelView(QGraphicsView):
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.scene() is not None:
            self.fitInView(
                self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
            )
