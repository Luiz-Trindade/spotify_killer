import yt_dlp
from concurrent.futures import ThreadPoolExecutor as Pool
import os
from datetime import datetime

from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.table import Table
from rich.columns import Columns
from rich.theme import Theme
from rich.text import Text
from InquirerPy import inquirer

# Custom theme
custom_theme = Theme(
    {
        "info": "cyan",
        "success": "bold green",
        "warning": "yellow",
        "error": "bold red",
    }
)

console = Console(theme=custom_theme)


def show_banner():
    header = Text("SPOTIFY KILLER", style="bold #1DB954", justify="center")
    tagline = Text(
        "🎵 Download media from anywhere 💿", style="italic #B3B3B3", justify="center"
    )

    features = Columns(
        [
            Text("🎬 Videos", style="cyan"),
            Text("🎵 Audio", style="magenta"),
            Text("📋 Playlists", style="yellow"),
        ],
        align="center",
        expand=True,
    )

    # Group combines multiple renderables
    content = Group(header, tagline, Text(""), features)

    panel = Panel(
        content,
        border_style="bold #1DB954",
        padding=(1, 4),
        expand=False,
    )
    console.print(panel)


def get_output_dir(media_type):
    today = datetime.now().strftime("%d.%m.%Y")
    output_path = os.path.join("output", media_type, today)
    os.makedirs(output_path, exist_ok=True)
    return output_path


def get_options(media_type):
    output_dir = get_output_dir(media_type)
    options = {
        "video": {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
        },
        "audio": {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
        },
    }
    return options[media_type]


def extract_links(url):
    ydl_opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            return [v["url"] for v in info["entries"]]
        return [info["webpage_url"]]


def download_video(url):
    with yt_dlp.YoutubeDL(get_options("video")) as ydl:
        ydl.download([url])


def download_audio(url):
    with yt_dlp.YoutubeDL(get_options("audio")) as ydl:
        ydl.download([url])


def show_summary(media_type, total, output_dir):
    table = Table(title="Download Summary", border_style="green")
    table.add_column("Type", style="cyan", justify="center")
    table.add_column("Quantity", style="yellow", justify="center")
    table.add_column("Directory", style="magenta")

    table.add_row(media_type.upper(), str(total), output_dir)
    console.print(table)


def main():
    show_banner()

    url = console.input("[bold cyan]🔗 Enter URL: [/bold cyan]").strip()
    if not url:
        console.print("[error]❌ Empty URL. Exiting.[/error]")
        return

    with console.status(
        "[bold yellow]🔍 Extracting links...[/bold yellow]", spinner="dots"
    ):
        try:
            urls = extract_links(url)
        except Exception as e:
            console.print(f"[error]❌ Error extracting links: {e}[/error]")
            return

    console.print(f"[success]✅ {len(urls)} link(s) found[/success]\n")

    download_options = inquirer.select(
        message="📥 Download type:",
        choices=["video", "audio"],
        default="video",
    ).execute()

    download_fn = download_audio if download_options == "audio" else download_video

    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"[cyan]Downloading {download_options}...",
            total=len(urls),
        )
        with Pool(max_workers=len(urls)) as pool:
            for _ in pool.map(download_fn, urls):
                progress.advance(task)

    console.print()
    output_dir = get_output_dir(download_options)
    show_summary(download_options, len(urls), output_dir)
    console.print("\n[success]🎉 Download completed successfully![/success]")


if __name__ == "__main__":
    main()
