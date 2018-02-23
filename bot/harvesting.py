import json
from pathlib import Path

import sc2
from sc2.constants import *

class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def __init__(self):
        self.extractor_started = False
        self.extractors = 0

    async def saturate_base(self, iteration, hatchery):
        larvae = self.units(LARVA)

        minerals_nicely_saturated = hatchery.ideal_harvesters - hatchery.assigned_harvesters <= 1

        # for the first base, build more workers if minerals are not ideally saturated
        if hatchery.assigned_harvesters < hatchery.ideal_harvesters and self.supply_left > 0:
            if self.can_afford(DRONE) and larvae.exists:
                await self.do(larvae.random.train(DRONE))

        # build more overlords if not already building
        if self.supply_left <= 2 and (not self.units(OVERLORD).not_ready.exists):
            if self.can_afford(OVERLORD) and larvae.exists:
                await self.do(larvae.random.train(OVERLORD))

        # move workers to gas if havent done that yet
        if self.units(EXTRACTOR).ready.exists:
            extractor = self.units(EXTRACTOR).first

            required_harvesters = max(0, extractor.ideal_harvesters - extractor.assigned_harvesters)
            for drone in self.workers.random_group_of(required_harvesters):
                await self.do(drone.gather(extractor))

        # if not self.units(EXTRACTOR).not_ready.exists:
        #     self.extractor_started = False

        # only build extractor when we are capable of doing so
        if not self.extractor_started and self.extractors < 1 and minerals_nicely_saturated:
            if self.can_afford(EXTRACTOR):
                drone = self.workers.random
                target = self.state.vespene_geyser.closest_to(drone.position)
                err = await self.do(drone.build(EXTRACTOR, target))
                if not err:
                    self.extractor_started = True

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")

        hatchery = self.units(HATCHERY).ready.first
        await self.saturate_base(iteration, hatchery)
        
