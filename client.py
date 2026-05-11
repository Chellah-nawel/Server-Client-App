import socket
import json
import os
import subprocess
import threading

from protocole import send_msg, recv_msg
from secu import verifier_certificat
from chiff import chiff_fichier


IP_SERVEUR = "127.0.0.1"
PORT_SERVEUR = 12345

#cree la socket pour client
def creer_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((IP_SERVEUR, PORT_SERVEUR))
    print(f"[CLIENT] connecte au serveur {IP_SERVEUR}:{PORT_SERVEUR}")
    return sock

#envoyer le certificat 
def env_cert(sock, cert_path):
    with open(cert_path, "rb") as f:
        cert = f.read()
    send_msg(sock, cert)
    print(f"[CLIENT] certificat envoye ({len(cert)} bytes)")


def rec_verif_cert(sock):
    cert_bytes = recv_msg(sock)
    if cert_bytes is None:
        raise Exception("cert serveur non recu")

    os.makedirs("certs", exist_ok=True)
    cert_path = "certs/cert_serv_recu.crt"
    with open(cert_path, "wb") as f:
        f.write(cert_bytes)

    # verification dans un thread pour eviter le freeze sur windows
    res = [None]
    err = [None]

    def _check():
        try:
            res[0] = verifier_certificat(cert_path)
        except Exception as e:
            err[0] = str(e)

    t = threading.Thread(target=_check, daemon=True)
    t.start()
    t.join(timeout=20)

    if t.is_alive():
        print("[CLIENT] timeout verif, on continue quand meme")
        return cert_path

    if err[0]:
        raise Exception(f"erreur verif: {err[0]}")

    if not res[0]:
        raise Exception("[CLIENT] cert serveur invalide, on coupe")

    print("[CLIENT] cert serveur OK")
    return cert_path

#recuperer cle publique
def extraire_cle_pub(cert_path):
    pub_path = "certs/serv_pub_extraite.pub"
    subprocess.run(
        ["openssl", "x509", "-in", cert_path, "-pubkey", "-noout", "-out", pub_path],
        check=True, capture_output=True, stdin=subprocess.DEVNULL
    )
    return pub_path


# envoie la cle de session chiffree au debut de la connexion
def envoyer_cle_session(sock, cle_session_enc):
    with open(cle_session_enc, "rb") as f:
        send_msg(sock, f.read())
    print("[CLIENT] cle de session envoyee")


# envoie juste le fichier chiffre, la cle est deja chez le serveur
def envoyer_fichier(sock, chemin_fichier, cle_session):

    fichier_enc = chiff_fichier(chemin_fichier, cle_session)

    # nom du fichier
    nom = os.path.basename(chemin_fichier).encode()
    send_msg(sock, nom)

    # contenu chiffre
    with open(fichier_enc, "rb") as f:
        send_msg(sock, f.read())

    print(f"[CLIENT] fichier '{chemin_fichier}' envoye")


def recevoir_reponse(sock):
    data = recv_msg(sock)
    if data is None:
        return None
    return json.loads(data.decode("utf-8"))
