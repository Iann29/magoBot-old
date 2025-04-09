import os
import subprocess

class OpenAgent:
    def __init__(self):
        self.apps = {
            "CELEIRO": {
                "package": "ru.xomka.hdagenw",
                "activity": "ru.xomka.hdagenw.profile.MainActivity"
            },
            "DINAMITE": {
                "package": "ru.xomka.hdagens",
                "activity": "ru.xomka.hdagens.profile.MainActivity"
            },
            "ITENS": {
                "package": "ru.xomka.hdageno",
                "activity": "ru.xomka.hdageno.profile.MainActivity"
            },
            "MACHADO": {
                "package": "ru.xomka.hdageny",
                "activity": "ru.xomka.hdageny.profile.MainActivity"
            },
            "MOEDAS": {
                "package": "ru.xomka.hdagenp",
                "activity": "ru.xomka.hdagenp.profile.MainActivity"
            },
            "PA": {
                "package": "ru.xomka.hdagenz",
                "activity": "ru.xomka.hdagenz.profile.MainActivity"
            },
            "SERRA ": {
                "package": "ru.xomka.hdagenx",
                "activity": "ru.xomka.hdagenx.profile.MainActivity"
            },
            "SILO": {
                "package": "ru.xomka.hdagenv",
                "activity": "ru.xomka.hdagenv.profile.MainActivity"
            },
            "TERRA 🏕": {
                "package": "ru.xomka.hdagenu",
                "activity": "ru.xomka.hdagenu.profile.MainActivity"
            },
            "VAZIAS": {
                "package": "ru.xomka.hdagena",
                "activity": "ru.xomka.hdagena.profile.MainActivity"
            }
        }

    def get_app_list(self):
        """Retorna a lista de nomes dos aplicativos disponíveis"""
        return list(self.apps.keys())

    def open_app(self, app_name):
        """Abre o aplicativo especificado usando ADB"""
        if app_name not in self.apps:
            raise ValueError(f"Aplicativo '{app_name}' não encontrado")

        app_info = self.apps[app_name]
        package = app_info["package"]
        activity = app_info["activity"]

        try:
            # Comando ADB para abrir o aplicativo
            command = f'adb shell am start -n {package}/{activity}'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                return True, "Aplicativo aberto com sucesso"
            else:
                return False, f"Erro ao abrir aplicativo: {result.stderr}"

        except Exception as e:
            return False, f"Erro ao executar comando ADB: {str(e)}"
