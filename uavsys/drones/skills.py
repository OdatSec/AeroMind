import asyncio
from mavsdk.offboard import PositionNedYaw, VelocityNedYaw
from .mavsdk_client import MavsdkClient
from ..utils.richlog import RichLog

class DroneSkills:
    def __init__(self, client: MavsdkClient):
        self.client = client
        self.drone = client.drone
        self.agent = client.agent_name

    async def get_telemetry(self) -> dict:
        """Snapshot real MAVSDK telemetry: GPS position + battery.
        Returns mock values when in mock mode."""
        if self.client.mock_mode:
            return {"lat": 0.0, "lon": 0.0, "alt_m": 0.0, "battery_pct": 100.0, "source": "mock"}
        try:
            pos_data = {"lat": 0.0, "lon": 0.0, "alt_m": 0.0, "battery_pct": 0.0, "source": "mavsdk"}
            # Get position (read one sample)
            async for position in self.drone.telemetry.position():
                pos_data["lat"] = round(position.latitude_deg, 6)
                pos_data["lon"] = round(position.longitude_deg, 6)
                pos_data["alt_m"] = round(position.relative_altitude_m, 1)
                break
            # Get battery (read one sample)
            async for battery in self.drone.telemetry.battery():
                pos_data["battery_pct"] = round(min(battery.remaining_percent, 100.0), 1)
                break
            return pos_data
        except Exception:
            return {"lat": 0.0, "lon": 0.0, "alt_m": 0.0, "battery_pct": 0.0, "source": "error"}

    def get_tool_descriptions(self) -> str:
        return """
        - connect(): Connect to the drone.
        - arm(): Arm the drone motors.
        - takeoff(alt_m): Takeoff to altitude in meters.
        - goto_location(lat, lon, alt): Fly to GPS coordinates.
        - hover(seconds): Hover for a specific duration.
        - return_to_launch(): Return to home and land.
        """

    async def connect(self):
        await self.client.connect()

    async def arm(self):
        await self.client.arm()

    async def takeoff(self, alt_m: float = 10.0):
        await self.client.takeoff(alt_m)

    async def land(self):
        await self.client.land()

    async def return_to_launch(self):
        """Return to launch position."""
        if self.client.mock_mode:
            RichLog.tool_call(self.agent, "return_to_launch", {})
            await asyncio.sleep(2)
            return
            
        try:
            await self.drone.action.return_to_launch()
        except Exception as e:
            RichLog.error(self.agent, f"RTL failed: {e}")

    async def hover(self, seconds: float):
        await self.client.hover(seconds)

    async def goto(self, north_m: float, east_m: float, down_m: float):
        """
        Robust goto: tries Offboard NED.
        If offboard fails, it logs error (and in a real app would fallback to global).
        """
        RichLog.tool_call(self.agent, "goto", {"n": north_m, "e": east_m, "d": down_m})
        if self.client.mock_mode:
            await asyncio.sleep(2) # Mock travel
            return

        try:
            # We must send a setpoint BEFORE starting offboard mode
            await self.drone.offboard.set_position_ned(PositionNedYaw(north_m, east_m, down_m, 0.0))
            
            try:
                await self.drone.offboard.start()
            except Exception as e:
                # If already in offboard, this might fail or be fine.
                # If failure is "Offboard is already active", we ignore.
                pass

            # Update setpoint
            await self.drone.offboard.set_position_ned(PositionNedYaw(north_m, east_m, down_m, 0.0))
            
            # Simulate travel time (speed approx 5m/s)
            dist = (north_m**2 + east_m**2 + down_m**2)**0.5
            travel_time = dist / 5.0 + 2.0
            await asyncio.sleep(travel_time)

        except Exception as e:
            RichLog.error(self.agent, f"Goto failed (Offboard): {e}")

    async def goto_location(self, lat: float, lon: float, alt: float):
        """Global goto using MAVSDK action plugin. Waits until drone arrives."""
        RichLog.tool_call(self.agent, "goto_location", {"lat": lat, "lon": lon, "alt": alt})
        if self.client.mock_mode:
            await asyncio.sleep(2)
            return

        try:
            await self.drone.action.goto_location(lat, lon, alt, 0)
            RichLog.log(self.agent, f"Traveling to ({lat:.6f}, {lon:.6f}, {alt}m)...", "tool")
            
            # Wait until drone arrives within 10m of target (or timeout 60s)
            import math
            timeout = 60  # seconds
            check_interval = 2  # check every 2s
            elapsed = 0
            last_dist = 999999
            resend_interval = 10  # re-send goto every 10s if stuck
            last_resend = 0
            
            while elapsed < timeout:
                await asyncio.sleep(check_interval)
                elapsed += check_interval
                
                # Re-send goto command periodically to prevent preemption
                if elapsed - last_resend >= resend_interval:
                    try:
                        await self.drone.action.goto_location(lat, lon, alt, 0)
                        last_resend = elapsed
                    except:
                        pass
                
                # Get current position from telemetry
                async for position in self.drone.telemetry.position():
                    cur_lat = position.latitude_deg
                    cur_lon = position.longitude_deg
                    
                    # Calculate distance (meters) using simple approximation
                    dlat = (lat - cur_lat) * 111139
                    dlon = (lon - cur_lon) * 111139 * math.cos(math.radians(lat))
                    dist = math.sqrt(dlat**2 + dlon**2)
                    
                    if dist < 10.0:
                        RichLog.log(self.agent, f"✅ Arrived at target ({dist:.1f}m away)", "tool")
                        return
                    else:
                        RichLog.log(self.agent, f"   En route... {dist:.0f}m remaining", "tool")
                    last_dist = dist
                    break  # Only read one position update per cycle
            
            RichLog.log(self.agent, f"⚠️ Travel timeout ({timeout}s). Proceeding.", "tool")
        except Exception as e:
             RichLog.error(self.agent, f"Goto Global failed: {e}")

    async def execute_tool(self, tool_name: str, args: dict) -> str:
        """Executes a tool by name with arguments."""
        try:
            if tool_name == "connect":
                await self.connect()
            elif tool_name == "arm":
                await self.arm()
            elif tool_name == "takeoff":
                await self.takeoff(float(args.get("alt_m", 10.0)))
            elif tool_name == "land":
                await self.land()
            elif tool_name == "return_to_launch" or tool_name == "rtl":
                await self.return_to_launch()
            elif tool_name == "hover":
                await self.hover(float(args.get("seconds", 5.0)))
            elif tool_name == "goto_location":
                lat = float(args.get("lat"))
                lon = float(args.get("lon"))
                alt = float(args.get("alt", 10.0))
                await self.goto_location(lat, lon, alt)
            elif tool_name == "goto":
                if "lat" in args and "lon" in args:
                    lat = float(args.get("lat"))
                    lon = float(args.get("lon"))
                    alt = float(args.get("alt", 10.0))
                    await self.goto_location(lat, lon, alt)
                else:
                    n = float(args.get("north_m", 0.0))
                    e = float(args.get("east_m", 0.0))
                    d = float(args.get("down_m", -4.0)) # Default to 4m height (-4 down)
                    await self.goto(n, e, d)
            else:
                return f"Unknown tool: {tool_name}"
            return "Success"
        except Exception as e:
            return f"Error: {e}"
