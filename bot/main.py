import json
from pathlib import Path
from pprint import pprint
import math

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.position import Point2


class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def __init__(self):
        self.drone_counter = 0
        self.speedlings = False
        self.speedlings_started = 0
        self.melee1 = False
        self.armor1 = False
        self.queen_counter = 0
        self.hatchery_count = 1
        self.extractor_started = False

    async def on_step(self, iteration):
        hatchery = self.units(HATCHERY).ready.closest_to(self.workers[0].position)
        larvae = self.units(LARVA)
        minerals_nicely_saturated = (hatchery.ideal_harvesters - hatchery.assigned_harvesters) <= 0
        should_spawn_overlord = self.supply_left <= 3 and not self.already_pending(OVERLORD) and self.drone_counter != 0

        # if iteration % 100 == 0:
        #     print("start", self.game_info.start_locations[0])
        #     print("hatch", hatchery.position)
        #     print("drone count", self.drone_counter)

        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")

        if iteration == 666:
            await self.chat_send("666 HELLFIRE")

        if self.supply_left < 4 and not self.already_pending(OVERLORD):
            if self.can_afford(OVERLORD) and larvae.exists:
                await self.do(larvae.random.train(OVERLORD))

        if not minerals_nicely_saturated and not self.already_pending(DRONE) and not should_spawn_overlord:
            if self.can_afford(DRONE) and self.supply_left >= 1 and larvae.exists:
                self.drone_counter += 1
                await self.do(larvae.random.train(DRONE))

        # move workers to gas if havent done that yet
        if self.units(EXTRACTOR).ready.exists:
            extractor = self.units(EXTRACTOR).first

            required_harvesters = max(0, extractor.ideal_harvesters - extractor.assigned_harvesters)
            for drone in self.workers.random_group_of(required_harvesters):
                await self.do(drone.gather(extractor))

        if not self.already_pending(EXTRACTOR) and not self.units(EXTRACTOR).ready.exists and not should_spawn_overlord and not self.extractor_started:
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

        if self.can_afford(QUEEN) and self.queen_counter < 1:
            queue_full = await self.do(hatchery.train(QUEEN))
            if not queue_full:
                self.queen_counter += 1

        if self.vespene >= 100:
            sp = self.units(SPAWNINGPOOL).ready
            if sp.exists and self.minerals >= 100 and not self.speedlings:
                await self.do(sp.first(RESEARCH_ZERGLINGMETABOLICBOOST))
                self.speedlings = True
                self.speedlings_started = self.state.game_loop

        if self.vespene >= 100 and self.speedlings:
            evo = self.units(EVOLUTIONCHAMBER).ready
            if evo.exists and not self.melee1 and self.minerals >= 100:
                await self.do(evo.first(RESEARCH_ZERGMELEEWEAPONSLEVEL1))
                self.melee1 = True

        if self.vespene >= 150 and self.speedlings:
            evo = self.units(EVOLUTIONCHAMBER).ready
            if evo.exists and not self.armor1 and self.minerals >= 150:
                await self.do(evo.first(RESEARCH_ZERGGROUNDARMORLEVEL1))
                self.armor1 = True

        if self.units(SPAWNINGPOOL).ready.exists and minerals_nicely_saturated and not should_spawn_overlord:
            if larvae.exists and self.can_afford(ZERGLING):
                await self.do(larvae.random.train(ZERGLING))

        if self.speedlings and 1000 < (self.state.game_loop - self.speedlings_started) < 3000:
            enemy_start = self.enemy_start_locations[0]
            expansions_pos = self.expansion_locations.keys()
            closest = None
            min_dist = 100000
            for p in expansions_pos:
                if p == enemy_start: continue
                dist = math.sqrt((p[0] - enemy_start[0]) ** 2 + (p[1] - enemy_start[1]) ** 2)
                if dist < min_dist and dist > 8:
                    min_dist = dist
                    closest = Point2(p).towards(self.game_info.map_center, 5)

            if closest:
                for zl in self.units(ZERGLING).idle:
                    await self.do(zl.attack(closest))

        if self.speedlings and (self.state.game_loop - self.speedlings_started) > 3000:
            target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
            for zl in self.units(ZERGLING).idle:
                await self.do(zl.attack(target))

        for queen in self.units(QUEEN).idle:
            abilities = await self.get_available_abilities(queen)
            if AbilityId.EFFECT_INJECTLARVA in abilities:
                await self.do(queen(EFFECT_INJECTLARVA, hatchery))

        if self.can_afford(HATCHERY) and self.units(SPAWNINGPOOL).ready.exists and self.units(EVOLUTIONCHAMBER).ready.exists and self.hatchery_count < 2:
            self.hatchery_count += 1
            await self.expand_now()
