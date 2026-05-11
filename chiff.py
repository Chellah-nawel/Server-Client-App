import subprocess

dossier = "certs"

# genere une cle aes et la chiffre avec la cle pub du destinataire
# appele une seule fois au debut de la session
def init_session(cle_pub_dest):

    cle_session = f"{dossier}/cle.session"
    cle_session_enc = f"{dossier}/cle_session.enc"

    # cree la cle aes 256 bit
    subprocess.run(["openssl", "rand", "-out", cle_session, "32"],
        check=True, capture_output=True)

    # chiffre la cle aes avec rsa (cle pub du serveur)
    subprocess.run(["openssl", "pkeyutl", "-encrypt", "-pubin",
        "-inkey", cle_pub_dest, "-in", cle_session, "-out", cle_session_enc],
        check=True, capture_output=True)

    return cle_session, cle_session_enc


# chiffre un fichier avec la cle de session deja existante
def chiff_fichier(fichier_path, cle_session):

    out = "fichier_chiff.enc"

    subprocess.run(["openssl", "enc", "-aes-256-cbc",
        "-in", fichier_path, "-out", out,
        "-pass", f"file:{cle_session}"],
        check=True, capture_output=True)

    return out


# dechiffre la cle de session avec la cle priv du serveur
# appele une seule fois quand le client se connecte
def dechiff_cle_session(cle_session_enc, cle_priv):

    out = f"{dossier}/cle_dechiff.session"

    subprocess.run(["openssl", "pkeyutl", "-decrypt",
        "-inkey", cle_priv, "-in", cle_session_enc, "-out", out],
        check=True, capture_output=True)

    return out


# dechiffre un fichier avec la cle de session (deja dechiffree)
def dechiff_fichier(fichier_enc, cle_session):

    out = "fichier_dechiff.txt"

    subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc",
        "-in", fichier_enc, "-out", out,
        "-pass", f"file:{cle_session}"],
        check=True, capture_output=True)

    return out
