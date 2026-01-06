import customtkinter as ctk
from tkinter import messagebox, filedialog
import subprocess
import threading
import os
import sys
import json
import io
import urllib.request

# --- IMPORTAÇÃO DAS BIBLIOTECAS ---
try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    print("AVISO: Instale 'qrcode' e 'pillow' (pip install qrcode pillow).")

try:
    from plyer import notification
    NOTIFY_AVAILABLE = True
except ImportError:
    NOTIFY_AVAILABLE = False

# --- CONFIGURAÇÃO VISUAL ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

NEON_CYAN = "#00ADB5"
DARK_BG = "#121212"
PANEL_BG = "#1E1E1E"
TEXT_COLOR = "#EEEEEE"

# ==============================================================================
# 💰 CONFIGURAÇÃO DO PIX
# ==============================================================================
PIX_PAYLOAD = "00020126820014br.gov.bcb.pix0136071008b9-3dd2-4c2a-b8f7-6f9eccedf67d0220Obrigado pela doacao27600016BR.COM.PAGSEGURO01362BB9F5B4-7082-4368-A102-216475FCA1D45204899953039865802BR5923FABIO FERREIRA DA SILVA6006Escada62290525PAGS000000000251231194671630497DA" 
# ==============================================================================

class ShurXitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ShurXit Downloader - V1")
        self.geometry("1100x850")
        self.minsize(1000, 700)
        self.configure(fg_color=DARK_BG)
        self.attributes('-alpha', 0.98) 
        
        # Inicia maximizado no Windows
        if os.name == 'nt':
            self.after(0, lambda: self.state('zoomed'))

        # --- GRID LAYOUT ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1) # Área central estica
        self.grid_rowconfigure(3, weight=0) # Manual Input fixo
        self.grid_rowconfigure(4, weight=0) # Rodapé fixo

        # --- CONFIGURAÇÕES DE DIRETÓRIOS (APPDATA) ---
        app_data = os.getenv('LOCALAPPDATA')
        self.config_folder = os.path.join(app_data, "ShurXit_Downloader")
        self.bin_folder = os.path.join(self.config_folder, "bin") 
        
        for folder in [self.config_folder, self.bin_folder]:
            if not os.path.exists(folder):
                try: os.makedirs(folder)
                except: pass

        self.config_file = os.path.join(self.config_folder, "shurxit_config.json")
        self.local_engine_path = os.path.join(self.bin_folder, "gallery-dl.exe")

        self.config_data = self.load_config()
        self.download_dir = self.config_data.get("path", os.path.join(os.path.expanduser("~"), "Downloads", "ShurXit_Media"))
        self.selected_browser = ctk.StringVar(value=self.config_data.get("browser", "Nenhum (Padrão)"))

        if not os.path.exists(self.download_dir):
            try: os.makedirs(self.download_dir)
            except: pass

        # Variáveis
        self.is_monitoring = ctk.BooleanVar(value=True)
        self.last_clipboard_text = ""
        self.active_downloads = 0
        self.total_files_session = 0
        self.queue_items = []
        
        # --- LISTA COMPLETA DE SITES ---
        self.sites_config = {
            # --- Populares / Redes Sociais ---
            "Twitter / X": {"keyword": "x.com", "enabled": ctk.BooleanVar(value=True)},
            "Twitter (Old)": {"keyword": "twitter.com", "enabled": ctk.BooleanVar(value=True)},
            "Instagram": {"keyword": "instagram.com", "enabled": ctk.BooleanVar(value=True)},
            "Reddit": {"keyword": "reddit.com", "enabled": ctk.BooleanVar(value=True)},
            "TikTok": {"keyword": "tiktok.com", "enabled": ctk.BooleanVar(value=True)},
            "Facebook": {"keyword": "facebook.com", "enabled": ctk.BooleanVar(value=True)},
            "Pinterest": {"keyword": "pinterest", "enabled": ctk.BooleanVar(value=True)},
            "Tumblr": {"keyword": "tumblr.com", "enabled": ctk.BooleanVar(value=True)},
            "VK": {"keyword": "vk.com", "enabled": ctk.BooleanVar(value=True)},
            "Flickr": {"keyword": "flickr.com", "enabled": ctk.BooleanVar(value=True)},
            "Bluesky": {"keyword": "bsky.app", "enabled": ctk.BooleanVar(value=True)},
            "Mastodon": {"keyword": "mastodon", "enabled": ctk.BooleanVar(value=True)},
            "Patreon": {"keyword": "patreon.com", "enabled": ctk.BooleanVar(value=True)},
            "SubscribeStar": {"keyword": "subscribestar", "enabled": ctk.BooleanVar(value=True)},
            "Fansly": {"keyword": "fansly.com", "enabled": ctk.BooleanVar(value=True)},
            "OnlyFans": {"keyword": "onlyfans", "enabled": ctk.BooleanVar(value=True)},

            # --- Imageboards / Boorus / Anime ---
            "4Chan": {"keyword": "4chan.org", "enabled": ctk.BooleanVar(value=True)},
            "2ch": {"keyword": "2ch", "enabled": ctk.BooleanVar(value=True)},
            "8chan": {"keyword": "8chan", "enabled": ctk.BooleanVar(value=True)},
            "Danbooru": {"keyword": "danbooru", "enabled": ctk.BooleanVar(value=True)},
            "Gelbooru": {"keyword": "gelbooru", "enabled": ctk.BooleanVar(value=True)},
            "Rule34": {"keyword": "rule34", "enabled": ctk.BooleanVar(value=True)},
            "Konachan": {"keyword": "konachan", "enabled": ctk.BooleanVar(value=True)},
            "Yandere": {"keyword": "yande.re", "enabled": ctk.BooleanVar(value=True)},
            "Sankaku Channel": {"keyword": "sankaku", "enabled": ctk.BooleanVar(value=True)},
            "E-Hentai": {"keyword": "e-hentai", "enabled": ctk.BooleanVar(value=True)},
            "ExHentai": {"keyword": "exhentai", "enabled": ctk.BooleanVar(value=True)},
            "NHentai": {"keyword": "nhentai", "enabled": ctk.BooleanVar(value=True)},
            "Hitomi.la": {"keyword": "hitomi.la", "enabled": ctk.BooleanVar(value=True)},
            "Pixiv": {"keyword": "pixiv.net", "enabled": ctk.BooleanVar(value=True)},
            "Kemono": {"keyword": "kemono", "enabled": ctk.BooleanVar(value=True)},
            "Coomer": {"keyword": "coomer", "enabled": ctk.BooleanVar(value=True)},
            
            # --- Sites Adultos / Galerias ---
            "EroMe": {"keyword": "erome.com", "enabled": ctk.BooleanVar(value=True)},
            "Pornhub": {"keyword": "pornhub.com", "enabled": ctk.BooleanVar(value=True)},
            "XVideos": {"keyword": "xvideos.com", "enabled": ctk.BooleanVar(value=True)},
            "XHamster": {"keyword": "xhamster.com", "enabled": ctk.BooleanVar(value=True)},
            "8muses": {"keyword": "8muses", "enabled": ctk.BooleanVar(value=True)},
            "Cyberdrop": {"keyword": "cyberdrop", "enabled": ctk.BooleanVar(value=True)},
            "Bunkr": {"keyword": "bunkr", "enabled": ctk.BooleanVar(value=True)},
            "ImageFap": {"keyword": "imagefap", "enabled": ctk.BooleanVar(value=True)},
            "Luscious": {"keyword": "luscious", "enabled": ctk.BooleanVar(value=True)},
            "Motherless": {"keyword": "motherless", "enabled": ctk.BooleanVar(value=True)},
            "Xasiat": {"keyword": "xasiat", "enabled": ctk.BooleanVar(value=True)},
            "Fapello": {"keyword": "fapello", "enabled": ctk.BooleanVar(value=True)},
            "FitNakedGirls": {"keyword": "fitnakedgirls", "enabled": ctk.BooleanVar(value=True)},
            "ViperGirls": {"keyword": "vipergirls", "enabled": ctk.BooleanVar(value=True)},

            # --- Arte / Fotografia / Outros ---
            "ArtStation": {"keyword": "artstation.com", "enabled": ctk.BooleanVar(value=True)},
            "DeviantArt": {"keyword": "deviantart.com", "enabled": ctk.BooleanVar(value=True)},
            "Behance": {"keyword": "behance.net", "enabled": ctk.BooleanVar(value=True)},
            "500px": {"keyword": "500px.com", "enabled": ctk.BooleanVar(value=True)},
            "Imgur": {"keyword": "imgur.com", "enabled": ctk.BooleanVar(value=True)},
            "ImageBam": {"keyword": "imagebam", "enabled": ctk.BooleanVar(value=True)},
            "ImageTwist": {"keyword": "imagetwist", "enabled": ctk.BooleanVar(value=True)},
            "PixelDrain": {"keyword": "pixeldrain", "enabled": ctk.BooleanVar(value=True)},
            "GoFile": {"keyword": "gofile.io", "enabled": ctk.BooleanVar(value=True)},
            "Catbox": {"keyword": "catbox.moe", "enabled": ctk.BooleanVar(value=True)},

            # --- Mangá / HQs ---
            "MangaDex": {"keyword": "mangadex", "enabled": ctk.BooleanVar(value=True)},
            "MangaNelo": {"keyword": "manganelo", "enabled": ctk.BooleanVar(value=True)},
            "Webtoons": {"keyword": "webtoons", "enabled": ctk.BooleanVar(value=True)},
            "Tapas": {"keyword": "tapas.io", "enabled": ctk.BooleanVar(value=True)},

            # --- GENÉRICO (Captura tudo que sobrar) ---
            "Outros Sites (Links Genéricos)": {"keyword": "http", "enabled": ctk.BooleanVar(value=True)} 
        }

        # --- CONSTRUÇÃO DA INTERFACE ---
        self.create_menu()
        self.create_header()
        self.create_progress_area()
        self.create_main_content_area()
        self.create_manual_input_area()
        self.create_donation_area() 

        # Inicialização
        self.update_status_display()
        self.check_clipboard_loop()
        
        # Inicia atualização em background
        threading.Thread(target=self.auto_update_engine, daemon=True).start()

    # ================= LAYOUT =================

    def create_menu(self):
        import tkinter as tk
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0, bg=PANEL_BG, fg=TEXT_COLOR)
        file_menu.add_command(label="Abrir Pasta Atual", command=self.open_download_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        options_menu = tk.Menu(menubar, tearoff=0, bg=PANEL_BG, fg=TEXT_COLOR)
        options_menu.add_command(label="📂 Escolher Pasta...", command=self.choose_download_folder)
        menubar.add_cascade(label="Opções", menu=options_menu)
        sites_menu = tk.Menu(menubar, tearoff=0, bg=PANEL_BG, fg=TEXT_COLOR)
        sites_menu.add_command(label="Filtrar Sites", command=self.open_site_manager)
        menubar.add_cascade(label="Sites", menu=sites_menu)
        self.config(menu=menubar)

    def create_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=10)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 5))

        control_bar = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        control_bar.pack(fill="x", padx=15, pady=(10, 5))

        self.lbl_status = ctk.CTkLabel(control_bar, text="MONITOR: ATIVO", font=ctk.CTkFont(size=14, weight="bold"), text_color=NEON_CYAN)
        self.lbl_status.pack(side="left")

        self.switch_monitor = ctk.CTkSwitch(control_bar, text="", command=self.toggle_monitoring_switch, variable=self.is_monitoring, progress_color=NEON_CYAN, width=40)
        self.switch_monitor.pack(side="left", padx=10)

        # Status do Motor
        self.lbl_update = ctk.CTkLabel(control_bar, text="", font=ctk.CTkFont(size=11), text_color="gray")
        self.lbl_update.pack(side="right")

        self.lbl_instruction = ctk.CTkLabel(control_bar, text="⚡ Modo Automático: Basta copiar o link (Ctrl+C)", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
        self.lbl_instruction.pack(side="left", padx=20)

        info_bar = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        info_bar.pack(fill="x", padx=15, pady=(5, 10))

        self.lbl_path = ctk.CTkLabel(info_bar, text=f"📂 Salvando em: {self.download_dir}", font=ctk.CTkFont(size=11), text_color="gray")
        self.lbl_path.pack(side="left")

        ctk.CTkLabel(info_bar, text="Cookies:", font=ctk.CTkFont(size=11)).pack(side="right", padx=(10, 0))
        self.browser_combobox = ctk.CTkComboBox(info_bar, values=["Nenhum (Padrão)", "chrome", "firefox", "edge", "opera", "brave"], width=140, height=22, variable=self.selected_browser, command=self.save_browser_preference, fg_color="#333333", border_color=NEON_CYAN)
        self.browser_combobox.pack(side="right")

    def create_progress_area(self):
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=5)
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=10, corner_radius=6, progress_color=NEON_CYAN)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        self.lbl_counter = ctk.CTkLabel(self.progress_frame, text="Arquivos na Sessão: 0", font=ctk.CTkFont(size=11, weight="bold"), text_color=NEON_CYAN)
        self.lbl_counter.grid(row=1, column=1, sticky="e")

    def create_main_content_area(self):
        queue_container = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=10)
        queue_container.grid(row=2, column=0, sticky="nsew", padx=(15, 5), pady=5)
        queue_container.grid_rowconfigure(1, weight=1)
        queue_container.grid_columnconfigure(0, weight=1)

        header_queue = ctk.CTkFrame(queue_container, fg_color="transparent")
        header_queue.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(header_queue, text="Fila de Detecção:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkButton(header_queue, text="Limpar", width=60, height=20, fg_color="#333333", command=self.clear_queue_visuals).pack(side="right")

        self.queue_scroll_frame = ctk.CTkScrollableFrame(queue_container, fg_color="transparent")
        self.queue_scroll_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        console_container = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=10)
        console_container.grid(row=2, column=1, sticky="nsew", padx=(5, 15), pady=5)
        console_container.grid_rowconfigure(1, weight=1)
        console_container.grid_columnconfigure(0, weight=1)

        header_console = ctk.CTkFrame(console_container, fg_color="transparent")
        header_console.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(header_console, text="Console de Execução:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        ctk.CTkButton(header_console, text="Limpar", width=60, height=20, fg_color="#333333", command=self.clear_log).pack(side="right")

        self.text_log = ctk.CTkTextbox(console_container, font=ctk.CTkFont(family="Consolas", size=11), fg_color="#1a1a1a", text_color="#cccccc")
        self.text_log.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.text_log.configure(state="disabled")

    def create_manual_input_area(self):
        input_container = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=10)
        input_container.grid(row=3, column=0, columnspan=2, sticky="ew", padx=15, pady=5)
        ctk.CTkLabel(input_container, text="Download Manual:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=15)
        self.manual_entry = ctk.CTkEntry(input_container, placeholder_text="Cole o link aqui se o monitor estiver desligado...", width=400, border_color=NEON_CYAN)
        self.manual_entry.pack(side="left", padx=10, fill="x", expand=True)
        btn_manual = ctk.CTkButton(input_container, text="Baixar Agora", width=120, fg_color=NEON_CYAN, text_color="black", hover_color="#008c94", command=self.manual_download)
        btn_manual.pack(side="right", padx=15, pady=10)

    def create_donation_area(self):
        if not QR_AVAILABLE: return
        donation_panel = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=15)
        donation_panel.grid(row=4, column=0, columnspan=2, sticky="ew", padx=15, pady=(5, 15))
        donation_panel.grid_columnconfigure(0, weight=1)
        content_frame = ctk.CTkFrame(donation_panel, fg_color="transparent")
        content_frame.grid(row=0, column=0)
        left_footer = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_footer.pack(side="left", padx=20)
        ctk.CTkLabel(left_footer, text="Curtiu o ShurXit?", font=ctk.CTkFont(size=14, weight="bold"), text_color="gray").pack()
        ctk.CTkLabel(left_footer, text="Apoie o dev via Pix!", font=ctk.CTkFont(size=16, weight="bold"), text_color=NEON_CYAN).pack()
        ctk.CTkButton(left_footer, text="Copiar Chave Pix", width=140, fg_color=NEON_CYAN, text_color="black", hover_color="#008c94", command=self.copy_pix).pack(pady=10)
        try:
            qr_gen = qrcode.QRCode(border=1)
            qr_gen.add_data(PIX_PAYLOAD)
            qr_gen.make(fit=True)
            img_wrapper = qr_gen.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img_wrapper.save(buffer, format="PNG")
            buffer.seek(0)
            img_pil = Image.open(buffer)
            self.qr_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=(100, 100))
            lbl_qr = ctk.CTkLabel(content_frame, image=self.qr_ctk, text="")
            lbl_qr.pack(side="left", padx=20, pady=10)
        except: pass

    # ================= LÓGICA DE ATUALIZAÇÃO SEGURA =================
    
    def auto_update_engine(self):
        """Baixa gallery-dl.exe para a pasta AppData (sem erro de permissão)"""
        self.lbl_update.configure(text="Verificando Motor...", text_color="#E67E22")
        url = "https://github.com/mikf/gallery-dl/releases/latest/download/gallery-dl.exe"
        
        try:
            # Baixa diretamente para a pasta segura em AppData
            urllib.request.urlretrieve(url, self.local_engine_path)
            self.lbl_update.configure(text="Motor: Atualizado", text_color="#00FF00")
            self.log("✅ Sistema: gallery-dl atualizado na pasta segura.")
        except Exception as e:
            # Se falhar (ex: sem internet), checa se já existe
            if os.path.exists(self.local_engine_path):
                self.lbl_update.configure(text="Motor: Local (Offline)", text_color="gray")
            else:
                self.lbl_update.configure(text="Motor: Sistema/Ausente", text_color="gray")
            self.log(f"ℹ️ Status Motor: {str(e)[:50]}...")

    # ================= LÓGICA GERAL =================
    
    def manual_download(self):
        url = self.manual_entry.get().strip()
        if url:
            self.log(f"📥 Comando Manual: {url}")
            self.add_to_queue_visual(url)
            threading.Thread(target=self.download_worker, args=(url,), daemon=True).start()
            self.manual_entry.delete(0, "end")
        else:
            messagebox.showwarning("Aviso", "Cole um link primeiro!")

    def toggle_monitoring_switch(self):
        self.update_status_display()

    def update_status_display(self):
        if self.is_monitoring.get():
            self.lbl_status.configure(text="MONITOR: ATIVO", text_color=NEON_CYAN)
            self.lbl_instruction.configure(text="⚡ Modo Automático: Basta copiar o link (Ctrl+C)", text_color="#A0E0A0") 
        else:
            self.lbl_status.configure(text="MONITOR: PAUSADO", text_color="#FF5555")
            self.lbl_instruction.configure(text="✋ Modo Manual: Cole o link na caixa abaixo e clique em Baixar", text_color="#E0A0A0") 

        if self.active_downloads > 0: 
            self.lbl_status.configure(text="BAIXANDO...", text_color="#E67E22")

    def copy_pix(self):
        self.clipboard_clear()
        self.clipboard_append(PIX_PAYLOAD)
        self.send_notification("Pix Copiado", "O código Pix Copia e Cola foi copiado!")

    def send_notification(self, title, message):
        if NOTIFY_AVAILABLE:
            try: notification.notify(title=title, message=message, app_name="ShurXit", timeout=5)
            except: pass

    def load_config(self):
        default = {"path": os.path.join(os.path.expanduser("~"), "Downloads", "ShurXit_Media"), "browser": "Nenhum (Padrão)"}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f: return json.load(f)
            except: pass
        return default
    
    def save_config_full(self):
        data = {"path": self.download_dir, "browser": self.selected_browser.get()}
        try:
            with open(self.config_file, "w") as f: json.dump(data, f)
        except: pass

    def save_browser_preference(self, choice):
        self.save_config_full()
        self.log(f"💾 Navegador salvo: {choice}")

    def choose_download_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.download_dir = f
            self.save_config_full()
            self.lbl_path.configure(text=f"Salvando em: {self.download_dir}")

    def add_to_queue_visual(self, url):
        item = ctk.CTkFrame(self.queue_scroll_frame, fg_color="#2A2A2A")
        item.pack(fill="x", pady=2)
        ctk.CTkLabel(item, text=f"🚀 {url}", anchor="w", padx=10).pack(side="left", pady=5)
        self.queue_items.append(item)

    def clear_queue_visuals(self):
        for i in self.queue_items: i.destroy()
        self.queue_items.clear()
    
    def clear_log(self):
        self.text_log.configure(state="normal")
        self.text_log.delete("0.0", "end")
        self.text_log.configure(state="disabled")

    def log(self, msg):
        self.text_log.configure(state="normal")
        self.text_log.insert("end", msg+"\n")
        self.text_log.see("end")
        self.text_log.configure(state="disabled")

    def increment_file_counter(self):
        self.total_files_session += 1
        self.lbl_counter.configure(text=f"Arquivos na Sessão: {self.total_files_session}")

    def update_progress_state(self, is_downloading):
        if is_downloading:
            self.active_downloads += 1
            if self.active_downloads == 1:
                self.progress_bar.configure(mode="indeterminate")
                self.progress_bar.start()
        else:
            self.active_downloads -= 1
            if self.active_downloads <= 0:
                self.active_downloads = 0
                self.progress_bar.stop()
                self.progress_bar.configure(mode="determinate")
                self.progress_bar.set(0)
        self.update_status_display()

    def open_download_folder(self):
        os.startfile(self.download_dir)

    def open_site_manager(self):
        win = ctk.CTkToplevel(self)
        win.title("Filtro de Sites")
        win.geometry("400x500")
        
        # Correção da janela atrás do painel
        win.transient(self) 
        win.grab_set()      
        win.lift()          
        win.focus_force()   

        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True)
        for name, data in self.sites_config.items():
            ctk.CTkSwitch(scroll, text=name, variable=data["enabled"]).pack(fill="x", padx=10, pady=5)

    def is_site_allowed(self, url):
        # A lógica abaixo respeita o filtro da lista
        url_lower = url.lower()
        matched_specific = False
        
        for site_name, data in self.sites_config.items():
            if site_name == "Outros Sites (Genérico)": continue
            if data["keyword"] in url_lower:
                matched_specific = True
                if not data["enabled"].get():
                    self.log(f"⛔ Bloqueado pelo filtro ({site_name}): {url}")
                    return False
                return True 
                
        if not matched_specific:
            if self.sites_config["Outros Sites (Genérico)"]["enabled"].get():
                return True
            else:
                self.log(f"⛔ Ignorado (Genérico OFF): {url}")
                return False
        return True

    def check_clipboard_loop(self):
        if self.is_monitoring.get():
            try:
                content = self.clipboard_get()
                if content != self.last_clipboard_text:
                    self.last_clipboard_text = content
                    link = content.strip()
                    if link.startswith("http"):
                         if self.is_site_allowed(link):
                             self.add_to_queue_visual(link)
                             threading.Thread(target=self.download_worker, args=(link,), daemon=True).start()
            except: pass
        self.after(800, self.check_clipboard_loop)

    def download_worker(self, url):
        self.after(0, self.update_progress_state, True)
        self.log(f"🔥 Iniciado: {url}")
        
        # --- SELEÇÃO DE MOTOR COM CAMINHO SEGURO (APPDATA) ---
        if os.path.exists(self.local_engine_path):
            cmd = [self.local_engine_path, '-d', self.download_dir]
        else:
            cmd = ['gallery-dl', '-d', self.download_dir]

        if self.selected_browser.get() != "Nenhum (Padrão)":
             cmd.extend(['--cookies-from-browser', self.selected_browser.get()])
        cmd.append(url)

        try:
            creation = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creation)
            for line in proc.stdout:
                line = line.strip()
                if line and ("#" in line or "http" in line):
                    self.after(0, self.log, f"  [DL] {line}")
                    if "#" in line: self.after(0, self.increment_file_counter)
            proc.wait()
            
            if proc.returncode == 0: 
                self.after(0, self.log, "✅ Concluído")
                self.send_notification("ShurXit", f"Download finalizado:\n{url}")
            else:
                err = proc.stderr.read()
                self.after(0, self.log, f"⚠️ Erro: {err}")
        except Exception as e:
            self.after(0, self.log, f"❌ Erro Crítico: {e}")
        finally:
            self.after(0, self.update_progress_state, False)

if __name__ == "__main__":
    app = ShurXitApp()
    app.mainloop()