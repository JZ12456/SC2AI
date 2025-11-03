#!/usr/bin/env python3
#Rule-based Terran bot with improved micro and logging
#Auto-saves replay and logs match stats
#Able to fight all 3 races

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.bot_ai import BotAI
from sc2.constants import *
import random, os, csv, datetime, math

REPLAY_DIR = "replays"
LOG_FILE = "match_log.csv"
os.makedirs(REPLAY_DIR, exist_ok=True)

class FinalTerranBot(BotAI):
    def __init__(self):
        super().__init__()
        self.scout_sent = False
        self.last_drop_time = 0
        self.drop_cooldown = 60
        self.research_started = False
        #Stats
        self.kills = 0
        self.losses = 0

    async def on_step(self, iteration):
        try:
            await self.macro_manager.on_step()
        except Exception:
            pass
        try:
            await self.micro_manager.on_step()
        except Exception:
            pass
        await self.distribute_workers()
        await self.produce_workers()
        await self.build_supply()
        await self.build_production()
        await self.train_units()
        await self.army_micro()
        await self.scout()
        await self.use_stim()

    async def produce_workers(self):
        for th in self.townhalls.ready:
            if th.is_idle and self.can_afford(SCV) and self.workers.amount < max(14, 18 * self.townhalls.amount):
                await self.do(th.train(SCV))

    async def build_supply(self):
        if self.supply_left < 5 and not self.already_pending(SUPPLYDEPOT):
            if self.can_afford(SUPPLYDEPOT):
                loc = self.start_location.towards(self.game_info.map_center, 6)
                await self.build(SUPPLYDEPOT, near=loc)

    async def build_production(self):
        if self.structures(BARRACKS).amount < 2 and not self.already_pending(BARRACKS):
            if self.can_afford(BARRACKS):
                await self.build(BARRACKS, near=self.townhalls.first.position.towards(self.game_info.map_center, 8))
        if self.structures(FACTORY).amount < 1 and not self.already_pending(FACTORY):
            if self.can_afford(FACTORY):
                await self.build(FACTORY, near=self.townhalls.first.position.towards(self.game_info.map_center, 10))
        if self.structures(STARPORT).amount < 1 and not self.already_pending(STARPORT):
            if self.can_afford(STARPORT):
                await self.build(STARPORT, near=self.townhalls.first.position.towards(self.game_info.map_center, 12))

    async def train_units(self):
        for rax in self.structures(BARRACKS).ready.idle:
            if self.can_afford(MARINE):
                await self.do(rax.train(MARINE))
        for sp in self.structures(STARPORT).ready.idle:
            if self.can_afford(MEDIVAC):
                await self.do(sp.train(MEDIVAC))

    async def army_micro(self):
        marines = self.units(MARINE)
        medivacs = self.units(MEDIVAC)
        enemies = self.enemy_units

        #Heal Marines with Medivacs
        for med in medivacs.ready:
            wounded = marines.closer_than(5, med).filter(lambda u: u.health_percentage < 1.0)
            for m in wounded:
                await self.do(m.move(med.position))

        #Focus fire & kiting
        for m in marines.idle:
            threats = enemies.closer_than(8, m.position)
            if threats.exists:
                target = min(threats, key=lambda u: u.health + getattr(u, "shield", 0))
                await self.do(m.attack(target.position))
            elif enemies.exists:
                target = enemies.closest_to(m)
                await self.do(m.attack(target.position))
            else:
                #Push to enemy base if army sufficient
                if marines.amount > 20:
                    for m in marines.idle:
                        await self.do(m.attack(self.enemy_start_locations[0]))
                elif marines.amount > 8:
                    for m in marines.random_group(min(5, marines.amount)).idle:
                        await self.do(m.attack(self.enemy_start_locations[0]))

    async def scout(self):
        if not self.scout_sent and self.workers.exists:
            scout = self.workers.random
            if scout:
                self.scout_sent = True
                await self.do(scout.move(self.enemy_start_locations[0]))

    async def use_stim(self):
        for m in self.units(MARINE).ready:
            abilities = await self.get_available_abilities(m)
            if AbilityId.EFFECT_STIM_MARINE in abilities:
                enemies = self.enemy_units.closer_than(8, m.position)
                if enemies.exists or self.units(MARINE).amount > 15:
                    await self.do(m(AbilityId.EFFECT_STIM_MARINE))

    async def on_unit_destroyed(self, unit_tag):
        self.losses += 1

    async def on_unit_killed(self, unit_tag):
        self.kills += 1

    async def on_end(self, game_result):
        replay_name = f"{REPLAY_DIR}/replay_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.SC2Replay"
        await self.save_replay(replay_name)

        #Log match stats to CSV
        log_exists = os.path.exists(LOG_FILE)
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            if not log_exists:
                writer.writerow(["datetime","result","kills","losses","final_army_size","enemy_race","difficulty"])
            writer.writerow([
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                game_result.name,
                self.kills,
                self.losses,
                self.units.amount,
                self.enemy_race.name,
                self.difficulty.name
            ])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--race", type=str, default="Zerg", help="Opponent race: Zerg, Protoss, Terran")
    parser.add_argument("--difficulty", type=str, default="Medium", help="Opponent difficulty: Easy, Medium, Hard")
    args = parser.parse_args()

    race_map = {"Zerg": Race.Zerg, "Protoss": Race.Protoss, "Terran": Race.Terran}
    diff_map = {"Easy": Difficulty.Easy, "Medium": Difficulty.Medium, "Hard": Difficulty.Hard}

    bot = Bot(Race.Terran, FinalTerranBot())
    comp = Computer(race_map.get(args.race, Race.Zerg), diff_map.get(args.difficulty, Difficulty.Medium))
    run_game(maps.get("AbyssalReefLE"), [bot, comp], realtime=False)
