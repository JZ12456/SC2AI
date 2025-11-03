
import math
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2

class MicroManager:
    """
    - Target prioritization: casters/ranged/high-damage units prioritized
    - Retreat logic: compare incoming DPS estimations vs unit HP
    - Medivac pickup/drop logic with simple drop target selection
    """
    def __init__(self, bot):
        self.bot = bot
        self._last_stutter = {}

    def _unit_priority(self, unit):
        #Higher numbers = higher priority
        #Prioritize casters,ranged and DPS units
        priority = 0
        if unit.type_id in {UnitTypeId.BANELING, UnitTypeId.ZERGLING}:
            priority += 5
        #Ranged/high value
        if unit.is_structure:
            priority += 1
        #Protoss casters (high priority bc templar, disruptor and colossus kinda cheese ngl)
        try:
            #Approximate by checking if unit is bio,mech or bio with shield
            if hasattr(unit, 'is_mechanical') and not unit.is_mechanical and hasattr(unit, 'shield'):
                priority += 4
        except Exception:
            pass
        #Add based on attack damage if available
        try:
            if getattr(unit, 'attack_damage', 0) > 10:
                priority += 3
        except Exception:
            pass
        return priority

    async def on_step(self):
        await self._marine_micro()
        await self._medivac_micro()

    async def _marine_micro(self):
        try:
            marines = self.bot.units(UnitTypeId.MARINE)
            enemies = self.bot.enemy_units
            if not marines.exists or not enemies.exists:
                return

            #Calculate enemy threats
            #For each marine, choose target with highest priority-weighted 
            for m in marines.idle:
                #Choose targets sorted by priority then health
                targets = sorted(enemies, key=lambda e: (-self._unit_priority(e), e.health + getattr(e,'shield',0)))
                if not targets:
                    continue
                target = targets[0]

                #Estimate incoming DPS around marine (Within 6 range)
                nearby_enemies = enemies.closer_than(6, m)
                estimated_enemy_dps = 0
                for e in nearby_enemies:
                    try:
                        estimated_enemy_dps += getattr(e, 'attack_damage', 5)
                    except Exception:
                        estimated_enemy_dps += 5

                #Retreat if estimated DPS would kill marine before it can fire twice
                marine_hp = m.health + getattr(m, 'shield', 0)
                #Assume marine can deal 6 damage per shot and fires twice
                marine_survival_time = marine_hp / max(1, estimated_enemy_dps)
                if marine_survival_time < 1.5:  # heuristic: too dangerous
                    #Fallback to base or medivac
                    if self.bot.units(UnitTypeId.MEDIVAC).exists:
                        safe_point = self.bot.units(UnitTypeId.MEDIVAC).closest_to(m).position
                    else:
                        safe_point = self.bot.start_location.position
                    await self.bot.do(m.move(safe_point))
                    continue

                #Stutter-step behavior(Flash Flash Flash)
                wc = getattr(m, 'weapon_cooldown', 0)
                if wc and wc > 0:
                    retreat_point = m.position.toward(self.bot.start_location.position, 2.5)
                    await self.bot.do(m.move(retreat_point))
                else:
                    await self.bot.do(m.attack(target.position))
        except Exception:
            pass

    async def _medivac_micro(self):
        try:
            medivacs = self.bot.units(UnitTypeId.MEDIVAC)
            if not medivacs.exists:
                return
            injured = self.bot.units.filter(lambda u: u.is_biological and u.health_percentage < 0.9)
            army = self.bot.units.of_type([UnitTypeId.MARINE, UnitTypeId.MARAUDER])
            for mv in medivacs.idle:
                #Pickup logic (Preserve low hp units)
                close_injured = injured.closer_than(8, mv)
                if close_injured.exists:
                    to_pick = close_injured.sorted(lambda u: u.health)[0]
                    try:
                        await self.bot.do(mv(AbilityId.LOAD_MEDIVAC, to_pick))
                    except Exception:
                        await self.bot.do(mv.move(to_pick.position))
                    continue

                # Drop logic (Drop behind army or worker line)
                if mv.has_cargo:
                    #Choose drop target (Priority on worker line)
                    enemy_workers = self.bot.enemy_units.filter(lambda u: u.is_worker)
                    if enemy_workers.exists:
                        drop_target = enemy_workers.closest_to(mv).position
                    elif self.bot.enemy_start_locations:
                        drop_target = self.bot.enemy_start_locations[0].position
                    else:
                        drop_target = self.bot.game_info.map_center
                    #Move to drop target
                    await self.bot.do(mv.move(drop_target))
                    #Unload when close
                    if mv.distance_to(drop_target) < 6:
                        try:
                            await self.bot.do(mv(AbilityId.UNLOAD_ALL))
                        except Exception:
                            pass
                    continue

                #Making sure idle medivacs are near army units
                if army.exists:
                    await self.bot.do(mv.move(army.center))
        except Exception:
            pass
