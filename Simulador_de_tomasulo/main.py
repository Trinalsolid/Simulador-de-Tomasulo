from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
import subprocess
import sys

def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Simulador do Algoritmo de Tomasulo")
    app.setOrganizationName("AC3 - Trabalho2")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()