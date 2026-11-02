import os
import sys
import time
import requests
from supabase import create_client, Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()

def clear_screen():
    console.clear()

def main():
    clear_screen()
    
    console.print(Panel.fit(
        "[bold cyan]✦ USRC MULTI-AGENT BRAINSTORMING CLI ✦[/]\n"
        "[italic]Kolaborasi Otonom AI Agent via Supabase & 9router[/]",
        border_style="cyan"
    ))

    # Input interaktif
    agent_name = Prompt.ask("[bold green]Nama Agent kamu[/]", default="Noelle")
    owner_name = Prompt.ask("[bold green]Nama Owner / Pemilik[/]", default="Raken")
    room_id = Prompt.ask("[bold green]Nama Room / Topik Sesi[/]", default="usrc-brainstorm")
    router_url = Prompt.ask("[bold green]9router Endpoint URL[/]", default="http://localhost:20128/v1/chat/completions")
    api_key = Prompt.ask("[bold green]9router API Key (kosongkan jika tidak ada)[/]", default="")
    model_name = Prompt.ask("[bold green]Model ID / Nama Model[/]", default="openhermes")
    
    # Ambil dari environment variables atau minta input jika kosong
    default_sup_url = os.getenv("SUPABASE_URL", "")
    default_sup_key = os.getenv("SUPABASE_KEY", "")

    supabase_url = Prompt.ask("[bold green]Supabase Project URL[/]", default=default_sup_url)
    supabase_key = Prompt.ask("[bold green]Supabase Anon Key[/]", default=default_sup_key, password=True)

    if not supabase_url or not supabase_key:
        console.print("[bold red]✦ Error: Supabase URL dan Anon Key wajib diisi![/]")
        sys.exit(1)

    try:
        supabase: Client = create_client(supabase_url, supabase_key)
    except Exception as e:
        console.print(f"[bold red]✦ Gagal terhubung ke Supabase: {e}[/]")
        sys.exit(1)

    clear_screen()
    console.print(f"[bold green]✦ Berhasil terhubung! Masuk ke room '{room_id}' sebagai {agent_name} ({owner_name})...[/]")
    time.sleep(1.5)

    try:
        supabase.table("rooms").upsert({"room_id": room_id, "status": "active"}).execute()
    except Exception:
        pass

    def fetch_messages():
        try:
            res = supabase.table("messages").select("*").eq("room_id", room_id).order("created_at", desc=False).execute()
            return res.data or []
        except Exception:
            return []

    def send_message(content):
        try:
            supabase.table("messages").insert({
                "room_id": room_id,
                "agent_name": agent_name,
                "owner": owner_name,
                "content": content
            }).execute()
        except Exception as e:
            console.print(f"[red]✦ Gagal mengirim pesan ke Supabase: {e}[/]")

    while True:
        messages = fetch_messages()
        
        table = Table(show_header=False, box=None, expand=True, padding=(0, 1))
        table.add_column("Agent", style="bold", width=22)
        table.add_column("Content")

        for m in messages:
            ag = m.get("agent_name", "Unknown")
            ow = m.get("owner", "")
            txt = m.get("content", "")
            color = "cyan" if ag == agent_name else "magenta"
            
            if "MEMBUKA DISKUSI" in txt:
                table.add_row(f"[bold yellow]✦ {ag} ({ow})[/]", f"[yellow italic]{txt}[/]")
            else:
                table.add_row(f"[{color}]✦ {ag} ({ow})[/]", txt)

        clear_screen()
        console.print(Panel(table, title=f"[bold gold1]✦ ROOM: {room_id} | AGENT: {agent_name} (Tekan Ctrl+C untuk keluar) ✦[/]", border_style="cyan"))

        if not messages:
            console.print(f"\n[bold yellow]✦ Room masih kosong. Masukkan topik atau pertanyaan pembuka untuk memulai brainstorming:[/]")
            topic = Prompt.ask("[bold cyan]Topik Pembuka[/]")
            if topic:
                send_message(f"MEMBUKA DISKUSI: {topic}")
            time.sleep(2)
            continue

        if messages:
            last_msg = messages[-1]
            last_agent = last_msg.get("agent_name")
            last_content = last_msg.get("content", "")
            
            if "[SELESAI]" in last_content:
                console.print("\n[bold green]✦ Konsensus telah tercapai! Diskusi selesai.[/]")
                break

            if last_agent != agent_name:
                console.print(f"\n[bold yellow]✦ Menyimak argumen {last_agent}, {agent_name} sedang merumuskan tanggapan...[/]")
                
                conversation_history = [
                    {
                        "role": "system",
                        "content": f"Kamu adalah {agent_name}, AI agent milik {owner_name} yang sedang berdiskusi otonom dengan agen lain dalam tim USRC. Berikan argumen yang tajam, bernas, berbobot secara teknis, dan singkat. Jangan berputar-putar. Jika solusi atau kesepakatan bersama sudah tercapai, akhiri tanggapanmu dengan kata [SELESAI]."
                    }
                ]
                
                for m in messages[-8:]:
                    role = "assistant" if m.get("agent_name") == agent_name else "user"
                    conversation_history.append({"role": role, "content": f"{m.get('agent_name')}: {m.get('content')}"})

                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"

                try:
                    res = requests.post(router_url, json={
                        "model": model_name,
                        "messages": conversation_history,
                        "temperature": 0.7
                    }, headers=headers, timeout=60)

                    if res.status_code == 200:
                        data = res.json()
                        reply = data["choices"][0]["message"]["content"].strip()
                        send_message(reply)
                    else:
                        console.print(f"[red]✦ 9router Error {res.status_code}: {res.text}[/]")
                        time.sleep(5)
                except Exception as e:
                    console.print(f"[red]✦ Gagal menghubungi 9router: {e}[/]")
                    time.sleep(5)
                
                time.sleep(2)

        time.sleep(3)

if __name__ == "__main__":
    main()
