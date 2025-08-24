from browser_cookie3 import chromium as chrome
from utils.api import Api
from random import choice, uniform
from threading import Thread, active_count
from time import sleep
import json
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich import print as rprint
from rich.text import Text
from rich.table import Table
from rich.live import Live

console = Console()

class TikReport:
    def __init__(this, cookies: dict):
        this.cookies = cookies
        this.userInfo = None
        this.selfInfo = None
        # Mapping reason codes to human-readable descriptions
        this.reasons = {
            '9101': 'Inappropriate Content',
            '91011': 'Harassment or Bullying',
            '9009': 'Hate Speech',
            '90093': 'Misinformation',
            '90097': 'Illegal Activities',
            '90095': 'Violent Content',
            '90064': 'Dangerous Acts',
            '90061': 'Self-Harm',
            '90063': 'Animal Cruelty',
            '9006': 'Spam',
            '9008': 'Intellectual Property Violation',
            '1001': 'Sexual Content',
            '1002': 'Impersonation',
            '1003': 'Personal Information',
            '1004': 'Minor Safety'
        }

    def reportAccount(self):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            total_reasons = len(self.reasons)
            task = progress.add_task("[cyan]Reporting account...", total=total_reasons)
            
            for reason_code, reason_desc in self.reasons.items():
                sleep(uniform(1.5, 3.0))
                
                params = {
                    'secUid'         : self.userInfo['userInfo']['user']['secUid'],
                    'nickname'       : self.userInfo['userInfo']['user']['nickname'],
                    'object_id'      : self.userInfo['userInfo']['user']['id'],
                    'owner_id'       : self.userInfo['userInfo']['user']['id'],
                    'target'         : self.userInfo['userInfo']['user']['id'],
                    'reporter_id'    : self.selfInfo['data']['user_id'],
                    'reason'         : reason_code,
                    'report_type'    : 'user',
                    'report_channel' : 'copy_link',
                    'from_page'      : 'user',
                    'lang'           : 'en'
                }

                try:
                    progress.update(task, description=f"[cyan]Reporting for: [white]{reason_desc}")
                    req = Api(cookies=self.cookies).tiktok_request('aweme/v2/aweme/feedback/', extra_params=params)
                    
                    if req.status_code == 403:
                        console.print(Panel.fit(
                            f"[yellow]Rate limited for reason: {reason_desc}\nWaiting 30 seconds...",
                            title="Rate Limit",
                            border_style="yellow"
                        ))
                        sleep(30)
                        continue
                    
                    if req.status_code != 200:
                        console.print(Panel.fit(
                            f"[yellow]Warning: Got status code {req.status_code} for reason: {reason_desc}",
                            title="Warning",
                            border_style="yellow"
                        ))
                        continue
                        
                    if not req.text:
                        console.print(Panel.fit(
                            f"[yellow]Warning: Empty response for reason: {reason_desc}",
                            title="Warning",
                            border_style="yellow"
                        ))
                        continue
                    
                    response_json = req.json()
                    if response_json.get('status_code', 0) == 0:
                        console.print(f"[green]✓[/green] Successfully reported - {reason_desc}")
                    else:
                        console.print(f"[red]✗[/red] Failed to report - {reason_desc} - {response_json.get('status_msg', 'Unknown error')}")
                    
                except Exception as e:
                    console.print(Panel.fit(
                        f"[red]Error reporting with reason {reason_desc}:\n{str(e)}",
                        title="Error",
                        border_style="red"
                    ))
                    sleep(5)
                
                progress.advance(task)

    def reportVideo(self, videoId: str):
        sleep(uniform(2.0, 4.0))
        
        try:
            if not self.userInfo or not self.selfInfo:
                console.print(Panel.fit(
                    f"[red]Error: Missing user info or self info for video {videoId}",
                    title="Error",
                    border_style="red"
                ))
                return
                
            # Select a random reason code and its description
            reason_code = choice(list(self.reasons.keys()))
            reason_desc = self.reasons[reason_code]
                
            params = {
                'nickname'          : self.userInfo['userInfo']['user']['nickname'],
                'object_id'         : videoId,
                'object_owner_id'   : self.userInfo['userInfo']['user']['id'],
                'owner_id'          : self.userInfo['userInfo']['user']['id'],
                'reason'            : reason_code,
                'report_type'       : 'video',
                'reporter_id'       : self.selfInfo['data']['user_id'],
                'target'            : videoId,
                'video_id'          : videoId,
                'video_owner'       : self.userInfo['userInfo']['user']['id']
            }
            
            with console.status(f"[cyan]Reporting video {videoId}..."):
                req = Api(cookies=self.cookies).tiktok_request('aweme/v2/aweme/feedback/', extra_params=params)
                response = req.json()
                console.print(f"[green]✓[/green] Reported video {videoId} - Reason: {reason_desc}")
            
        except Exception as e:
            console.print(Panel.fit(
                f"[red]Error reporting video {videoId}:\n{str(e)}",
                title="Error",
                border_style="red"
            ))

    def start(self, username: str):
        # Create welcome banner
        console.print(Panel.fit(
            "[cyan]TikTok Report Bot[/cyan]\n[white]Starting report process...",
            title="Welcome",
            border_style="cyan"
        ))

        # Initialize with spinner
        with console.status("[cyan]Fetching user information...") as status:
            try:
                self.userInfo = Api(cookies=self.cookies).user_info(username).json()
                status.update("[cyan]Fetching account information...")
                self.selfInfo = Api(cookies=self.cookies).account_info().json()
            except Exception as e:
                console.print(Panel.fit(
                    f"[red]Error initializing:\n{str(e)}",
                    title="Error",
                    border_style="red"
                ))
                return

        # Verify user info
        if 'userInfo' not in self.userInfo or 'user' not in self.userInfo.get('userInfo', {}):
            console.print(Panel.fit(
                f"[red]Could not find user info for {username}.\nThe user might not exist or the response format has changed.",
                title="Error",
                border_style="red"
            ))
            return

        # Show user info
        user = self.userInfo['userInfo']['user']
        stats = self.userInfo['userInfo'].get('stats', {})
        user_table = Table(show_header=True, header_style="cyan")
        user_table.add_column("Field")
        user_table.add_column("Value")
        user_table.add_row("Username", user['nickname'])
        user_table.add_row("User ID", user['id'])
        user_table.add_row("Followers", str(stats.get('followerCount', 'N/A')))
        user_table.add_row("Following", str(stats.get('followingCount', 'N/A')))
        user_table.add_row("Hearts", str(stats.get('heartCount', 'N/A')))
        user_table.add_row("Videos", str(stats.get('videoCount', 'N/A')))

        console.print(Panel(user_table, title="User Information", border_style="cyan"))
        
        # Ask for confirmation
        if questionary.confirm("Do you want to proceed with reporting?").ask():
            self.reportAccount()
        else:
            console.print("[yellow]Operation cancelled by user.[/yellow]")

def main():
    console.clear()
    # Create title
    title = Text()
    title.append("TikTok ", style="cyan bold")
    title.append("Report ", style="white bold")
    title.append("Bot", style="red bold")
    
    console.print(Panel.fit(
        title,
        subtitle="[cyan italic]By xtekky[/cyan italic]",
        border_style="cyan"
    ))

    # Main menu
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Report a User",
                "Report User's Videos",
                "Exit"
            ]).ask()

        if choice == "Exit":
            console.print(Panel.fit(
                "[yellow]Thank you for using TikTok Report Bot![/yellow]",
                border_style="yellow"
            ))
            break

        try:
            # Get cookies
            with console.status("[cyan]Getting browser cookies..."): 
                cookies = {c.name: c.value for c in chrome(domain_name='tiktok.com')}

            # Get username
            username = questionary.text("Enter the TikTok username:").ask()
            
            if choice == "Report a User":
                bot = TikReport(cookies)
                bot.start(username)
            
            elif choice == "Report User's Videos":
                with console.status("[cyan]Fetching user information...") as status:
                    userInfo = Api(cookies=cookies).user_info(username).json()
                    
                    if not userInfo or 'userInfo' not in userInfo or 'user' not in userInfo['userInfo']:
                        console.print(Panel.fit(
                            f"[red]Could not fetch user info for {username}",
                            title="Error",
                            border_style="red"
                        ))
                        continue

                    secUid = userInfo['userInfo']['user']['secUid']
                    hasMore = True
                    cursor = "0"
                    bot = TikReport(cookies)
                    
                    # Initialize the bot with user info first
                    bot = TikReport(cookies)
                    bot.userInfo = userInfo  # Set the user info
                    bot.selfInfo = Api(cookies=cookies).account_info().json()  # Get self info
                    
                    if not bot.selfInfo:
                        console.print(Panel.fit(
                            "[red]Could not fetch account information. Please try again.",
                            title="Error",
                            border_style="red"
                        ))
                        continue

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    ) as progress:
                        videos_processed = 0
                        while hasMore:
                            try:
                                videos = Api(cookies=cookies).user_videos(secUid, 33, cursor).json()
                                
                                if 'itemList' not in videos or not videos['itemList']:
                                    hasMore = False
                                    continue
                                
                                total_videos = len(videos['itemList'])
                                report_task = progress.add_task(
                                    f"[cyan]Reporting videos... Batch {videos_processed + 1}",
                                    total=total_videos
                                )
                                
                                for idx, video in enumerate(videos['itemList']):
                                    try:
                                        bot.reportVideo(video['id'])
                                        progress.update(report_task, advance=1)
                                        videos_processed += 1
                                        sleep(uniform(1.5, 3.0))  # Random delay between reports
                                    except Exception as e:
                                        console.print(Panel.fit(
                                            f"[yellow]Warning: Failed to report video {video['id']}\n{str(e)}",
                                            title="Warning",
                                            border_style="yellow"
                                        ))
                                
                                hasMore = videos.get('hasMore', False)
                                cursor = videos.get('cursor', "0")
                                
                                # Show batch completion message
                                console.print(f"[green]✓[/green] Completed batch of {total_videos} videos")
                                sleep(2)  # Short delay between batches
                                
                            except Exception as e:
                                console.print(Panel.fit(
                                    f"[red]Error fetching videos:\n{str(e)}",
                                    title="Error",
                                    border_style="red"
                                ))
                                hasMore = False
                        
                        # Show final completion message
                        console.print(Panel.fit(
                            f"[green]Successfully processed {videos_processed} videos!",
                            title="Complete",
                            border_style="green"
                        ))
                        
                    console.print("[green]✓[/green] Finished reporting videos!")

        except Exception as e:
            console.print(Panel.fit(
                f"[red]An error occurred:\n{str(e)}",
                title="Error",
                border_style="red"
            ))

        if not questionary.confirm("Would you like to perform another action?").ask():
            console.print(Panel.fit(
                "[yellow]Thank you for using TikTok Report Bot![/yellow]",
                border_style="yellow"
            ))
            break

if __name__ == '__main__':
    main()
