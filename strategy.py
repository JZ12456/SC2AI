
from sc2 import Race, UnitTypeId

class RaceStrategy:
    """
    Pro-style, timed build orders per enemy race.
    Timings are approximate.
    MacroManager will attempt to follow these timings as triggers.
    """

    def __init__(self, enemy_race: Race):
        self.enemy_race = enemy_race
        self.strategy = self._select_strategy(enemy_race)

    def _select_strategy(self, enemy_race):
        #Each build step
        if enemy_race == Race.Zerg:
            return {
                "name": "ProBioDrop_Zerg_Timed",
                "description": "Standard bio drop with stim timing vs Zerg",
                "build_order": [
                    {"time": 0, "action": "train", "unit": UnitTypeId.SCV, "count": 12},
                    {"time": 40, "action": "build", "unit": UnitTypeId.SUPPLYDEPOT},
                    {"time": 70, "action": "train", "unit": UnitTypeId.SCV, "count": 14},
                    {"time": 95, "action": "build", "unit": UnitTypeId.BARRACKS},
                    {"time": 220, "action": "train", "unit": UnitTypeId.MARINE, "count": 6},
                    {"time": 300, "action": "tech", "unit": "Stim"},
                    {"time": 360, "action": "build", "unit": UnitTypeId.FACTORY},
                    {"time": 460, "action": "tech", "unit": "Medivac"},
                    {"time": 520, "action": "drop_play"},
                    {"time": 600, "action": "timed_push", "count": 9}
                ]
            }
        elif enemy_race == Race.Protoss:
            return {
                "name": "ProMarauderTank_Protoss_Timed",
                "description": "Marauder + Tank timing vs Protoss",
                "build_order": [
                    {"time": 0, "action": "train", "unit": UnitTypeId.SCV, "count": 12},
                    {"time": 40, "action": "build", "unit": UnitTypeId.SUPPLYDEPOT},
                    {"time": 100, "action": "build", "unit": UnitTypeId.BARRACKS},
                    {"time": 240, "action": "tech", "unit": "Factory"},
                    {"time": 360, "action": "train", "unit": UnitTypeId.MARAUDER, "count": 4},
                    {"time": 540, "action": "tech", "unit": "SiegeTank"},
                    {"time": 720, "action": "add_medivac_support"},
                    {"time": 900, "action": "timed_push", "count": 12}
                ]
            }
        else:
            return {
                "name": "AdaptiveTerran_Mirror_Timed",
                "description": "Flexible Terran mirror plan",
                "build_order": [
                    {"time": 0, "action": "train", "unit": UnitTypeId.SCV, "count": 12},
                    {"time": 50, "action": "build", "unit": UnitTypeId.SUPPLYDEPOT},
                    {"time": 110, "action": "build", "unit": UnitTypeId.BARRACKS},
                    {"time": 300, "action": "train", "unit": UnitTypeId.MARINE, "count": 6},
                    {"time": 420, "action": "tech", "unit": "Factory"},
                    {"time": 600, "action": "tech", "unit": "Starport"},
                    {"time": 800, "action": "mix"}
                ]
            }

    def get_build_order(self):
        return self.strategy.get("build_order", [])

    def get_name(self):
        return self.strategy.get("name", "DefaultStrategy")

    def get_description(self):
        return self.strategy.get("description", "")
