import json
from pathlib import Path
from pprint import pprint

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer


def seconds_to_ticks(s):
    return s * 21.5


class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def __init__(self):
        self.drone_counter = 0

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
                await self.build(SPAWNINGPOOL, hatchery, unit=worker)
