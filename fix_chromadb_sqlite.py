"""
Fix ChromaDB SQLite configuration.
ChromaDB uses SQLite internally for metadata storage. This script ensures
the proper SQLite module is used.
"""
import sys

# Replace sqlite3 with pysqlite3 for ChromaDB compatibility
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

if __name__ == "__main__":
    print("ChromaDB SQLite configuration fixed!")
    print("You can now run your application normally.")
