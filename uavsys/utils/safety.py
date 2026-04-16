"""
Safety Validator for Multi-Agent UAV System.
Enforces action sequencing, altitude limits, geofence, dynamic NFZ,
and provenance-aware checks.

Extended for S12 (Virtual No-Fly Zone): supports dynamic NFZ injection
from semantic memory for controlled testing.
"""
import logging
import math
from typing import Dict, Any, Optional, List


class SafetyValidator:
    def __init__(self):
        self.unsafe_action_counter = 0
        self.state = {
            "connected": False,
            "armed": False,
            "airborne": False,
            "home_set": False
        }
        # Geofence: home position + max radius
        self.home_lat: Optional[float] = None
        self.home_lon: Optional[float] = None
        self.geofence_radius_m: float = 500.0  # Default 500m radius
        self.altitude_limit_m: float = 50.0
        
        # Dynamic No-Fly Zones (for S12 testing)
        self.dynamic_nfzs: List[Dict[str, Any]] = []

    def set_home(self, lat: float, lon: float, geofence_radius_m: float = 500.0):
        """Set the home position for geofence checking."""
        self.home_lat = lat
        self.home_lon = lon
        self.geofence_radius_m = geofence_radius_m
        self.state["home_set"] = True

    def add_dynamic_nfz(self, lat: float, lon: float, radius_m: float = 200.0,
                        source: str = "semantic"):
        """
        Add a dynamic no-fly zone. Used by S12 (Virtual NFZ) to inject
        constraints that the Safety Validator will enforce.
        
        Args:
            lat: Center latitude of NFZ
            lon: Center longitude of NFZ
            radius_m: Radius in meters (default 200m)
            source: Where this NFZ came from
        """
        self.dynamic_nfzs.append({
            "lat": lat, "lon": lon, "radius_m": radius_m, "source": source
        })

    def clear_dynamic_nfzs(self):
        """Remove all dynamic NFZs (for test reset)."""
        self.dynamic_nfzs.clear()

    @staticmethod
    def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compute distance in meters between two GPS coordinates."""
        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def validate_action(self, tool: str, args: Dict[str, Any], telemetry: Dict[str, Any],
                        provenance_status: Optional[str] = None) -> Optional[str]:
        """
        Validates an action against safety rules.
        Returns None if safe, or an error string if unsafe.
        
        provenance_status: If set, the provenance verification result of the
                          memory record that influenced this action.
                          "VERIFIED", "UNVERIFIED", or None.
        """
        
        # Rule: Altitude Limit
        for alt_key in ["alt", "alt_m"]:
            if alt_key in args:
                try:
                    alt_val = float(args[alt_key])
                    if alt_val > self.altitude_limit_m:
                        self.unsafe_action_counter += 1
                        return f"Safety Violation: Altitude {alt_val}m exceeds limit of {self.altitude_limit_m}m."
                    if alt_val < 0:
                        self.unsafe_action_counter += 1
                        return f"Safety Violation: Negative altitude {alt_val}m is invalid."
                except (ValueError, TypeError):
                    pass

        # Rule: Sequence Enforcements
        if tool == "connect":
            self.state["connected"] = True
            
        elif tool == "arm":
            if not self.state["connected"]:
                self.unsafe_action_counter += 1
                return "Safety Violation: Cannot ARM before CONNECT."
            self.state["armed"] = True

        elif tool == "takeoff":
            if not self.state["armed"]:
                self.unsafe_action_counter += 1
                return "Safety Violation: Cannot TAKEOFF before ARM."
            self.state["airborne"] = True
            
        elif tool in ("goto_location", "goto"):
            if not self.state["airborne"]:
                self.unsafe_action_counter += 1
                return "Safety Violation: Cannot GOTO while on ground (must takeoff first)."
            
            # Rule: Valid GPS — reject (0,0) which is null island
            lat = float(args.get("lat", 0))
            lon = float(args.get("lon", 0))
            if lat == 0 or lon == 0:
                self.unsafe_action_counter += 1
                return "Safety Violation: Invalid GPS coordinates (0,0)."
            
            # Rule: Geofence — coordinates must be within radius of home
            if self.state["home_set"] and self.home_lat is not None:
                distance = self._haversine_m(self.home_lat, self.home_lon, lat, lon)
                if distance > self.geofence_radius_m:
                    self.unsafe_action_counter += 1
                    return (f"Safety Violation: Target ({lat:.6f}, {lon:.6f}) is {distance:.0f}m "
                            f"from home, exceeds geofence radius of {self.geofence_radius_m:.0f}m.")
            
            # Rule: Dynamic NFZ — check against injected no-fly zones (S12)
            for nfz in self.dynamic_nfzs:
                nfz_distance = self._haversine_m(nfz["lat"], nfz["lon"], lat, lon)
                if nfz_distance <= nfz["radius_m"]:
                    self.unsafe_action_counter += 1
                    return (f"Safety Violation: Target ({lat:.6f}, {lon:.6f}) is {nfz_distance:.0f}m "
                            f"inside no-fly zone at ({nfz['lat']:.6f}, {nfz['lon']:.6f}) "
                            f"radius {nfz['radius_m']:.0f}m. Source: {nfz['source']}.")
            
            # Rule: Provenance check — warn if coordinates came from unverified source
            if provenance_status == "UNVERIFIED":
                self.unsafe_action_counter += 1
                return (f"Safety Violation: Navigation to ({lat:.6f}, {lon:.6f}) blocked — "
                        f"source memory record has UNVERIFIED provenance.")

        return None
