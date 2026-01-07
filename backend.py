import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import sqlite3
import re
import io

from database import (
    init_db, add_ceramic, get_all_ceramics, add_gudang, get_all_gudangs, 
    update_stock, get_stock_details, delete_ceramic, delete_gudang, 
    get_stock_by_ceramic_and_gudang, get_or_create_gudang, get_or_create_ceramic
)

# Initialize the database here since the backend is now managing it
init_db()

# Create the FastAPI app
app = FastAPI(
    title="API Stok Keramik",
    description="API untuk mengelola data stok keramik.",
    version="1.0.0",
)

# Configure CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
def read_root():
    """
    A welcome message to confirm the API is running.
    """
    return {"message": "Selamat Datang di API Stok Keramik"}


@app.get("/api/v1/stock")
def read_stock():
    """
    Get a detailed list of all ceramic stock across all warehouses.
    
    The structure of the response is a list of ceramic items. Each item includes:
    - id
    - nama (name)
    - total_stock
    - category
    - stock_per_gudang (a dictionary where keys are warehouse names and values are the stock quantity)
    """
    try:
        all_ceramics_data = get_stock_details()
        gudangs_data = get_all_gudangs() # Returns list of tuples (id, name)
        
        response_data = []
        
        for c_id, nama, total in all_ceramics_data:
            total_stock = total or 0
            stock_per_gudang = {}
            
            for gid, gname in gudangs_data:
                quantity = get_stock_by_ceramic_and_gudang(c_id, gid)
                stock_per_gudang[gname] = quantity or 0
            
            ceramic_item = {
                "id": c_id,
                "nama": nama,
                "total_stock": total_stock,
                "category": get_category_by_name(nama),
                "stock_per_gudang": stock_per_gudang
            }
            response_data.append(ceramic_item)
            
        return response_data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve stock data: {str(e)}")


@app.post("/api/v1/import-excel")
async def import_excel_api(file: UploadFile = File(...)):
    """
    Imports stock data from an Excel file.
    Resets stock in specified warehouses and then updates from the file.
    """
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format. Please upload an Excel file (.xlsx or .xls).")

    try:
        # Read the file content into a BytesIO object
        contents = await file.read()
        excel_file = io.BytesIO(contents)

        df = pd.read_excel(excel_file, header=0)

        if df.columns.empty or df.columns[0].lower() != 'item':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Excel format. First column (A1) must have header 'Item'.")

        item_col = df.columns[0]
        gudang_cols = [col for col in df.columns[1:] if not str(col).lower().startswith('unnamed')]

        if len(gudang_cols) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No warehouse columns found in the Excel file (starting from B1) or all warehouse columns are unnamed.")

        # --- Process Import ---
        # Get/create gudang IDs and reset stock in those gudangs
        gudang_ids = {name: get_or_create_gudang(name) for name in gudang_cols}
        
        conn = sqlite3.connect("stok_keramik.db")
        cursor = conn.cursor()
        try:
            for gid in gudang_ids.values():
                # Reset stock for the gudangs being imported
                cursor.execute("UPDATE stok SET quantity = 0 WHERE gudang_id = ?", (gid,))
            conn.commit()

            imported_count = 0
            processed_items = set()
            for index, row in df.iterrows():
                nama_keramik = row[item_col]
                if pd.isna(nama_keramik):
                    continue
                
                nama_keramik = str(nama_keramik).strip()
                if not nama_keramik:
                    continue
                
                normalized_name = normalize_ceramic_name(nama_keramik)
                ceramic_id = get_or_create_ceramic(normalized_name) # Ensure ceramic exists

                processed_items.add(normalized_name) # Use normalized name for counting unique items

                for gudang_nama in gudang_cols:
                    gudang_id = gudang_ids[gudang_nama]
                    
                    try:
                        quantity = 0
                        if gudang_nama in row and not pd.isna(row[gudang_nama]):
                            quantity = int(float(row[gudang_nama]))
                    except (ValueError, TypeError):
                        quantity = 0 # Default to 0 if conversion fails
                    
                    update_stock(ceramic_id, gudang_id, quantity) # Update stock in DB
                
                imported_count += 1
            
            return {
                "message": f"Successfully processed {len(processed_items)} unique ceramic items.",
                "details": f"Stock for warehouses: {', '.join(gudang_cols)} has been fully updated."
            }
        except Exception as db_exc:
            conn.rollback() # Rollback on any database error during import
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error during import: {str(db_exc)}")
        finally:
            conn.close()

    except HTTPException:
        raise # Re-raise HTTPExceptions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to import file: {str(e)}")

# This block allows running the script directly for development
if __name__ == "__main__":
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)