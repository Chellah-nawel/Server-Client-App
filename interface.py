import customtkinter as ctk
from tkinter import filedialog
import threading
from secu import generer_ca, generer_certificat
from client import (
    creer_client,
    env_cert,
    rec_verif_cert,
    extraire_cle_pub,
    envoyer_cle_session,
    envoyer_fichier,
    recevoir_reponse
)
from chiff import init_session

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Système Client-Serveur Sécurisé")
        self.geometry("1200x700")

        # ================= STATE =================
        # État global du système
        self.clients_connectes = 0
        self.client_id         = 0
        self.validated         = False
        self.current_client    = ""

        # ── Ajouts pour la vraie logique réseau ──
        self.sock              = None   # socket TCP actif vers le serveur
        self.cert_path         = None   # chemin du certificat du client genere
        self.cle_pub_serv_path = None   # cle pub serveur (pour init session)
        self.cle_session       = None   # cle aes de session, generee une fois par connexion
        self.profile           = {}     # infos du profil saisi dans le popup

        # ================= MAIN LAYOUT =================
        self.main = ctk.CTkFrame(self, fg_color="#0b0f1a")
        self.main.pack(fill="both", expand=True, padx=10, pady=10)

        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_columnconfigure(1, weight=2)

        # Interface du serveur
        self.server_frame = ctk.CTkFrame(
            self.main,
            fg_color="#121a2a",
            corner_radius=15
        )
        self.server_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            self.server_frame,
            text="🖥 SERVEUR ACTIF",
            font=("Arial", 20, "bold"),
            text_color="#00ff99"
        ).pack(pady=10)

        self.server_status = ctk.CTkLabel(
            self.server_frame,
            text="🟢 Listening...",
            text_color="#22c55e"
        )
        self.server_status.pack()

        self.client_count = ctk.CTkLabel(
            self.server_frame,
            text="Clients connectés : 0",
            text_color="#facc15"
        )
        self.client_count.pack(pady=5)

        # LISTE CLIENTS
        self.client_list = ctk.CTkTextbox(
            self.server_frame,
            height=80,
            fg_color="#0a0f18"
        )
        self.client_list.pack(fill="x", padx=10, pady=5)

        self.server_log = ctk.CTkTextbox(
            self.server_frame,
            fg_color="#0a0f18",
            text_color="#00ff99",
            corner_radius=10
        )
        self.server_log.pack(fill="both", expand=True, padx=10, pady=10)

        # Interface utilisateur client
        self.client_frame = ctk.CTkFrame(
            self.main,
            fg_color="#121a2a",
            corner_radius=15
        )
        self.client_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(
            self.client_frame,
            text="👤 CLIENT",
            font=("Arial", 20, "bold"),
            text_color="#60a5fa"
        ).pack(pady=10)

        self.connect_btn = ctk.CTkButton(
            self.client_frame,
            text="Créer Profil / Connexion",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.open_profile
        )
        self.connect_btn.pack(pady=10)

        self.pipeline = ctk.CTkLabel(
            self.client_frame,
            text="⏳ En attente..."
        )
        self.pipeline.pack(pady=5)

        self.file_entry = ctk.CTkEntry(
            self.client_frame,
            width=300,
            placeholder_text="Chemin fichier..."
        )
        self.file_entry.pack(pady=5)

        self.file_buttons_frame = ctk.CTkFrame(self.client_frame, fg_color="transparent")
        self.file_buttons_frame.pack(pady=5)

        self.browse_btn = ctk.CTkButton(
            self.file_buttons_frame,
            text="📁 Parcourir",
            fg_color="#334155",
            hover_color="#475569",
            command=self.select_file,
            width=140
        )
        self.browse_btn.pack(side="left", padx=5)

        self.send_btn = ctk.CTkButton(
            self.file_buttons_frame,
            text="🚀 Envoyer",
            fg_color="#0c4923",
            hover_color="#0b5f2a",
            state="disabled",
            command=self.send_file,
            width=140
        )
        self.send_btn.pack(side="left", padx=5)

        self.actions_buttons_frame = ctk.CTkFrame(self.client_frame, fg_color="transparent")
        self.actions_buttons_frame.pack(pady=5)

        self.reset_btn = ctk.CTkButton(
            self.actions_buttons_frame,
            text="🔄 Réinitialiser",
            fg_color="#dc2626",
            hover_color="#991b1b",
            command=self.reset,
            width=140
        )
        self.reset_btn.pack(side="left", padx=5)

        self.disconnect_btn = ctk.CTkButton(
            self.actions_buttons_frame,
            text="🔌 Déconnexion",
            fg_color="#7f1d1d",
            hover_color="#991b1b",
            command=self.disconnect_client,
            width=140
        )
        self.disconnect_btn.pack(side="left", padx=5)

        self.progress = ctk.CTkProgressBar(
            self.client_frame,
            progress_color="#3b82f6"
        )
        self.progress.set(0)
        self.progress.pack(fill="x", padx=20, pady=10)

        self.client_log = ctk.CTkTextbox(
            self.client_frame,
            fg_color="#0a0f18",
            text_color="white",
            corner_radius=10
        )
        self.client_log.pack(fill="both", expand=True, padx=10, pady=10)

    # ================= LOG =================
    def log(self, box, tag, msg):
        box.insert("end", f"[{tag}] {msg}\n")
        box.see("end")

    # ================= PROFILE =================
    def open_profile(self):

        self.popup = ctk.CTkToplevel(self)
        self.popup.title("Profil Client")
        self.popup.geometry("380x300")
        self.popup.grab_set()
        self.popup.configure(fg_color="#0b0f1a")

        frame = ctk.CTkFrame(self.popup, fg_color="#121a2a")
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            frame,
            text="Création Profil",
            font=("Arial", 18, "bold"),
            text_color="#60a5fa"
        ).pack(pady=10)

        self.nom  = ctk.CTkEntry(frame, placeholder_text="Nom")
        self.nom.pack(pady=5)

        self.pays = ctk.CTkEntry(frame, placeholder_text="Pays (ex: DZ)")
        self.pays.pack(pady=5)

        self.ville = ctk.CTkEntry(frame, placeholder_text="Ville")
        self.ville.pack(pady=5)

        # Organisation = toujours USTHB (fixe, meme que le serveur)
        # Duree = 60 jours automatiquement

        ctk.CTkButton(
            frame,
            text="Connexion",
            fg_color="#16a34a",
            command=self.connect_client
        ).pack(pady=15)

    # Connexion d'un client et ajout côté serveur
    def connect_client(self):

        name = self.nom.get()
        if not name:
            self.log(self.client_log, "ERROR", "Nom requis")
            return

        # Stocker les infos du profil pour generer_certificat() dans cert_process
        # Organisation fixee a USTHB (identique au serveur)
        # Duree fixee a 60 jours automatiquement
        self.profile = {
            "nom"   : name,
            "pays"  : self.pays.get().upper() or "DZ",
            "ville" : self.ville.get() or "Alger",
            "org"   : "USTHB",
            "jours" : 60
        }
        self.popup.destroy()

        self.client_id += 1
        # Afficher le vrai nom du client au lieu de "Client N"
        self.current_client = name

        self.clients_connectes += 1
        self.client_count.configure(text=f"Clients connectés : {self.clients_connectes}")
        self.client_list.insert("end", f"{self.current_client}\n")
        self.log(self.client_log, "CONNECT", f"{self.current_client} en cours de connexion...")
        self.log(self.server_log, "SERVER",  f"{self.current_client} tente de se connecter")

        # Lancer la vraie procédure de connexion + certificat dans un thread
        # (évite de bloquer l'interface pendant les opérations réseau)
        threading.Thread(target=self.cert_process, daemon=True).start()

    # ── Remplace la simulation random() par la vraie procédure ──
    def cert_process(self):
        """
        Vraie procédure de connexion et d'échange de certificats :
        1. Génère le certificat client (secu.py)
        2. Connecte le socket au serveur (client.py)
        3. Reçoit et vérifie le certificat serveur
        4. Envoie notre certificat
        5. Extrait la clé publique du serveur (pour chiffrer les fichiers)
        """
        try:
            # ── 1. Générer le certificat client ────────────────
            self.pipeline.configure(text="🔐 Génération certificat...")
            self.log(self.client_log, "CERT", "Génération certificat en cours...")

            # generer_ca() crée la CA si elle n'existe pas encore
            generer_ca()
            result = generer_certificat(
                self.profile["nom"],
                self.profile["pays"],
                self.profile["ville"],
                self.profile["org"],
                self.profile["jours"]
            )
            self.cert_path = result["certificat"]
            self.log(self.client_log, "CERT", f"Certificat généré : {self.cert_path}")

            # ── 2. Connexion socket au serveur ─────────────────
            self.pipeline.configure(text="🔌 Connexion au serveur...")
            self.sock = creer_client()
            self.log(self.client_log, "CONNECT", "Socket connecté au serveur")

            # ── 3. Recevoir et vérifier le certificat serveur ──
            self.pipeline.configure(text="📥 Vérification certificat serveur...")
            self.log(self.server_log, "CERT", "Envoi certificat serveur...")
            cert_serv_path = rec_verif_cert(self.sock)
            self.log(self.server_log, "CERT", "Validation certificat client...")

            # ── 4. Envoyer notre certificat au serveur ──────────
            self.pipeline.configure(text="📤 Envoi certificat client...")
            env_cert(self.sock, self.cert_path)
            self.log(self.client_log, "CERT", "Certificat envoyé au serveur")

            # ── 5. Extraire la clé publique du serveur ──────────
            # Nécessaire pour chiffrer la clé AES avec RSA lors de l'envoi de fichiers
            self.cle_pub_serv_path = extraire_cle_pub(cert_serv_path)

            # ── 6. Generer et envoyer la cle de session ─────────
            # une seule cle aes pour toute la session, le serv va la garder
            self.pipeline.configure(text="🔑 Init session AES...")
            cle_session, cle_session_enc = init_session(self.cle_pub_serv_path)
            self.cle_session = cle_session
            envoyer_cle_session(self.sock, cle_session_enc)
            self.log(self.client_log, "SECURITY", "cle de session envoyee au serveur")

            # ── Succès ─────────────────────────────────────────
            self.validated = True
            self.pipeline.configure(text="✔ Certificat validé")
            self.log(self.client_log, "SUCCESS", "Certificat serveur validé ✓")
            self.log(self.server_log, "SUCCESS", "Certificat client OK ✓")
            self.send_btn.configure(state="normal")

        except Exception as e:
            # Échec : certificat invalide ou erreur réseau
            self.validated = False
            self.pipeline.configure(text="❌ Certificat refusé")
            self.log(self.client_log, "ERROR", f"Erreur : {e}")
            self.log(self.server_log, "ERROR", "Certificat invalide ou connexion échouée")

    # ================= FILE =================
    def select_file(self):
        file = filedialog.askopenfilename()
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, file)

    # Vérification des conditions avant envoi du fichier
    def send_file(self):

        if not self.validated:
            self.log(self.client_log, "ERROR", "Certificat invalide")
            return

        if not self.file_entry.get():
            self.log(self.client_log, "ERROR", "Aucun fichier")
            return

        self.send_btn.configure(state="disabled")
        threading.Thread(target=self.transfer_process, daemon=True).start()

    # ── Remplace la simulation time.sleep() par le vrai transfert ──
    def transfer_process(self):
        """
        Vrai transfert de fichier :
        1. Chiffrement AES + clé RSA (chiff.py)
        2. Envoi au serveur (protocole.py)
        3. Réception de la confirmation
        """
        try:
            chemin = self.file_entry.get()

            # ── 1. Chiffrement ─────────────────────────────────
            self.pipeline.configure(text="🔑 Chiffrement AES...")
            self.log(self.client_log, "SECURITY", "Chiffrement AES du fichier...")
            self.log(self.server_log, "SECURITY",  "Réception fichier en cours...")
            self.progress.set(0.2)

            # ── 2. Envoi ───────────────────────────────────────
            self.pipeline.configure(text="📡 Envoi sécurisé...")
            self.log(self.client_log, "UPLOAD", "Envoi fichier chiffré...")

            # envoyer_fichier() fait : chiff_fichier() + 2x send_msg()
            envoyer_fichier(self.sock, chemin, self.cle_session)
            self.progress.set(0.7)

            # ── 3. Confirmation du serveur ─────────────────────
            self.pipeline.configure(text="📥 Réception confirmation...")
            reponse = recevoir_reponse(self.sock)
            self.progress.set(1.0)

            if reponse and reponse.get("status") == "ok":
                nom    = reponse.get("fichier_recu", "?")
                taille = reponse.get("taille", 0)
                self.log(self.client_log, "SUCCESS", f"Fichier envoyé : {nom}")
                self.log(self.server_log, "SUCCESS",  f"Fichier reçu + déchiffré : {nom} ({taille} bytes)")

            self.pipeline.configure(text="✔ Terminé")

        except Exception as e:
            self.log(self.client_log, "ERROR", f"Erreur envoi : {e}")
            self.pipeline.configure(text="❌ Erreur envoi")

        finally:
            self.send_btn.configure(state="normal")

    # Réinitialisation de l'interface utilisateur
    def reset(self):
        self.file_entry.delete(0, "end")
        self.progress.set(0)
        self.validated = False
        self.send_btn.configure(state="disabled")
        self.log(self.client_log, "SYSTEM", "Reset effectué")

    def disconnect_client(self):

        if self.clients_connectes <= 0:
            return

        # Fermer le socket proprement si ouvert
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

        self.clients_connectes -= 1

        # mise à jour UI serveur
        self.client_count.configure(
            text=f"Clients connectés : {self.clients_connectes}"
        )

        # état sécurité reset
        self.validated         = False
        self.current_client    = ""
        self.cert_path         = None
        self.cle_pub_serv_path = None
        self.cle_session       = None
        self.file_entry.delete(0, "end")
        self.progress.set(0)

        # désactiver envoi
        self.send_btn.configure(state="disabled")

        # reset pipeline
        self.pipeline.configure(text="⏳ Déconnecté")

        # log côté client
        self.log(self.client_log, "SYSTEM", "Client déconnecté")

        # log côté serveur
        self.log(self.server_log, "SERVER", f"{self.current_client} déconnecté")
