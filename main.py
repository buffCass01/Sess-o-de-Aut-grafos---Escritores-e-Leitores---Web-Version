import sys

from PySide6.QtWidgets import QApplication

from janela import JanelaAutografos


def main() -> None:
    aplicativo = QApplication(sys.argv)
    janela = JanelaAutografos()
    janela.show()
    sys.exit(aplicativo.exec())


if __name__ == "__main__":
    main()
