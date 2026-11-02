import os
import sys
import time
import requests
from datetime import datetime
from supabase import create_client, Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

console = Console()

class MultiAgentChat:
    def __init__(self):
        self.supabase = None
        self.agent_name = None
        self.room_id = None
        self.room_token = None
        self.router_url = None
        self.api_key = None
        self.model_name = None
        self.running = True
        
    def setup_credentials(self):
        """Interactive setup untuk koneksi Supabase dan konfigurasi agent"""
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]✦ MULTI-AGENT CHAT ROOM SETUP ✦[/]\n"
            "[italic]Sesuaikan credentials dan konfigurasi agent kamu[/]",
            border_style="cyan"
        ))
        
        # Supabase credentials
        supabase_url = Prompt.ask("[bold green]Supabase Project URL[/]", 
                                  default="https://oadhnihtdnjuviouifcu.supabase.co")
        supabase_key = Prompt.ask("[bold green]Supabase Anon Key[/]", 
                                  default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9hZGhuaWh0ZG5qdXZpb3VpZmN1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTM2MDI4OTAsImV4cCI6MjEwOTE3ODg5MH0.j3vqfCOVcO8vFouuu_JwmjgCKJujkpOGjMR_-kCD96I")
        
        # Initialize Supabase
        try:
            self.supabase = create_client(supabase_url, supabase_key)
            console.print("[green]✓ Supabase connected![/]")
        except Exception as e:
            console.print(f"[bold red]✦ Gagal terhubung ke Supabase: {e}[/]")
            sys.exit(1)
        
        time.sleep(1)
        
        # Agent name
        self.agent_name = Prompt.ask("[bold green]Nama Agent kamu[/]", default="Rover")
        
        # Room selection
        console.print("\n[bold cyan]✦ Pilihan Room:[/]")
        console.print("[1] Buat room baru")
        console.print("[2] Join room yang sudah ada")
        
        choice = Prompt.ask("[bold green]Pilihan[/]", choices=["1", "2"], default="2")
        
        if choice == "1":
            self._create_new_room()
        else:
            self._join_existing_room()
        
        # 9router configuration
        self.router_url = Prompt.ask("[bold green]9router Endpoint URL[/]", 
                                     default="http://localhost:20128/v1/chat/completions")
        self.api_key = Prompt.ask("[bold green]9router API Key (optional)[/]", default="")
        self.model_name = Prompt.ask("[bold green]Model ID[/]", default="openhermes")
    
    def _create_new_room(self):
        """Create a new room dengan token random"""
        import uuid
        room_id = str(uuid.uuid4())[:12]
        room_token = str(uuid.uuid4())
        
        try:
            self.supabase.table("rooms").insert({
                "id": room_id,
                "token": room_token
            }).execute()
            
            self.room_id = room_id
            self.room_token = room_token
            
            console.print(f"\n[bold green]✦ Room berhasil dibuat![/]")
            console.print(f"[cyan]Room ID    : {room_id}[/]")
            console.print(f"[cyan]Room Token : {room_token}[/]")
            console.print("[italic yellow]Bagikan token ini ke agent lain buat join ke room ini![/]")
            time.sleep(3)
        except Exception as e:
            console.print(f"[red]✦ Gagal membuat room: {e}[/]")
            sys.exit(1)
    
    def _join_existing_room(self):
        """Join ke room yang sudah ada pakai token"""
        room_token = Prompt.ask("[bold green]Room Token[/]")
        
        try:
            result = self.supabase.table("rooms").select("*").eq("token", room_token).execute()
            
            if result.data and len(result.data) > 0:
                self.room_id = result.data[0]["id"]
                self.room_token = room_token
                console.print(f"\n[bold green]✓ Berhasil join ke room {self.room_id}![/]")
                time.sleep(2)
            else:
                console.print("[red]✦ Room token tidak ditemukan![/]")
                sys.exit(1)
        except Exception as e:
            console.print(f"[red]✦ Gagal join room: {e}[/]")
            sys.exit(1)
    
    def fetch_messages(self, limit=15):
        """Fetch messages terbaru dari room"""
        try:
            result = self.supabase.table("messages").select("*").eq("room_id", self.room_id).order("created_at", desc=False).limit(limit).execute()
            return result.data or []
        except Exception:
            return []
    
    def send_message(self, content):
        """Send message ke room"""
        try:
            self.supabase.table("messages").insert({
                "room_id": self.room_id,
                "sender": self.agent_name,
                "content": content,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            console.print(f"[red]✦ Gagal mengirim pesan: {e}[/]")
    
    def display_room(self, messages):
        """Display room dengan formatted messages"""
        console.clear()
        
        table = Table(show_header=False, box=None, expand=True, padding=(0, 1))
        table.add_column("Sender", style="bold", width=18)
        table.add_column("Content")
        
        for m in messages:
            sender = m.get("sender", "Unknown")
            content = m.get("content", "")
            color = "cyan" if sender == self.agent_name else "magenta"
            
            if "MEMBUKA DISKUSI" in content:
                table.add_row(f"[bold yellow]✦ {sender}[/]", f"[yellow italic]{content}[/]")
            else:
                table.add_row(f"[{color}]✦ {sender}[/]", content)
        
        console.print(Panel(
            table, 
            title=f"[bold gold1]✦ ROOM: {self.room_id} | AGENT: {self.agent_name} ✦[/]",
            border_style="cyan"
        ))
    
    def get_agent_response(self, messages):
        """Get AI response dari 9router berdasarkan context pesan"""
        try:
            conversation_history = [
                {
                    "role": "system",
                    "content": f"Kamu adalah {self.agent_name}, AI agent yang sedang berdiskusi otomatis dengan agen lain. Berikan argumen yang tajam, bernas, berbobot secara teknis, dan singkat. Jika sudah mencapai konsensus, akhiri dengan [SELESAI]."
                }
            ]
            
            for m in messages[-10:]:
                role = "assistant" if m.get("sender") == self.agent_name else "user"
                conversation_history.append({
                    "role": role,
                    "content": f"{m.get('sender')}: {m.get('content')}"
                })
            
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = requests.post(
                self.router_url,
                json={
                    "model": self.model_name,
                    "messages": conversation_history,
                    "temperature": 0.7
                },
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                console.print(f"[red]✦ 9router Error {response.status_code}[/]")
                return None
        except Exception as e:
            console.print(f"[red]✦ Error getting agent response: {e}[/]")
            return None
    
    def should_respond(self, messages):
        """Logic untuk determine apakah agent harus merespons"""
        if not messages:
            return False
        
        last_msg = messages[-1]
        last_sender = last_msg.get("sender")
        last_content = last_msg.get("content", "")
        
        if "[SELESAI]" in last_content:
            return False
        
        if last_sender != self.agent_name:
            return True
        
        if f"@{self.agent_name}" in last_content or last_content.startswith(f"{self.agent_name}:"):
            return True
        
        return False
    
    def run(self):
        """Main loop agent"""
        console.clear()
        console.print(f"[bold green]✦ {self.agent_name} siap di room {self.room_id}![/]")
        console.print("[italic]Tekan Ctrl+C untuk keluar[/]")
        time.sleep(2)
        
        try:
            while self.running:
                messages = self.fetch_messages(limit=20)
                self.display_room(messages)
                
                if not messages:
                    console.print(f"\n[bold yellow]✦ Room kosong. Masukkan topik pembuka untuk memulai diskusi:[/]")
                    topic = Prompt.ask("[bold cyan]Topik Pembuka[/]")
                    if topic:
                        self.send_message(f"MEMBUKA DISKUSI: {topic}")
                    time.sleep(2)
                    continue
                
                last_content = messages[-1].get("content", "")
                if "[SELESAI]" in last_content:
                    console.print("\n[bold green]✓ Konsensus tercapai! Diskusi selesai.[/]")
                    time.sleep(2)
                    break
                
                if self.should_respond(messages):
                    last_sender = messages[-1].get("sender")
                    console.print(f"\n[bold yellow]✦ Menyimak argumen {last_sender}, {self.agent_name} sedang merumuskan tanggapan...[/]")
                    
                    response = self.get_agent_response(messages)
                    if response:
                        self.send_message(response)
                        console.print(f"[green]✓ Pesan dikirim![/]")
                    
                    time.sleep(2)
                
                time.sleep(3)
        
        except KeyboardInterrupt:
            console.print("\n[bold yellow]✦ Keluar dari room. Sampai jumpa![/]")
            self.running = False
        except Exception as e:
            console.print(f"[red]✦ Error: {e}[/]")
            self.running = False

def main():
    chat = MultiAgentChat()
    chat.setup_credentials()
    chat.run()

if __name__ == "__main__":
    main()
