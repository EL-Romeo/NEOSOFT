import sqlite3

DATABASE_NAME = "stok_keramik.db"

def init_db():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Table for ceramics (keramik)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keramik (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL UNIQUE
        )
    """)

    # Table for gudangs (mitra/warehouses)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gudang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL UNIQUE
        )
    """)

    # Junction table for stock (stok) linking ceramics and gudangs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stok (
            ceramic_id INTEGER NOT NULL,
            gudang_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (ceramic_id, gudang_id),
            FOREIGN KEY (ceramic_id) REFERENCES keramik(id) ON DELETE CASCADE,
            FOREIGN KEY (gudang_id) REFERENCES gudang(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

def add_ceramic(nama):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO keramik (nama) VALUES (?)", (nama,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Keramik '{nama}' sudah ada.")
        return None
    finally:
        conn.close()

def get_all_ceramics():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama FROM keramik")
    ceramics = cursor.fetchall()
    conn.close()
    return ceramics

def add_gudang(nama_gudang):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO gudang (nama) VALUES (?)", (nama_gudang,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Gudang '{nama_gudang}' sudah ada.")
        return None
    finally:
        conn.close()

def get_all_gudangs():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama FROM gudang")
    gudangs = cursor.fetchall()
    conn.close()
    return gudangs

def update_stock(ceramic_id, gudang_id, quantity):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO stok (ceramic_id, gudang_id, quantity) VALUES (?, ?, ?) "
        "ON CONFLICT(ceramic_id, gudang_id) DO UPDATE SET quantity = excluded.quantity",
        (ceramic_id, gudang_id, quantity)
    )
    conn.commit()
    conn.close()



def get_stock_details():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            k.id,
            k.nama,
            COALESCE(SUM(s.quantity), 0) AS total_stok
        FROM
            keramik AS k
        LEFT JOIN
            stok AS s ON k.id = s.ceramic_id
        GROUP BY
            k.id, k.nama
        ORDER BY
            k.nama
    """)
    details = cursor.fetchall()
    conn.close()
    return details

def get_stock_by_ceramic_and_gudang(ceramic_id, gudang_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT quantity FROM stok WHERE ceramic_id = ? AND gudang_id = ?",
        (ceramic_id, gudang_id)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def delete_ceramic(ceramic_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keramik WHERE id = ?", (ceramic_id,))
    conn.commit()
    conn.close()

def delete_gudang(gudang_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gudang WHERE id = ?", (gudang_id,))
    conn.commit()
    conn.close()

def get_or_create_gudang(nama_gudang):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM gudang WHERE nama = ?", (nama_gudang,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0]
    else:
        cursor.execute("INSERT INTO gudang (nama) VALUES (?)", (nama_gudang,))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

def get_or_create_ceramic(nama):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM keramik WHERE nama = ?", (nama,))
    result = cursor.fetchone()
    if result:
        conn.close()
        return result[0]
    else:
        cursor.execute("INSERT INTO keramik (nama) VALUES (?)", (nama,))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")

    # Example Usage:
    # add_gudang("Gudang Pusat")
    # add_gudang("Gudang Cabang A")
    # 
    # add_ceramic("Keramik A", "30x30")
    # add_ceramic("Keramik B", "40x40")
    # 
    # ceramic_a_id = get_all_ceramics()[0][0]
    # gudang_pusat_id = get_all_gudangs()[0][0]
    # gudang_cabang_a_id = get_all_gudangs()[1][0]
    # 
    # update_stock(ceramic_a_id, gudang_pusat_id, 100)
    # update_stock(ceramic_a_id, gudang_cabang_a_id, 50)
    # 
    # print("\nStock Details:")
    # for detail in get_stock_details():
    #     print(detail)
