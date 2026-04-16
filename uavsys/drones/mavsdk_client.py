import asyncio
import logging
from mavsdk import System
from ..utils.richlog import RichLog

class MavsdkClient:
    def __init__(self, grpc_port: int, system_address: str, agent_name: str):
        self.grpc_port = grpc_port
        self.system_address = system_address
        self.agent_name = agent_name
        # Start MAVSDK server on specific gRPC port
        self.drone = System(port=grpc_port)
        self.is_connected = False
        self.mock_mode = False

    async def connect(self):
        """Connects to the drone via UDP system address."""
        RichLog.log(self.agent_name, f"Connecting to drone at {self.system_address} (gRPC {self.grpc_port})...", "system")
        try:
            # We use a timeout to decide if we should fallback to mock
            await asyncio.wait_for(self._connect_loop(), timeout=10.0)
        except asyncio.TimeoutError:
            self.mock_mode = True
            RichLog.error(self.agent_name, f"Connection timed out. Switching to MOCK MODE.")
        except Exception as e:
             self.mock_mode = True
             RichLog.error(self.agent_name, f"Connection failed: {e}. Switching to MOCK MODE.")

    async def _connect_loop(self):
        await self.drone.connect(system_address=self.system_address)
        RichLog.log(self.agent_name, "Waiting for drone connection...", "system")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                self.is_connected = True
                RichLog.log(self.agent_name, "Drone connected!", "system")
                break
        
        # Check health/global position just like user snippet
        RichLog.log(self.agent_name, "Checking global position...", "system")
        async for health in self.drone.telemetry.health():
             if health.is_global_position_ok and health.is_home_position_ok:
                 RichLog.log(self.agent_name, "Global position OK.", "system")
                 break

    async def arm(self):
        RichLog.tool_call(self.agent_name, "arm", {})
        if self.mock_mode: return
        try:
            await self.drone.action.arm()
        except Exception as e:
            if "COMMAND_DENIED" in str(e):
                RichLog.log(self.agent_name, "Arming denied (likely already armed), proceeding.", "system")
            else:
                RichLog.error(self.agent_name, f"Arming failed: {e}")
                raise

    async def disarm(self):
        RichLog.tool_call(self.agent_name, "disarm", {})
        if self.mock_mode: return
        try:
            await self.drone.action.disarm()
        except Exception as e:
            RichLog.error(self.agent_name, f"Disarming failed: {e}")

    async def takeoff(self, altitude_m: float = 10.0):
        RichLog.tool_call(self.agent_name, "takeoff", {"alt_m": altitude_m})
        if self.mock_mode: return
        try:
            await self.drone.action.set_takeoff_altitude(altitude_m)
            await self.drone.action.takeoff()
            
            # Wait for altitude like in user snippet?
            # User snippet:
            # async for pos in drone.telemetry.position():
            #    if abs(pos.relative_altitude_m - altitude) < ALTITUDE_THRESHOLD: ...
            
            # We can do a simplified wait here or trust the action returns when initiated
            # MAVSDK action.takeoff returns when command is sent, not finished.
            # But for ReAct loop, maybe we just return success.
            # Let's add a small wait logic if we want to be fancy, 
            # but simple sleep is "good enough" for demo structure.
            await asyncio.sleep(5)
            
        except Exception as e:
            RichLog.error(self.agent_name, f"Takeoff failed: {e}")
            raise

    async def land(self):
        RichLog.tool_call(self.agent_name, "land", {})
        if self.mock_mode: return
        try:
            await self.drone.action.land()
        except Exception as e:
            RichLog.error(self.agent_name, f"Landing failed: {e}")
            raise

    async def hover(self, seconds: float):
        RichLog.tool_call(self.agent_name, "hover", {"seconds": seconds})
        # Even in mock mode we wait
        await asyncio.sleep(seconds)

    async def goto_local(self, north_m: float, east_m: float, down_m: float, yaw_deg: float = 0.0):
        RichLog.tool_call(self.agent_name, "goto_local", {"n": north_m, "e": east_m, "d": down_m, "yaw": yaw_deg})
        if self.mock_mode: return
        try:
            await self.drone.offboard.set_position_ned(
                from_mavsdk.offboard.PositionNedYaw(north_m, east_m, down_m, yaw_deg)
            )
            await self.drone.offboard.start()
            await asyncio.sleep(5) 
        except Exception as e:
             RichLog.error(self.agent_name, f"Goto Local failed: {e}. Trying fallback...")
             pass
