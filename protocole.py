import struct
import os


def recv_exactement(sock, n: int) -> bytes:
    # lire exactement n bytes depuis le socket
    #tourne jusqu'a avoir tout recu
    data = b''
    while len(data) < n:
        morceau = sock.recv(n - len(data))  # lire ce qui manque
        if not morceau:
            return None  # connexion fermée par l'autre côté
        data += morceau  # accumuler les morceaux
    return data


def send_msg(sock, data: bytes):
   #les 4 bytes indiquant la taille
    #Puis les donnes completes
    # sendall() garantit que tout est envoye, sans interruption
    taille = len(data)
    sock.sendall(taille.to_bytes(4, byteorder='big')) # codnvertir un int pour l'envoyer en reseau
    sock.sendall(data)                        # envoie tout d'un coup


def recv_msg(sock) -> bytes:
    #ire exactement 4 bytes pour connaitre la taille
    taille_raw = recv_exactement(sock, 4)
    if taille_raw is None:
        return None  # connexion coupe

    taille = int.from_bytes(taille_raw, byteorder='big') # convertir en entier Python

    # lire exactement 'taille' bytes
    return recv_exactement(sock, taille)


def send_fichier_brut(sock, chemin_fichier: str):
    # envoyer le nom du fichier ensuite le contenu
    nom = os.path.basename(chemin_fichier).encode() 
    send_msg(sock, nom)                               # envoyer le nom

    with open(chemin_fichier, "rb") as f:
        contenu = f.read()
    send_msg(sock, contenu)                           # envoyer le contenu

    print(f"[ENVOI] Fichier '{chemin_fichier}' envoyé ({len(contenu)} bytes)")


def recv_fichier_brut(sock, dossier_destination: str = "recu/") -> str:

    #lire le nom du fichier, le contenu et le sauvegarde dans dossier_destination
    #retourne le chemin du fichier sauvegarde

    os.makedirs(dossier_destination, exist_ok=True)  # créer le dossier si besoin

    #nom
    nom_raw = recv_msg(sock)
    if nom_raw is None:
        return None
    nom = nom_raw.decode()

    #contenu
    contenu = recv_msg(sock)
    if contenu is None:
        return None

    #sauvgarder
    chemin = os.path.join(dossier_destination, nom)
    with open(chemin, "wb") as f:
        f.write(contenu)

    print(f"[RECEPTION] Fichier '{nom}' sauvegardé ({len(contenu)} bytes)")
    return chemin
