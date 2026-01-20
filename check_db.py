# import sqlite3
# try:
#     conn = sqlite3.connect('health.db')
#     cursor = conn.cursor()
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#     tables = cursor.fetchall()
#     print("Tables found:", [t[0] for t in tables])
    
#     # Check if pharmacy_inventory has columns
#     if 'pharmacy_inventory' in [t[0] for t in tables]:
#         cursor.execute("PRAGMA table_info(pharmacy_inventory)")
#         cols = cursor.fetchall()
#         print("Inventory Columns:", [c[1] for c in cols])
        
#     conn.close()
# except Exception as e:
#     print("Error:", e)
# # 

import sqlite3

try:
    conn = sqlite3.connect('health.db')
    cursor = conn.cursor()
    
    # 1. Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]
    print("Tables found:", table_names)
    
    # 2. Check if pharmacy_inventory exists and show columns
    if 'pharmacy_inventory' in table_names:
        cursor.execute("PRAGMA table_info(pharmacy_inventory)")
        cols = cursor.fetchall()
        print("Inventory Columns:", [c[1] for c in cols])
    else:
        print("Warning: 'pharmacy_inventory' table not found.")
        
    conn.close()

except Exception as e:
    print("Error:", e)