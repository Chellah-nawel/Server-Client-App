import subprocess
import os


def generer_certificat(nom="MonServeur", pays="DZ", ville="Alger", org="USTHB", dossier="certs", jours=365):
    os.makedirs(dossier, exist_ok=True)

    prefixe      = nom.lower().replace(" ", "_")
    cle_privee   = f"{dossier}/{prefixe}_private.pem"
    certificat   = f"{dossier}/{prefixe}_cert.pem"
    cle_publique = f"{dossier}/{prefixe}_public.pem"

    subprocess.run(["openssl", "genrsa", "-out", cle_privee, "2048"],
                   check=True, capture_output=True)

    sujet = f"/C={pays}/ST={ville}/L={ville}/O={org}/CN={nom}"
    subprocess.run(["openssl", "req", "-new", "-x509",
                    "-key", cle_privee, "-out", certificat,
                    "-days", str(jours), "-subj", sujet],
                   check=True, capture_output=True)

    subprocess.run(["openssl", "x509", "-pubkey", "-noout",
                    "-in", certificat, "-out", cle_publique],
                   check=True, capture_output=True)

    print("\nCertificat genere avec succes !")
    print(f"  Nom          : {nom}")
    print(f"  Pays         : {pays}")
    print(f"  Ville        : {ville}")
    print(f"  Organisation : {org}")
    print(f"  Validite     : {jours} jours")
    print(f"  Cle privee   : {cle_privee}")
    print(f"  Certificat   : {certificat}")
    print(f"  Cle publique : {cle_publique}")

    return {"cle_privee": cle_privee, "certificat": certificat, "cle_publique": cle_publique}


def saisir_infos_client():
    print("\n--- Informations du certificat ---")
    nom   = input("Nom (CN)                    : ").strip() or "Client"
    pays  = input("Pays (2 lettres, ex: DZ)    : ").strip().upper() or "DZ"
    ville = input("Ville                       : ").strip() or "Alger"
    org   = input("Organisation                : ").strip() or "USTHB"

    while True:
        jours = input("Validite en jours (1-365)   : ").strip()
        if jours == "":
            jours = 365
            break
        elif jours.isdigit() and 1 <= int(jours) <= 365:
            jours = int(jours)
            break
        else:
            print(" Valeur invalide , Entrez un nombre entre 1 et 365.")

    return nom, pays, ville, org, jours


if __name__ == "__main__":
    nom, pays, ville, org, jours = saisir_infos_client()
    generer_certificat(nom, pays, ville, org, jours=jours)
