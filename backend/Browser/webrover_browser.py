# webrover_browser.py
import asyncio
import platform
from pathlib import Path
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import re
import os
import aiohttp
import socket
import subprocess
import psutil
import time

class WebRoverBrowser:
    def __init__(self, 
                 user_data_dir: Optional[str] = None,
                 headless: bool = False,
                 proxy: Optional[str] = None):
        base_dir = self._default_user_dir()
        # Initially just store the base Chrome directory
        self.base_user_dir = base_dir
        # Will be set after profile selection
        self.user_data_dir = None
        self.headless = headless
        self.proxy = proxy
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None
        self.chrome_process = None

    def _default_user_dir(self) -> str:
        """Get platform-specific default user data directory"""
        system = platform.system()
        if system == "Windows":
            return str(Path.home() / "AppData/Local/Google/Chrome/User Data")
        elif system == "Darwin":
            return str(Path.home() / "Library/Application Support/Google/Chrome")
        else:  # Linux
            return str(Path.home() / ".config/google-chrome")

    def _find_chrome_executable(self) -> str:
        """Find Chrome executable on the system"""
        system = platform.system()
        
        if system == "Windows":
            # Common Chrome installation paths on Windows
            possible_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                str(Path.home() / "AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
                "C:\\Users\\Public\\Desktop\\Google Chrome.lnk"  # Sometimes it's a shortcut
            ]
            
            for path in possible_paths:
                if os.path.exists(path) and path.endswith('.exe'):
                    return path
                    
        elif system == "Darwin":
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        else:  # Linux
            # Try common Linux paths
            possible_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable", 
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        
        raise RuntimeError(f"Chrome executable not found on {system}")

    def _kill_existing_chrome_processes(self):
        """Kill any existing Chrome processes that might be using the debug port"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and any('--remote-debugging-port=9222' in arg for arg in cmdline):
                            print(f"Killing existing Chrome process with PID {proc.info['pid']}")
                            proc.kill()
                            proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            print(f"Warning: Could not kill existing Chrome processes: {e}")

    def _is_port_available(self, port: int = 9222) -> bool:
        """Check if the debug port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                return result != 0  # Port is available if connection fails
        except Exception:
            return True

    async def connect_to_chrome(self, 
                              timeout: float = 30,
                              retries: int = 3) -> Tuple[Browser, BrowserContext]:
        """Connect to existing Chrome instance with retry logic"""
        self._playwright = await async_playwright().start()
        
        # Kill any existing Chrome processes using the debug port
        self._kill_existing_chrome_processes()
        
        # Wait a bit for processes to fully terminate
        await asyncio.sleep(2)
        
        print("Starting Chrome with remote debugging...")
        chrome_process = await self.launch_chrome_with_remote_debugging()
        
        # Wait longer for Chrome to start
        await asyncio.sleep(5)
        
        print("Attempting to connect to Chrome...")
        for attempt in range(retries):
            try:
                # Get the WebSocket endpoint from Chrome's debugging API
                ws_endpoint = None
                print("Getting browser websocket URL")
                
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get("http://127.0.0.1:9222/json/version", timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                ws_endpoint = data.get('webSocketDebuggerUrl')
                            else:
                                raise aiohttp.ClientError(f"HTTP {response.status}")
                    except Exception as e:
                        print(f"Failed to get WebSocket endpoint: {e}")
                        raise
                
                if not ws_endpoint:
                    raise RuntimeError("Could not get WebSocket debugger URL")
                
                print(f"Connecting to WebSocket endpoint: {ws_endpoint}")
                self._browser = await self._playwright.chromium.connect_over_cdp(
                    ws_endpoint
                )

                print("Connected to browser:", self._browser)
                
                # Use the first available context instead of creating a new one
                contexts = self._browser.contexts
                if not contexts:
                    raise RuntimeError("No browser contexts available after connection")
                self._context = contexts[0]
                print("Context: ", self._context)
                
                print("Successfully connected to Chrome")
                return self._browser, self._context
            
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt == retries - 1:
                    # If all attempts failed, try to restart Chrome
                    if chrome_process and chrome_process.returncode is None:
                        chrome_process.terminate()
                        try:
                            await asyncio.wait_for(chrome_process.wait(), timeout=5)
                        except asyncio.TimeoutError:
                            chrome_process.kill()
                    
                    raise RuntimeError(f"Failed to connect to Chrome after {retries} attempts: {str(e)}")
                
                # Wait before retrying
                await asyncio.sleep(3)

    async def launch_chrome_with_remote_debugging(self):
        """Launch Chrome with remote debugging port"""
        chrome_path = self._find_chrome_executable()
        
        if not os.path.exists(chrome_path):
            raise RuntimeError(f"Chrome executable not found at {chrome_path}")

        # Create a temporary user data directory to avoid conflicts
        temp_user_data = Path.cwd() / "temp_chrome_data"
        temp_user_data.mkdir(exist_ok=True)

        cmd = [
            chrome_path,
            f"--remote-debugging-port=9222",
            f"--user-data-dir={temp_user_data}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-web-security",  # Sometimes helps with connectivity
            "--disable-features=VizDisplayCompositor",  # Can help with headless mode
            "--start-maximized",
        ]

        if self.headless:
            cmd.extend(["--headless=new", "--disable-gpu"])

        # Windows-specific flags
        if platform.system() == "Windows":
            cmd.extend([
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ])

        try:
            print("Launching Chrome with command:", " ".join(cmd))
            
            # Use subprocess.Popen for better control on Windows
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
                # Convert to asyncio process-like object
                self.chrome_process = process
            else:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                self.chrome_process = process
            
            print("Waiting for Chrome to start and verify port is listening")
            # Wait for Chrome to start and verify port is listening
            for i in range(20):  # Try for 20 seconds
                await asyncio.sleep(1)
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('127.0.0.1', 9222))
                    sock.close()
                    if result == 0:
                        print(f"Chrome started successfully with remote debugging port (attempt {i+1})")
                        return process
                except Exception as conn_e:
                    print(f"Connection check {i+1} failed: {conn_e}")
                    continue
            
            # If we get here, Chrome didn't start properly
            if hasattr(process, 'stderr') and process.stderr:
                try:
                    stderr = await asyncio.wait_for(process.stderr.read(), timeout=1)
                    print(f"Chrome stderr output: {stderr.decode()}")
                except:
                    pass
            
            raise RuntimeError("Chrome failed to start with remote debugging port after 20 seconds")
            
        except Exception as e:
            print(f"Error launching Chrome: {e}")
            if hasattr(process, 'stderr') and process.stderr:
                try:
                    stderr = await asyncio.wait_for(process.stderr.read(), timeout=1)
                    print(f"Chrome stderr output: {stderr.decode()}")
                except:
                    pass
            raise RuntimeError(f"Failed to launch Chrome: {str(e)}")

    async def create_context(self, 
                           viewport: dict = {"width": 2560, "height": 1440},
                           user_agent: str = None) -> BrowserContext:
        """Create optimized browser context with human-like settings"""
        if not self._browser:
            raise RuntimeError("Browser not connected. Call connect_to_chrome first.")

        # Return existing context if it exists
        if self._context:
            return self._context

        # Create new context with optimized settings
        self._context = await self._browser.new_context(
            viewport=viewport,
            user_agent=user_agent or self._modern_user_agent(),
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"],
            geolocation={"latitude": 40.7128, "longitude": -74.0060},  # NYC
            http_credentials=None,
            proxy=self._proxy_settings(),
            color_scheme="light",
        )

        await self._add_anti_detection()
        await self._configure_network()
        return self._context

    async def _add_anti_detection(self):
        """Inject JavaScript to mask automation"""
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US'] });
            window.chrome = { runtime: {} };
        """)

    async def _configure_network(self):
        """Block unnecessary resources for faster loading"""
        await self._context.route("**/*.{png,jpg,jpeg,webp}", lambda route: route.abort())
        await self._context.route("**/*.css", lambda route: route.abort())
        await self._context.route(re.compile(r"(analytics|tracking|beacon)"), lambda route: route.abort())

    def _modern_user_agent(self) -> str:
        """Generate current Chrome user agent string"""
        versions = {
            "Windows": "122.0.0.0",
            "Darwin": "122.0.0.0",
            "Linux": "122.0.0.0"
        }
        system = platform.system()
        return f"Mozilla/5.0 ({self._os_info()}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{versions[system]} Safari/537.36"

    def _os_info(self) -> str:
        """Get platform-specific OS info for user agent"""
        if platform.system() == "Windows":
            return "Windows NT 10.0; Win64; x64"
        elif platform.system() == "Darwin":
            return "Macintosh; Intel Mac OS X 10_15_7"
        else:
            return "X11; Linux x86_64"

    def _proxy_settings(self) -> Optional[dict]:
        """Parse proxy configuration"""
        if not self.proxy:
            return None
        return {
            "server": self.proxy,
            "username": os.getenv("PROXY_USER"),
            "password": os.getenv("PROXY_PASS")
        }

    async def close(self):
        """Cleanup resources"""
        try:
            if self._context:
                await self._context.close()
        except Exception as e:
            print(f"Error closing context: {e}")
            
        try:
            if self._browser:
                await self._browser.close()
        except Exception as e:
            print(f"Error closing browser: {e}")
            
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            print(f"Error stopping playwright: {e}")
            
        # Clean up Chrome process
        try:
            if self.chrome_process:
                if hasattr(self.chrome_process, 'terminate'):
                    self.chrome_process.terminate()
                    try:
                        await asyncio.wait_for(self.chrome_process.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        if hasattr(self.chrome_process, 'kill'):
                            self.chrome_process.kill()
                else:
                    # For subprocess.Popen objects
                    self.chrome_process.terminate()
                    try:
                        self.chrome_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.chrome_process.kill()
        except Exception as e:
            print(f"Error cleaning up Chrome process: {e}")
            
        # Clean up temporary user data directory
        try:
            temp_user_data = Path.cwd() / "temp_chrome_data"
            if temp_user_data.exists():
                import shutil
                shutil.rmtree(temp_user_data, ignore_errors=True)
        except Exception as e:
            print(f"Error cleaning up temp directory: {e}")