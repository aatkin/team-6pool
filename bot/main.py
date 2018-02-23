import json
from pathlib import Path
from pprint import pprint

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer


class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def __init__(self):
        self.drone_counter = 0
        self.speedlings = False
        self.speedlings_started = 0
        self.melee1 = False
        self.armor1 = False

    async def on_step(self, iteration):
        hatchery = self.units(HATCHERY).ready.first
        larvae = self.units(LARVA)
        minerals_nicely_saturated = hatchery.ideal_harvesters - hatchery.assigned_harvesters <= 1

        if iteration % 100 == 0:
            pprint(vars(self))

        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")

        if iteration == 666:
            await self.chat_send("666 HELLFIRE")

        if self.supply_left < 3 and not self.already_pending(OVERLORD):
            if self.can_afford(OVERLORD) and larvae.exists:
                await self.do(larvae.random.train(OVERLORD))

        if not minerals_nicely_saturated:
            if self.can_afford(DRONE) and self.supply_left >= 1 and larvae.exists:
                self.drone_counter += 1
                await self.do(larvae.random.train(DRONE))

        # move workers to gas if havent done that yet
        if self.units(EXTRACTOR).ready.exists:
            extractor = self.units(EXTRACTOR).first

            required_harvesters = max(0, extractor.ideal_harvesters - extractor.assigned_harvesters)
            for drone in self.workers.random_group_of(required_harvesters):
                await self.do(drone.gather(extractor))

        if not self.already_pending(EXTRACTOR) and len(self.units(EXTRACTOR)) < 1 and minerals_nicely_saturated:
            if self.can_afford(EXTRACTOR):
                drone = self.workers.random
                target = self.state.vespene_geyser.closest_to(drone.position)
                err = await self.do(drone.build(EXTRACTOR, target))
                if not err:
                    self.extractor_started = True

        if not self.units(SPAWNINGPOOL) and not self.already_pending(SPAWNINGPOOL):
            if self.can_afford(SPAWNINGPOOL):
                worker = self.select_build_worker(hatchery, force=True)
                pos = hatchery.position.to2.towards(self.game_info.map_center, 5)
                await self.build(SPAWNINGPOOL, pos, unit=worker)

        if not self.units(EVOLUTIONCHAMBER) and not self.already_pending(EVOLUTIONCHAMBER) and (self.units(SPAWNINGPOOL) or self.already_pending(SPAWNINGPOOL)):
            if self.can_afford(EVOLUTIONCHAMBER):
                worker = self.select_build_worker(hatchery, force=True)
                pos = hatchery.position.to2.towards(self.game_info.map_center, 5)
                await self.build(EVOLUTIONCHAMBER, pos, unit=worker)

        if self.vespene >= 100:
            sp = self.units(SPAWNINGPOOL).ready
            if sp.exists and self.minerals >= 100 and not self.speedlings:
                await self.do(sp.first(RESEARCH_ZERGLINGMETABOLICBOOST))
                self.speedlings = True
                self.speedlings_started = self.state.game_loop

        if self.vespene >= 100:
            evo = self.units(EVOLUTIONCHAMBER).ready
            if evo.exists and not self.melee1 and self.minerals >= 100:
                await self.do(evo.first(RESEARCH_ZERGMELEEWEAPONSLEVEL1))
                self.melee1 = True

        if self.vespene >= 150:
            evo = self.units(EVOLUTIONCHAMBER).ready
            if evo.exists and not self.armor1 and self.minerals >= 150:
                await self.do(evo.first(RESEARCH_ZERGGROUNDARMORLEVEL1))
                self.armor1 = True

        if self.units(SPAWNINGPOOL).ready.exists:
            if larvae.exists and self.can_afford(ZERGLING):
                await self.do(larvae.random.train(ZERGLING))

        if self.speedlings and (self.state.game_loop - self.speedlings_started) > 1800:
            target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
            for zl in self.units(ZERGLING).idle:
                await self.do(zl.attack(target))
