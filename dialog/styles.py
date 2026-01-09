# dialog/styles.py

BASE_STYLE = """
<style>
    body { 
        font-family: Segoe UI, sans-serif; 
        color: #333; 
        line-height: 1.6; 
    }
    h1 { 
        color: #C2185B; 
        border-bottom: 2px solid #eee; 
        padding-bottom: 10px; 
        margin-top: 0; 
    }
    h2 { 
        color: #1976D2; 
        margin-top: 25px; 
        margin-bottom: 10px; 
    }
    li { 
        margin-bottom: 8px; 
        font-size: 18px; 
    }
    p { 
        margin-bottom: 10px; 
    }
    
    /* Khung Code */
    pre { 
        background-color: #f5f5f5; 
        color: #2E7D32; 
        padding: 12px; 
        border: 1px solid #ddd; 
        border-radius: 4px; 
        font-family: Consolas, monospace;
        font-weight: bold;
        font-size: 18px;
    }
    
    /* Highlight từ khóa */
    .key { 
        font-weight: bold; 
        color: #E65100; 
        background-color: #fff3e0; 
        padding: 2px 5px; 
        border-radius: 3px; 
    }
    code { 
        background-color: #eee; 
        padding: 2px 4px; 
        border-radius: 3px; 
        font-family: Consolas; 
        color: #333; 
    }
</style>
"""

TABLE_STYLE = """
<style>
    body { font-family: Segoe UI, sans-serif; }
    
    /* Header Nhóm */
    h3 { 
        background-color: #e3f2fd; 
        color: #0d47a1; 
        padding: 10px; 
        border-radius: 4px; 
        border-left: 5px solid #1976D2;
        margin-top: 25px;
        margin-bottom: 10px;
        font-size: 18px;
    }
    
    table { 
        width: 100%; 
        border-collapse: collapse; 
        margin-bottom: 15px; 
        font-size: 18px; 
    }
    
    th { 
        text-align: left; 
        background-color: #1976D2; 
        color: white; 
        padding: 10px; 
        border: 1px solid #1976D2; 
    }
    
    td { 
        border: 1px solid #ddd; 
        padding: 8px 10px; 
        color: #333; 
        vertical-align: top; 
    }
    
    /* Zebra striping */
    tr:nth-child(even) { background-color: #f9f9f9; }
    tr:nth-child(odd) { background-color: #ffffff; }
    
    /* Cột lệnh */
    .cmd { 
        color: #d32f2f; 
        font-weight: bold; 
        font-family: Consolas, monospace; 
        white-space: nowrap;
    }
</style>
"""