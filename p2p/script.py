import subprocess

def abrir_terminais(comandos):
    """
    Abre múltiplos terminais e executa comandos diferentes em cada um.
    """
    for comando in comandos:
        subprocess.Popen(["gnome-terminal", "--"] + comando)    

comandos = [
    ["python", "peer.py", "localhost", "33333", "22222"],
    ["python", "peer.py", "localhost", "22222", "33333", '11111', '44444'],
    ["python", "peer.py", "localhost", "11111", "22222"],
    ['python', "peer.py", "localhost", "44444", "22222", "55555", "66666"],
    ["python", "peer.py", "localhost", "55555", "44444"],
    ["python", "peer.py", "localhost", "66666", "44444"]

]

abrir_terminais(comandos)
