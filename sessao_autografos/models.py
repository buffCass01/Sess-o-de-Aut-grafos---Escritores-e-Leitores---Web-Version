from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Condition
from time import sleep

from PySide6.QtCore import QThread, Signal


@dataclass(frozen=True)
class Fa:
    id: int
    nome: str
    aparencia: int


class TravaLeitoresEscritores:
    """Permite leituras simultaneas e escrita exclusiva, priorizando escritores."""

    def __init__(self) -> None:
        self._condicao = Condition()
        self._leitores_ativos = 0
        self._escritor_ativo = False
        self._escritores_esperando = 0

    @contextmanager
    def leitura(self):
        with self._condicao:
            while self._escritor_ativo or self._escritores_esperando > 0:
                self._condicao.wait()
            self._leitores_ativos += 1

        try:
            yield
        finally:
            with self._condicao:
                self._leitores_ativos -= 1
                if self._leitores_ativos == 0:
                    self._condicao.notify_all()

    @contextmanager
    def escrita(self):
        with self._condicao:
            self._escritores_esperando += 1
            try:
                while self._escritor_ativo or self._leitores_ativos > 0:
                    self._condicao.wait()
                self._escritor_ativo = True
            finally:
                self._escritores_esperando -= 1

        try:
            yield
        finally:
            with self._condicao:
                self._escritor_ativo = False
                self._condicao.notify_all()


class LeitorWorker(QThread):
    entrou = Signal(int, int)
    mensagem = Signal(str)
    consulta_concluida = Signal(int, object)

    def __init__(
        self,
        numero: int,
        trava: TravaLeitoresEscritores,
        autografos: list[str],
        duracao_segundos: int,
    ) -> None:
        super().__init__()
        self.numero = numero
        self.trava = trava
        self.autografos = autografos
        self.duracao_segundos = duracao_segundos

    def run(self) -> None:
        self.mensagem.emit(f"Leitor {self.numero} pediu para consultar a lista.")

        with self.trava.leitura():
            self.entrou.emit(self.numero, self.duracao_segundos)
            self.mensagem.emit(f"Leitor {self.numero} esta lendo a lista.")
            sleep(self.duracao_segundos)
            resultado = tuple(self.autografos)

        self.consulta_concluida.emit(self.numero, resultado)


class AutorWorker(QThread):
    comecou_a_assinar = Signal(int, str)
    mensagem = Signal(str)
    autografo_concluido = Signal(int, str, object)

    def __init__(
        self,
        fa: Fa,
        trava: TravaLeitoresEscritores,
        autografos: list[str],
        duracao_segundos: int,
    ) -> None:
        super().__init__()
        self.fa = fa
        self.trava = trava
        self.autografos = autografos
        self.duracao_segundos = duracao_segundos

    def run(self) -> None:
        self.mensagem.emit(
            f"O autor aguarda acesso exclusivo para atender {self.fa.nome}."
        )

        with self.trava.escrita():
            self.comecou_a_assinar.emit(self.fa.id, self.fa.nome)
            self.mensagem.emit(f"O autor esta autografando para {self.fa.nome}.")
            sleep(self.duracao_segundos)
            self.autografos.append(self.fa.nome)
            resultado = tuple(self.autografos)

        self.autografo_concluido.emit(self.fa.id, self.fa.nome, resultado)
