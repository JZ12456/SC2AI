
import asyncio
from sc2 import UnitTypeId, AbilityId
import time

class MacroManager:
    """
    EXECUTES THE BUILD ORDER AND BUILDS SCVS
    """
    def __init__(self, bot):
        self.bot = bot
        self.bo_pointer = 0
        self.last_bo_time = time.time()

    async def on_step(self):
        await self._ensure_workers()
        await self._ensure_supply()
        await self._execute_build_order()
        await self._manage_production()

    async def _ensure_workers(self):
        try:
            ideal_workers = 20 * max(1, self.bot.townhalls.amount)
            if self.bot.workers.amount < ideal_workers and self.bot.can_afford(UnitTypeId.SCV):
                await self.bot.train(UnitTypeId.SCV)
        except Exception:
            pass

    async def _ensure_supply(self):
        try:
            if self.bot.supply_left < 4 and not self.bot.already_pending(UnitTypeId.SUPPLYDEPOT):
                if self.bot.can_afford(UnitTypeId.SUPPLYDEPOT):
                    worker = self.bot.workers.random_or(None)
                    if worker:
                        await self.bot.do(worker.build(UnitTypeId.SUPPLYDEPOT, self.bot.start_location.position.toward(self.bot.game_info.map_center, 5)))
        except Exception:
            pass

    async def _execute_build_order(self):
        try:
            bo = self.bot.strategy.get_build_order()
            if not bo:
                return
            if self.bo_pointer >= len(bo):
                return
            goal = bo[self.bo_pointer]
            action = goal[0]
            if action == "train":
                unit = goal[1]
                count = goal[2] if len(goal) > 2 else 1
                current = self.bot.units(unit).amount
                if current < count and self.bot.can_afford(unit):
                    #Send training orders to idle production if available
                    for b in self.bot.structures(UnitTypeId.BARRACKS).idle:
                        await self.bot.do(b.train(unit))
                else:
                    self.bo_pointer += 1
            elif action == "build":
                structure = goal[1]
                if not self.bot.structures(structure).exists and self.bot.can_afford(structure):
                    worker = self.bot.workers.random_or(None)
                    if worker:
                        await self.bot.do(worker.build(structure, self.bot.start_location.position.toward(self.bot.game_info.map_center, 8)))
                else:
                    self.bo_pointer += 1
            elif action == "tech":
                tech = goal[1]
                if tech == "Medivac":
                    #Prioritize starport then medivac
                    if not self.bot.structures(UnitTypeId.STARPORT).exists:
                        if self.bot.structures(UnitTypeId.FACTORY).exists and self.bot.can_afford(UnitTypeId.STARPORT):
                            worker = self.bot.workers.random_or(None)
                            if worker:
                                await self.bot.do(worker.build(UnitTypeId.STARPORT, self.bot.start_location.position.toward(self.bot.game_info.map_center, 10)))
                    else:
                        #Try to build medivac
                        if self.bot.can_afford(UnitTypeId.MEDIVAC):
                            for s in self.bot.structures(UnitTypeId.STARPORT).idle:
                                await self.bot.do(s.train(UnitTypeId.MEDIVAC))
                        #Advance when we have at least 1 medivac
                        if self.bot.units(UnitTypeId.MEDIVAC).amount >= 1:
                            self.bo_pointer += 1
                elif tech == "Factory":
                    if not self.bot.structures(UnitTypeId.FACTORY).exists:
                        if self.bot.can_afford(UnitTypeId.FACTORY):
                            worker = self.bot.workers.random_or(None)
                            if worker:
                                await self.bot.do(worker.build(UnitTypeId.FACTORY, self.bot.start_location.position.toward(self.bot.game_info.map_center, 10)))
                    else:
                        self.bo_pointer += 1
                elif tech == "SiegeTank":
                    #Makes sure factory makes tanks
                    if self.bot.can_afford(UnitTypeId.SIEGETANK):
                        for f in self.bot.structures(UnitTypeId.FACTORY).idle:
                            await self.bot.do(f.train(UnitTypeId.SIEGETANK))
                    #Advance when we have at least 1 tank
                    if self.bot.units(UnitTypeId.SIEGETANK).amount >= 1:
                        self.bo_pointer += 1
                else:
                    self.bo_pointer += 1
            elif action in ("drop_play","timed_push","add_medivac_support","mix"):
                if time.time() - self.last_bo_time > 6:
                    self.bo_pointer += 1
                    self.last_bo_time = time.time()
            else:
                #If there is no right action ADVANCE ALL IN
                self.bo_pointer += 1
        except Exception:
            pass

    async def _manage_production(self):
        #Simple macro cycle 
        try:
            #Marines
            for b in self.bot.structures(UnitTypeId.BARRACKS).idle:
                if self.bot.can_afford(UnitTypeId.MARINE):
                    await self.bot.do(b.train(UnitTypeId.MARINE))
            #Medivacs
            for s in self.bot.structures(UnitTypeId.STARPORT).idle:
                if self.bot.can_afford(UnitTypeId.MEDIVAC):
                    await self.bot.do(s.train(UnitTypeId.MEDIVAC))
            #!!!!Maruaders if against Protoss
            if self.bot.strategy and "Protoss" in str(self.bot.enemy_race):
                for b in self.bot.structures(UnitTypeId.BARRACKS).idle:
                    if self.bot.can_afford(UnitTypeId.MARAUDER):
                        await self.bot.do(b.train(UnitTypeId.MARAUDER))
        except Exception:
            pass
