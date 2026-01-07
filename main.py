import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import pandas as pd
import os
import sqlite3
import re
import requests # NEW: Import requests for API calls

# Keep database imports for now, as import_excel still uses them locally
from database import (
    init_db, add_ceramic, get_all_ceramics, add_gudang, get_all_gudangs, 
    update_stock, get_stock_details, delete_ceramic, delete_gudang, 
    get_stock_by_ceramic_and_gudang, get_or_create_gudang, get_or_create_ceramic
)

# NEW: API Base URL
API_BASE_URL = "http://127.0.0.1:8000" # Ensure your backend is running on this address

def normalize_ceramic_name(name):
    name = str(name).strip().upper()
    # Hapus suffix varian
    name = re.sub(r'\s*(KW1-B|KW2-B|KW1-N|KW1-G|KW-1|KW-2|KW1|KW2|I|II)$', '', name)
    # Ganti 'GR' atau 'GRIS' menjadi 'GRISS' jika di akhir nama
    name = re.sub(r'\s*(GR|GRIS)$', 'GRISS', name)
    # Hapus spasi berlebih
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def get_category_by_name(name):
    name_upper = str(name).strip().upper()
    if "PINGUL" in name_upper or "PINGULAN" in name_upper or "GRAMETINDO" in name_upper:
        return "PINGUL"
    if "LIST" in name_upper:
        return "LIST"
    if name_upper.startswith("AM ") or " AM " in name_upper or "LEMKRA" in name_upper:
        return "NAT"
    if any(k in name_upper for k in ["STEP", "STP", "STEPNOSING"]):
        return "STEPNOSING"
    if any(k in name_upper for k in [
        "KRAN", "STOP KRAN", "AUGUSTO", "BRACHIO", "GRAVINO", "VILANOVA",
        "EXCEL", "SOBAR", "DEVEN", "HALMAR", "EINER", "CLASSIC", "FLEX",
        "ISCO", "SAVITAR", "APOLLO", "WALLSHOWER", "SHOWER", "HANDSHOWER",
        "ALPHARD", "HAWAI", "GENTONG", "COUPLING", "UNION", "SELANG", "BCP",
        "PEMBERSIH", "SARGOT", "AVOR", "SARINGAN", "HANDLE", "BOSSINI",
        "SAPHIRA", "ENGSEL", "KUNCI", "BOLZANO", "GRENDEL", "LAMPU", "RH",
        "KAPSTOCK", "TISSUE", "KORDEN", "BAUT", "KAPSTK", "FIONI", "BATHUB",
        "KAPS", "RAK", "KACA", "PISAU", "GERGAJI", "PENGUIN", "PROFIL", "PELAMPUNG",
        "WATERHEAT", "WTRHEAT", "WATER HEATER", "WATER HEAT", "PELOR", "GIGI",
        "TOILET", "COOKER", "KOMPOR", "KITCHEN", "ANGZDOOR", "PKM",
        "BELLEZA", "COSTO", "DUPON", "FIDEM", "HAND SHOW", "BATH+SHOW", "K DIND",
        "K DOUBLE", "K SHOW", "K TAMAN", "K WAST", "PLANGSET", "PLST+T", "RING H",
        "SHOW BIDET", "SHW TNG", "STOP K", "SABUN", "TS CAIR", "WAST +KAB+KC",
        "HANSA", "MOVE", "OULUSOLID", "SPC", "TASIN", "TOTO", "TRILLIUN", "TRISENSA",
        "VAPELY", "MAGNET", "SPRINGKNEE", "WASSER", "CABINET",
        "GERMANY", "IGM", "MASPION", "MERIDIAN", "OULU", "SOLID", "TUTUP", "HAK ANGIN"
    ]):
        return "Sanitari"
    if any(k in name_upper for k in [
        "ARNA 60/60", "RMN", "CERANOSA", "RUDY", "GRD", "PASADENA", "SANDIMAS",
        "ALTHEA", "HELA", "IMPERIAL", "MAXNUM", "MELIUZ", "PAVIA", "REXTON",
        "A&F", "CERA TILES", "CYAN", "GOLFGRES", "SMART TILES", "AMADEO", "COVE",
        "GRANIT88", "GROSETO", "QIAOHUI", "ZED", "GRANITO", "NIRO", "DECOGRESS",
        "INDECOR", "INDOGRES", "GRANIT", "CAVALLO", "CIMETRIC", "PEGASUS",
        "WHTHORSE", "D-EURO", "TOPFRES", "IKAD", "SUNPWR", "CAVALI", "CITIGRES",
        "ROTA", "SCAFATI", "PLATINUM", "CENTRO",
        "A&Y", "DECOGRES 60X60", "GOLGRES", "PORTINO", "SPEEDO", "TOPGRES", "TOSCANA",
        "DECOGRES 60/60", "WHTHRSE"
    ]):
        return "Granit"
    if any(k in name_upper for k in [
        "ARWANA", "UNO", "ALLEGRA", "ATENA", "BATIRUS", "CAKRA", "COLOSSAL",
        "CONCORD", "DIVA", "ENIGMA", "GRAND", "HABITAT", "HECTOR", "IKAD",
        "INDOTILE", "KIA", "LAGUNA", "LUNA", "MULIA", "MARINO", "MUSTIKA",
        "PASCAL", "PASOLA", "PICASSO", "RAMIRO", "REDHORSE", "REDLINE",
        "SANTALIA", "TERRA", "UNICERA", "VALENCIA", "ZEUS",
        "ARW", "GEMILANG", "PCSO"
    ]):
        return "Keramik"
    return "Lainnya"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Aplikasi Stok Keramik")
        self.geometry("1000x600")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Stok Keramik", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.import_excel_button = ctk.CTkButton(self.sidebar_frame, text="Impor Excel", command=self.import_excel)
        self.import_excel_button.grid(row=1, column=0, padx=20, pady=10)

        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, rowspan=4, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.grid(row=1, column=0, padx=20, pady=(0,10), sticky="nsew")

        self.categories = ["Semua", "Granit", "Keramik", "Sanitari", "LIST", "PINGUL", "NAT", "STEPNOSING", "Lainnya"]

        self.treeviews = {}
        self.tab_frames = {}

        for category in self.categories:
            self.tab_view.add(category)
            tab_frame = ctk.CTkFrame(self.tab_view.tab(category), corner_radius=0)
            tab_frame.pack(expand=True, fill="both")
            tab_frame.grid_rowconfigure(0, weight=1)
            tab_frame.grid_columnconfigure(0, weight=1)
            self.tab_frames[category] = tab_frame

        self.bottom_frame = ctk.CTkFrame(self.main_frame)
        self.bottom_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.bottom_frame.grid_columnconfigure(1, weight=1)

        self.refresh_button = ctk.CTkButton(self.bottom_frame, text="Refresh", command=self.display_ceramics_stock)
        self.refresh_button.grid(row=0, column=0, padx=10, sticky="w")
        
        self.search_label = ctk.CTkLabel(self.bottom_frame, text="Search:")
        self.search_label.grid(row=0, column=2, padx=(20, 5), sticky="e")

        self.search_entry = ctk.CTkEntry(self.bottom_frame, placeholder_text="Cari di tab saat ini...")
        self.search_entry.grid(row=0, column=3, padx=(0, 20), sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        self.all_ceramics_data = [] # Will store raw data (list of dictionaries) from API
        self.categorized_data = {cat: [] for cat in self.categories}
        self.gudangs_data = [] # Will store (gname, gname) tuples derived from API response
        
        self.display_ceramics_stock()

    def display_ceramics_stock(self):
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/stock")
            response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx) 
            api_data = response.json()
            
            self.all_ceramics_data = [] # Reset to store API data
            
            # Extract gudang data from the first item, assuming all items have the same gudangs
            if api_data:
                first_item_gudangs = api_data[0]['stock_per_gudang']
                self.gudangs_data = [(gname, gname) for gname in first_item_gudangs.keys()]
            else:
                self.gudangs_data = []

            # Reset categorized data for new API response
            self.categorized_data = {cat: [] for cat in self.categories}

            for item in api_data:
                # Use existing categorization logic on item['nama']
                category = get_category_by_name(item['nama'])
                
                # If category is not in our tabs, default to Lainnya
                if category not in self.categorized_data:
                    category = "Lainnya"

                self.categorized_data[category].append(item) # Append full item dictionary
                self.categorized_data["Semua"].append(item)
                self.all_ceramics_data.append(item) # Keep raw data (dictionaries) for search
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Failed to connect to backend API: {e}\nPlease ensure the backend server is running at {API_BASE_URL}")
            self.all_ceramics_data = [] # Clear data on error
            self.gudangs_data = []
            self.categorized_data = {cat: [] for cat in self.categories}
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.all_ceramics_data = [] # Clear data on error
            self.gudangs_data = []
            self.categorized_data = {cat: [] for cat in self.categories}

        for category in self.categories:
            self._populate_treeview(self.tab_frames[category], category, self.categorized_data[category])
        
        # Clear search box and trigger a search to show all items in the current tab
        self.search_entry.delete(0, 'end')
        self._on_search(None) 

    def _populate_treeview(self, parent_frame, category_name, ceramics_data):
        for widget in parent_frame.winfo_children():
            widget.destroy()

        base_columns = ('id', 'nama', 'total') # Added 'id' as it's useful
        base_headings = ('ID', 'Nama Keramik', 'Total Stok') # Added 'ID'
        
        # Gudangs data is now derived from API response and is a list of (name, name) tuples
        gudang_columns = tuple(f'g_{gname}' for gid, gname in self.gudangs_data) # Use gname as key
        gudang_headings = tuple(gname for gid, gname in self.gudangs_data)

        columns = base_columns + gudang_columns
        headings = base_headings + gudang_headings

        tree = ttk.Treeview(parent_frame, columns=columns, show='headings', selectmode='browse')
        
        for col, head in zip(columns, headings):
            tree.heading(col, text=head)
            tree.column(col, anchor='center', width=120)
        
        tree.column('id', anchor='center', width=50) # Set column width for ID
        tree.column('nama', anchor='w', width=250)

        vsb = ttk.Scrollbar(parent_frame, orient='vertical', command=tree.yview)
        hsb = ttk.Scrollbar(parent_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.treeviews[category_name] = tree
        self._update_treeview_data(tree, ceramics_data)

    def _update_treeview_data(self, tree, ceramics_data):
        # Clear existing data
        for i in tree.get_children():
            tree.delete(i)
        
        # Insert new data
        # ceramics_data is now a list of dictionaries (API response format)
        for item in ceramics_data:
            values = [item['id'], item['nama'], item['total_stock']]
            for gid_placeholder, gname in self.gudangs_data: # Iterate through (gname, gname) tuples
                values.append(item['stock_per_gudang'].get(gname, 0)) # Get quantity by warehouse name
            
            tree.insert('', 'end', iid=item['id'], values=values)

    def _on_search(self, event):
        search_term = self.search_entry.get().lower()
        current_tab = self.tab_view.get()
        
        if not current_tab:
             return

        # self.categorized_data now stores dictionaries
        original_data = self.categorized_data[current_tab]

        if not search_term:
            filtered_data = original_data
        else:
            filtered_data = [
                item for item in original_data 
                if search_term in item['nama'].lower() # Access 'nama' key
            ]
        
        tree_to_update = self.treeviews.get(current_tab)
        if tree_to_update:
            self._update_treeview_data(tree_to_update, filtered_data)

    def import_excel(self):
        file_path = filedialog.askopenfilename(
            title="Pilih file Excel",
            filetypes=(("Excel Files", "*.xlsx"), ("All files", "*.*"))
        )
        if not file_path:
            return

        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                
                response = requests.post(f"{API_BASE_URL}/api/v1/import-excel", files=files)
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                
                api_response = response.json()
                
                if response.status_code == 200:
                    messagebox.showinfo("Impor Selesai", api_response.get("message", "Impor berhasil.") + "\n" + api_response.get("details", ""))
                    self.display_ceramics_stock() # Refresh data after successful import
                else:
                    messagebox.showerror("Error Impor", api_response.get("detail", "Terjadi kesalahan yang tidak diketahui saat mengimpor."))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Gagal terhubung ke backend API untuk impor Excel: {e}\nPastikan server backend berjalan pada {API_BASE_URL}")
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan saat memproses file Excel: {e}")


def main():
    # init_db() # REMOVED: Desktop app no longer initializes DB
    ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"

    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()