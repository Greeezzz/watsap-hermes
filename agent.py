import os
import sys
import time
import argparse
import requests
from supabase import create_client, Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()

DEFAULT_ROUTER_URL = "http://localhost:4000/v1/chat/completions"
DEFAULT_MODEL = "openhermes"

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Brainstorming CLI via Supabase & 9router")
    parser.add_argument("--name", required=True, help="Nama Agent (contoh: Noelle)")
    parser.add_argument("--owner", required=True, help="Nama Owner (contoh: Raken)")
    parser.add_argument("--room", default="usrc-main", help="ID Room Brainstorming")
    parser.add_argument("--url", default=os.getenv("SUPABASE_URL"), help="Supabase URL")
    parser.add_argument("--key", default=os.getenv("SUPABASE_KEY"), help="Supabase Anon Key")
    parser.add_argument("--router-url", default=os.getenv("ROUTER_URL", DEFAULT_ROUTER_URL), help="9router API Endpoint")
    parser.add_argument("--model", default=os.getenv("ROUTER_MODEL", DEFAULT_MODEL), help="Model ID di 9router")
    args = parser.parse_args()

    if not args.url or not args.key:
        console.print("[bold red]✦ Error: Supabase URL dan Key wajib diisi via argumen (--url & --key) atau Environment Variables (SUPABASE_URL & SUPABASE_KEY).[/]")
        sys.exit(1)

    supabase: Client = create_client(args.url, args.key)

    console.print(Panel.fit(
        f"[bold gold1]MULTI-AGENT BRAINSTORMING ROOM[/]\n"
        f"[cyan]Agent:[/] {args.name} (Owner: {args.owner})\n"
        f"[cyan]Room:[/] {args.room}\n"
        f"[cyan]Model Endpoint:[/] {args.router_url}",
        border_style="gold1"
    ))

    try:
        supabase.table("rooms").upsert({"room_id": args.room, "status": "active"}).execute()
    except Exception as e:
        console.print(f"[yellow]✦ Info room upsert: {e}[/]")

    def fetch_messages():
        try:
            res = supabase.table("messages").select("*").eq("room_id", args.room).order("created_at", desc=False).execute()
            return res.data or []
        except Exception:
            return []

    def send_message(content):
        try:
            supabase.table("messages").insert({
                "room_id": args.room,
                "agent_name": args.name,
                "owner": args.owner,
                "content": content
            }).execute()
        except Exception as e:
            console.print(f"[red]✦ Gagal mengirim pesan: {e}[/]")

    console.print(f"[green]✦ Terhubung ke room '{args.room}'. Menunggu diskusi...[/]")
    time.sleep(2)

    while True:
        messages = fetch_messages()
        
        table = Table(show_header=False, box=None, expand=True)
        table.add_column("Agent", style="bold", width=16)
        table.add_column("Content")

        for m in messages:
            agent = m.get("agent_name", "Unknown")
            owner = m.get("owner", "")
            content = m.get("content", "")
            color = "cyan" if agent == args.name else "magenta"
            table.add_row(f"[{color}]✦ {agent} ({owner})[/]", content)

        console.clear()
        console.print(Panel(table, title=f"[bold]Room: {args.room} (Tekan Ctrl+C untuk keluar)[/]", border_style="blue"))

        if not messages:
            console.print(f"\n[yellow]✦ Room masih kosong. Masukkan topik / pesan pembuka untuk memulai diskusi:[/]")
            topic = Prompt.ask("Topik Pembuka")
            if topic:
                send_message(f"MEMBUKA DISKUSI: {topic}")
            time.sleep(2)
            continue

        if messages:
            last_msg = messages[-1]
            last_agent = last_msg.get("agent_name")
            
            if last_agent != args.name and "[SELESAI]" not in last_msg.get("content", ""):
                console.print(f"\n[yellow]✦ Giliran {args.name} merespons via 9router...[/]")
                
                conversation_history = [{"role": "system", "content": f"Kamu adalah {args.name}, AI agent milik {args.owner} yang sedang berdiskusi otonom dengan agen lain. Berikan argumen yang tajam, bernas, dan singkat. Jika sudah sepakat, akhiri dengan [SELESAI]."}]
                for m in messages[-6:]:
                    role = "assistant" if m.get("agent_name") == args.name else "user"
                    conversation_history.append({"role": role, "content": f"{m.get('agent_name')}: {m.get('content')}"})

                try:
                    res = requests.post(args.router_url, json={
                        "model": args.model,
                        "messages": conversation_history,
                        "temperature": 0.7
                    }, timeout=60)

                    if res.status_code == 200:
                        data = res.json()
                        reply = data["choices"][0]["message"]["content"].strip()
                        send_message(reply)
                    else:
                        console.print(f"[red]✦ 9router Error {res.status_code}: {res.text}[/]")
                except Exception as e:
                    console.print(f"[red]✦ Gagal menghubungi 9router: {e}[/]")
                
                time.sleep(3)

        time.sleep(5)

if __name__ == "__main__":
    main()
