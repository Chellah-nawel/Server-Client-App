import os
import subprocess

#create dossier pour stocker certificats
dossier="certs"
os.makedirs(dossier, exist_ok=True) #cree le dossier "certs/"


def generer_ca(): #genere l'autorité de certification (ca)
    """
    Produit : ca_private.pem (clé privée) et ca_cert.pem (certificat CA)
    IMPORTANT : sans CA, la vérification des certificats est impossible.
    Le serveur et le client ont chacun un certificat SIGNÉ par cette CA.
    """
    
    ca_cle = f"{dossier}/ca_cle.priv"
    ca_cert = f"{dossier}/ca_cert.crt"

    #si CA existe deja ne pas la regénérer 
    if os.path.exists(ca_cert):
        return ca_cle, ca_cert
    """si on la refaite les ancient certs ne seront pas valid"""


    #la clé privée de CA 
    #   openssl genrsa -out ca_cle.priv 2048
    subprocess.run(["openssl", "genrsa", "-out", ca_cle, "2048"], 
    check=True, capture_output=True, stdin=subprocess.DEVNULL)   

    """
    we run subprocess that way cuz its safer
    check c pour f the command fails raise an error
    captureoutput default, the command prints directly to the terminal
    """

    """
    # req          →  outil de gestion des requetes de certificat
    # -new         →  nouvelle requete
    # -x509        →  creer un certificat auto-signe UNIQUEMENT pour la CA
    # -key         →  cle privee a utiliser pour signer
    # -out         →  fichier de sortie du certificat
    # -days 60     →  valide 2 mois
    # -subj        →  informations de la CA en une seul ligne 
    #   /C=DZ      →  Country : Algerie
    #   /ST=Alger  →  State   : wilaya
    #   /O=USTHB   →  Organization
    #   /CN=CAutho     →  Common Name : nom de la CA
    """
    #commande:          openssl req -new -x509 -key ca_cle.priv -out ca_cert.crt -days 60 -subj...
    subprocess.run(["openssl", "req", "-new","-x509","-key", ca_cle, "-out", ca_cert,
                    "-days", "60","-subj", "/C=DZ/ST=Alger/L=Alger/O=USTHB/CN=CAutho"],
    check=True, capture_output=True, stdin=subprocess.DEVNULL)#its auto signed req -x509

    return ca_cle, ca_cert


def saisir_infos_client():
    nom = input("Nom                         : ").strip() or "Client"
    pays = input("Pays (2 lettres, ex: DZ)    : ").strip().upper() or "DZ"
    ville = input("Ville                       : ").strip() or "Alger"
    org = input("Organisation                : ").strip() or "USTHB"

    while True:
        jours = input("Validite en jours(1-60) : ").strip()
        if jours == "":
            jours = 60
            break
        elif jours.isdigit() and 1 <= int(jours) <= 60:
            jours = int(jours)
            break
        else:
            print("Duree invalide, Entrez un nombre entre 1 et 60.")    
    return nom, pays, ville, org, jours



def generer_certificat(nom=None, pays=None, ville=None, org=None, jours=None):

    if nom is None:
        nom, pays, ville, org, jours = saisir_infos_client()

    sujet = f"/C={pays}/ST={ville}/L={ville}/O={org}/CN={nom}"
    """
    # Sujet du certificat au format X.509
    # /C=  Country     /ST= State(wilaya)   /L= Locality(ville)
    # /O=  Organization                     /CN= Common Name (nom)"""


    base = nom.lower().replace(" ", "_")    #nom de base pour les fichier "INFO usthb" => "info_usthb"

    cle_privee = f"{dossier}/{base}.priv"   # cle privee du client
    certificat = f"{dossier}/{base}.crt"   # certificat final
    cle_publique = f"{dossier}/{base}.pub"   # cle publique extraite

    csr = f"{dossier}/{base}.csr"   # demande de signature (temporaire)

    ca_cle = f"{dossier}/ca_cle.priv"
    ca_cert = f"{dossier}/ca_cert.crt"

    #gerere cle priv client
    #   openssl genrsa -out clientname.priv 2048
    subprocess.run(["openssl", "genrsa", "-out", cle_privee, "2048"],
    check=True, capture_output=True, stdin=subprocess.DEVNULL)

    #extraire cle pub
    #   openssl rsa -in clientname.priv -pubout -out clientname.pub
    subprocess.run(["openssl", "rsa", "-in", cle_privee, "-pubout", "-out", cle_publique],
    check=True, capture_output=True, stdin=subprocess.DEVNULL)


    #demande de signature de CA pour cree cert client
    #   openssl req -new -key clientname.priv -out clientname.csr -subj sujet...
    subprocess.run(["openssl","req","-new","-key", cle_privee,"-out", csr, "-subj", sujet],
    check=True, capture_output=True, stdin=subprocess.DEVNULL)

    #cree cert client signee par CA
    #   openssl x509 -req -in clientname.csr -CA ca_cert.crt -CAkey ca_cle.priv
    subprocess.run(["openssl", "x509", "-req","-in", csr,"-CA", ca_cert,
                "-CAkey", ca_cle,"-CAcreateserial","-out", certificat,"-days", "60"],
    check=True, capture_output=True, stdin=subprocess.DEVNULL)

    os.remove(csr)

    return {
        "succes"      : True,
        "cle_privee"  : cle_privee,
        "certificat"  : certificat,
        "cle_publique": cle_publique
    }


def generer_serv_certificat():    #execute once

    #recupere CA
    ca_cle  = f"{dossier}/ca_cle.priv"
    ca_cert = f"{dossier}/ca_cert.crt"

    cle_priv = f"{dossier}/cle_serv.priv"
    cle_pub =f"{dossier}/cle_serv.pub"
    cert = f"{dossier}/cert_serv.crt"
    csr = f"{dossier}/serv.csr"

    if os.path.exists(cert):
        print("Certificat serveur exist")
        return cle_priv, cle_pub, cert

    sujet = "/C=DZ/ST=Alger/L=Alger/O=USTHB/CN=Serveur"

    #genere cle priv du serv
    #   openssl genrsa -out cle_serv.priv 2048
    subprocess.run(["openssl", "genrsa", "-out", cle_priv, "2048"],
    check=True, capture_output=True, stdin=subprocess.DEVNULL)
    
    #extraire cle pub 
    #   openssl rsa -in cle_serv.priv -pubout -out cle_serv.pub
    subprocess.run(["openssl", "rsa", "-in", cle_priv, "-pubout", "-out", cle_pub],
    check=True, capture_output=True, stdin=subprocess.DEVNULL)

    #demande de signature de CA pour cree cert serv
    #   openssl req -new -key cle_serv.priv -out serv.csr -subj ...
    subprocess.run(["openssl","req","-new","-key", cle_priv,"-out", csr, "-subj", sujet],
    check=True, capture_output=True, stdin=subprocess.DEVNULL)

    #cree cert serv signee par ca
    # openssl x509 -req -in serv.csr -CA ca_cert.crt -CAkey ca_cle.priv
    subprocess.run(["openssl", "x509", "-req","-in", csr,"-CA", ca_cert,
                    "-CAkey", ca_cle,"-CAcreateserial","-out", cert,"-days", "60"],
    check=True, capture_output=True, stdin=subprocess.DEVNULL)

    #supp le fichier temp
    os.remove(csr)

    return cle_priv ,cle_pub ,cert

def verifier_certificat(certificat_path):
    """
    Cette commande vérifie automatiquement :
      - la signature (signée par notre CA ?)
      - la date (pas expiré ?)
      - la chaîne de confiance
    Serveur l'appelle pour vérifier le client
    Client l'appelle pour vérifier le serveur
    """
    ca_cert = f"{dossier}/ca_cert.crt"  #recupere le certificat de CA

    #verifie signature date
    #   openssl verify -CAfile ca_cert.crt clientname.crt(cert_serv.crt)
    # timeout=15 : evite le freeze infini sur Windows si openssl ne repond pas
    # stdin=subprocess.DEVNULL : empeche openssl d'attendre une saisie clavier
    result = subprocess.run(["openssl", "verify", "-CAfile", ca_cert, certificat_path],
        capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL
    )

    if result.returncode == 0:
        print(f"[OK] Certificat valide ")
        return True
    else:
        # openssl affiche le problème exact
        print(f"[ERREUR] {result.stderr}")
        return False

if __name__ == "__main__":

    generer_ca()                      # 1. CA (une seule fois)
    #generer_serv_certificat()      # 2. Serveur (fixe)
    #generer_certificat("serveur", "DZ", "alger","USTHB", "60") 

    #nom, pays, ville, org, jours = saisir_infos_client()
    #generer_certificat(nom, pays, ville, org, jours)   # 3. Client (saisi)
    verifier_certificat("certs\hi.crt")
