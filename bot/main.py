import json
from pathlib import Path
from pprint import pprint

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer


def seconds_to_ticks(s):
    return s * 21.5


overlord_build_time = seconds_to_ticks(18)


class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    def __init__(self):
        self.drone_counter = 0
        self.overlord_started = 0
        self.building_overlord = False

    async def on_step(self, iteration):
        hatchery = self.units(HATCHERY).ready.first
        larvae = self.units(LARVA)

        if iteration % 100 == 0:
            pprint(vars(self))

        if (iteration - self.overlord_started) >= overlord_build_time:
            self.building_overlord = False

        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")

        if iteration == 666:
            await self.chat_send("666 HELLFIRE")

        if self.supply_left < 3 and not self.building_overlord:
            if self.can_afford(OVERLORD) and larvae.exists:
                self.overlord_started = iteration
                self.building_overlord = True
                await self.do(larvae.random.train(OVERLORD))

        if self.drone_counter < 5:
            if self.can_afford(DRONE) and self.supply_left >= 1 and larvae.exists:
                self.drone_counter += 1
                await self.do(larvae.random.train(DRONE))

        if not self.units(SPAWNINGPOOL) and not self.already_pending(SPAWNINGPOOL):
            if self.can_afford(SPAWNINGPOOL):
                worker = self.select_build_worker(hatchery, force=True)
                await self.build(SPAWNINGPOOL, hatchery, unit=worker)
