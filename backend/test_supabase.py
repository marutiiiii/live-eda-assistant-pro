# backend/test_supabase.py

from db import supabase

def main():
    # Just check we can talk to Supabase and read from analyses
    try:
        response = supabase.table("analyses").select("*").limit(1).execute()
        print("✅ Connection OK")
        print("Data:", response.data)
    except Exception as e:
        print("❌ Error talking to Supabase:", e)

if __name__ == "__main__":
    main()
