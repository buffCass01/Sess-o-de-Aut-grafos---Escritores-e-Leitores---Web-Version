import math
import random
import wave
from array import array
from pathlib import Path

from PySide6.QtCore import QObject, QTemporaryDir, QUrl, Signal
from PySide6.QtMultimedia import (
    QAudioOutput,
    QMediaDevices,
    QMediaPlayer,
    QSoundEffect,
)


_TAXA_AMOSTRAGEM = 22050


def _salvar_wav(caminho: Path, amostras: list[int]) -> None:
    dados = array("h", amostras)
    with wave.open(str(caminho), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(_TAXA_AMOSTRAGEM)
        arquivo.writeframes(dados.tobytes())


def _sintetizar_tons(notas: tuple[tuple[float, float], ...]) -> list[int]:
    amostras: list[int] = []
    for frequencia, duracao in notas:
        quantidade = int(_TAXA_AMOSTRAGEM * duracao)
        for indice in range(quantidade):
            borda = min(
                1.0,
                indice / (_TAXA_AMOSTRAGEM * 0.012),
                (quantidade - indice - 1) / (_TAXA_AMOSTRAGEM * 0.025),
            )
            fase = 2 * math.pi * frequencia * indice / _TAXA_AMOSTRAGEM
            amostras.append(int(11000 * borda * math.sin(fase)))
        amostras.extend([0] * int(_TAXA_AMOSTRAGEM * 0.025))
    return amostras


def _sintetizar_musica() -> list[int]:
    melodia = (
        523.25, 659.25, 783.99, 659.25, 440.00, 523.25, 659.25, 783.99,
        349.23, 440.00, 523.25, 659.25, 392.00, 493.88, 587.33, 783.99,
        523.25, 659.25, 783.99, 659.25, 440.00, 523.25, 659.25, 783.99,
        349.23, 440.00, 523.25, 659.25, 392.00, 493.88, 587.33, 523.25,
    )
    baixos = (130.81, 110.00, 87.31, 98.00)
    quantidade_nota = int(_TAXA_AMOSTRAGEM * 0.18)
    amostras: list[int] = []

    for indice_nota, frequencia in enumerate(melodia):
        baixo = baixos[indice_nota // 8]
        for indice in range(quantidade_nota):
            borda = min(
                1.0,
                indice / (_TAXA_AMOSTRAGEM * 0.012),
                (quantidade_nota - indice - 1) / (_TAXA_AMOSTRAGEM * 0.025),
            )
            tempo = indice / _TAXA_AMOSTRAGEM
            tom = math.sin(2 * math.pi * frequencia * tempo)
            tom += 0.16 * math.sin(4 * math.pi * frequencia * tempo)
            tom += 0.42 * math.sin(2 * math.pi * baixo * tempo)
            amostras.append(int(9000 * borda * tom))

    return amostras


def _sintetizar_escrita() -> list[int]:
    gerador = random.Random(23)
    amostras: list[int] = []
    duracao_risco = int(_TAXA_AMOSTRAGEM * 0.11)

    for risco in range(6):
        for indice in range(duracao_risco):
            borda = min(
                1.0,
                indice / (_TAXA_AMOSTRAGEM * 0.01),
                (duracao_risco - indice - 1) / (_TAXA_AMOSTRAGEM * 0.02),
            )
            tempo = indice / _TAXA_AMOSTRAGEM
            ruido = gerador.uniform(-1.0, 1.0)
            tom = math.sin(2 * math.pi * (390 + risco * 28) * tempo)
            amostras.append(int(4300 * borda * (0.55 * ruido + 0.45 * tom)))
        amostras.extend([0] * int(_TAXA_AMOSTRAGEM * 0.07))

    return amostras


class AudioEvento(QObject):
    erro = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.aviso: str | None = None
        self._erro_reportado = False
        self._musica_ativa = False
        self._disponivel = not QMediaDevices.defaultAudioOutput().isNull()
        self._diretorio = QTemporaryDir()
        self._sons: dict[str, QSoundEffect] = {}
        self._player: QMediaPlayer | None = None
        self._saida: QAudioOutput | None = None

        if not self._disponivel:
            self.aviso = "Áudio indisponível: nenhum dispositivo de saída foi encontrado."
            return
        if not self._diretorio.isValid():
            raise RuntimeError("Não foi possível criar os arquivos temporários de áudio.")

        pasta = Path(self._diretorio.path())
        caminhos = {
            "musica": pasta / "musica_evento.wav",
            "clique": pasta / "clique.wav",
            "chegada": pasta / "chegada.wav",
            "passos": pasta / "passos.wav",
            "consulta": pasta / "consulta.wav",
            "escrita": pasta / "escrita.wav",
        }
        _salvar_wav(caminhos["musica"], _sintetizar_musica())
        _salvar_wav(
            caminhos["clique"],
            _sintetizar_tons(((880.0, 0.045), (660.0, 0.04))),
        )
        _salvar_wav(
            caminhos["chegada"],
            _sintetizar_tons(((587.33, 0.08), (783.99, 0.12))),
        )
        _salvar_wav(
            caminhos["passos"],
            _sintetizar_tons(
                ((392.0, 0.055), (0.0, 0.035), (330.0, 0.055), (0.0, 0.035), (440.0, 0.07))
            ),
        )
        _salvar_wav(
            caminhos["consulta"],
            _sintetizar_tons(((659.25, 0.07), (783.99, 0.12))),
        )
        _salvar_wav(caminhos["escrita"], _sintetizar_escrita())

        volumes = {
            "clique": 0.28,
            "chegada": 0.38,
            "passos": 0.3,
            "consulta": 0.28,
            "escrita": 0.2,
        }
        for nome, volume in volumes.items():
            efeito = QSoundEffect(self)
            efeito.setSource(QUrl.fromLocalFile(str(caminhos[nome])))
            efeito.setVolume(volume)
            efeito.statusChanged.connect(
                lambda efeito=efeito: self._verificar_erro_efeito(efeito)
            )
            self._sons[nome] = efeito

        self._sons["escrita"].setLoopCount(QSoundEffect.Infinite.value)
        self._saida = QAudioOutput(self)
        self._saida.setVolume(0.2)
        self._player = QMediaPlayer(self)
        self._player.setAudioOutput(self._saida)
        self._player.setSource(QUrl.fromLocalFile(str(caminhos["musica"])))
        self._player.setLoops(QMediaPlayer.Loops.Infinite)
        self._player.errorOccurred.connect(self._verificar_erro_player)

    @property
    def disponivel(self) -> bool:
        return self._disponivel

    @property
    def musica_ativa(self) -> bool:
        return self._musica_ativa

    def definir_musica(self, ativa: bool) -> bool:
        if not self._disponivel or self._player is None:
            return False
        if ativa:
            self._player.play()
        else:
            self._player.pause()
        self._musica_ativa = ativa
        return self._musica_ativa

    def tocar(self, nome: str) -> None:
        efeito = self._sons.get(nome)
        if self._disponivel and efeito is not None:
            efeito.play()

    def iniciar_escrita(self) -> None:
        if self._disponivel:
            self._sons["escrita"].play()

    def parar_escrita(self) -> None:
        if self._disponivel:
            self._sons["escrita"].stop()

    def encerrar(self) -> None:
        self.definir_musica(False)
        for efeito in self._sons.values():
            efeito.stop()

    def _verificar_erro_efeito(self, efeito: QSoundEffect) -> None:
        if efeito.status() == QSoundEffect.Status.Error:
            self._reportar_erro("Um efeito sonoro não pôde ser carregado.")

    def _verificar_erro_player(self, erro: QMediaPlayer.Error, detalhe: str) -> None:
        if erro != QMediaPlayer.Error.NoError:
            self._reportar_erro(f"A música não pôde ser reproduzida: {detalhe}")

    def _reportar_erro(self, mensagem: str) -> None:
        if not self._erro_reportado:
            self._erro_reportado = True
            self.erro.emit(mensagem)
