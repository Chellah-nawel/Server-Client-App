import socket
import json
import threading
import os

from protocole import send_msg, recv_msg
from secu import verifier_certificat, generer_serv_certificat, generer_ca
from chiff import dechiff_cle_session, dechiff_fichier


def gerer_client(connexion, adresse, cert_serv_path, cle_priv_serv):

    print(f"[+] nouveau client: {adresse}")

    try:
        # envoyer notre cert au client
        with open(cert_serv_path, "rb") as f:
            send_msg(connexion, f.read())

        # recevoir cert client
        cert_bytes = recv_msg(connexion)
        if cert_bytes is None:
            print(f"[-] {adresse}: cert client non recu")
            return

        os.makedirs("recu", exist_ok=True)
        cert_path = f"recu/cert_{adresse[0]}_{adresse[1]}.crt"
        with open(cert_path, "wb") as f:
            f.write(cert_bytes)

        if not verifier_certificat(cert_path):
            print(f"[-] {adresse}: cert invalide, on coupe")
            connexion.close()
            return

        print(f"[+] {adresse}: cert OK")

        # recevoir la cle de session chiffree
        cle_enc_bytes = recv_msg(connexion)
        if cle_enc_bytes is None:
            print(f"[-] {adresse}: cle session non recue")
            return

        # sauvegarder et dechiffrer la cle de session
        # on garde le chemin en memoire pour toute la session
        cle_enc_path = f"recu/cle_session_{adresse[0]}_{adresse[1]}.enc"
        with open(cle_enc_path, "wb") as f:
            f.write(cle_enc_bytes)

        cle_session = dechiff_cle_session(cle_enc_path, cle_priv_serv)
        print(f"[+] {adresse}: cle de session dechiffree, session prete")

        # dossier pour les fichiers de ce client
        dossier_client = f"recu/{adresse[0]}_{adresse[1]}/"
        os.makedirs(dossier_client, exist_ok=True)

        # boucle reception fichiers - meme cle pour tous les fichiers
        while True:
            nom_raw = recv_msg(connexion)
            if nom_raw is None:
                print(f"[-] {adresse}: client deconnecte")
                break

            nom_fichier = nom_raw.decode()

            fichier_enc_bytes = recv_msg(connexion)
            if fichier_enc_bytes is None:
                break

            print(f"[{adresse}] fichier '{nom_fichier}' recu, dechiffrement...")

            # ecrire le fichier chiffre sur disque pour openssl
            tmp_enc = f"recu/tmp_{adresse[1]}.enc"
            with open(tmp_enc, "wb") as f:
                f.write(fichier_enc_bytes)

            # dechiffrer avec la cle de session de ce client
            fichier_dec = dechiff_fichier(tmp_enc, cle_session)

            # deplacer vers le bon dossier
            fichier_final = f"{dossier_client}{nom_fichier}"
            if os.path.exists(fichier_dec):
                os.replace(fichier_dec, fichier_final)

            # nettoyer le tmp
            if os.path.exists(tmp_enc):
                os.remove(tmp_enc)

            print(f"[{adresse}] fichier dechiffre -> {fichier_final}")

            # reponse json au client
            rep = json.dumps({
                "status": "ok",
                "fichier_recu": nom_fichier,
                "taille": os.path.getsize(fichier_final) if os.path.exists(fichier_final) else 0
            }).encode()
            send_msg(connexion, rep)

    except Exception as e:
        print(f"[ERREUR] {adresse}: {e}")

    finally:
        connexion.close()
        print(f"[-] connexion fermee: {adresse}")


def demarrer_serveur():

    generer_ca()
    cle_priv_serv, cert_serv = generer_serv_certificat()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', 12345))
    srv.listen(5)

    print("=" * 45)
    print("  serveur demarre sur port 12345")
    print("=" * 45)

    while True:
        conn, addr = srv.accept()
        t = threading.Thread(target=gerer_client, args=(conn, addr, cert_serv, cle_priv_serv))
        t.daemon = True
        t.start()
        print(f"[THREAD] thread pour {addr} | actifs: {threading.active_count() - 1}")
