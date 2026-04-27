
import socket
import json
#-------------- La connexion avec  socket----------------------


IP_SERVEUR = "127.0.0.1"   # L'IP de la machine du serveur 
PORT_SERVEUR =12345          # num port utilise par le serveur

def creer_client():
    """
    Crée UN socket et le connecte au serveur.
    L'OS attribue automatiquement un port au client (tu ne choisis pas).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#AF_INET pour IPv4, SOCK_STREAM pour TCP car on veut une connexion fiable et donc ipv4 va permettre d'avoir une adresse IP et TCP va permettre d'avoir une connexion fiable
    sock.connect((IP_SERVEUR, PORT_SERVEUR))#connect with the server
    return sock#il return exactement contient une connexion TCP active + les infos de connexion + les fonctions pour communiquer.

#----------------fonctions envoyer et recevoir afin d'echanger les messages et les certificats ---------------
#-----envoyer:
def envoyer(sock, titre_msg, **donnees):#sock=la connexion,titre_msg afin d'indequer  t'envoie quoi ,et **donnees permet d’envoyer permet de passer un nombre li nhebo de parametres nommes qui sont regroupes automatiquement dans un dictionnaire.
    msg = {"type": titre_msg, **donnees}#afin de construire un dectionnaire pour qu'il soit bien lisible
    texte = json.dumps(msg) + "\n"#afin de transfprmer un dictionnaire en  format json et aussi ajouter \n vers la fin pour que recv peut  savoir ou s'arreter 
    sock.sendall(texte.encode("utf-8"))    # .encode("utf-8") → convertit le texte en octets (les sockets n'acceptent que des octets)
    # sendall() → garantit que TOUT est envoyé, même si ça prend plusieurs appels réseau

#----------recevoir def recevoir(sock):
    """
    Reçoit un message JSON COMPLET depuis le serveur.
 
    On accumule les morceaux dans un buffer jusqu'à trouver le \n
    qui indique que le message est complet.
 
    Retourne : un dictionnaire Python (le message décodé)
    """
def recevoir(sock):

    buffer = b""#b"" c une chaine de char vide 
    while b"\n" not in buffer: # tant que mzal on apas lit le \n
        morceau = sock.recv(4096)  # lire jusqu'a 4096 octets
 
        # Si recv() retourne b"" (vide), le serveur a ferme la connexion
        if not morceau:
            raise Exception("Le serveur a fermé la connexion")
 
        buffer += morceau  # nhto wach qrina dans buffer
 
    # .decode("utf-8") → reconvertit les octets en texte
    # .strip()         → enlève le \n et les espaces en trop
    # json.loads()     → transforme le texte JSON en dict Python (inverse de json.dumps)
    return json.loads(buffer.decode("utf-8").strip())

#---------------------echange certificats 
def envoyer_cert(sock):

    with open("certs/client.crt", "rb") as f:
        mon_cert = f.read()

    envoyer(sock, "CERT", data=mon_cert.hex())#converti mon cert en octet et l'envoyer


def recevoir_cert(sock):
    msg = recevoir(sock)

    if msg["type"] != "CERT":
        raise Exception("Certificat attendu")

    return bytes.fromhex(msg["data"])#