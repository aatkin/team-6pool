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
        self.overlord_started = 0

    async def on_step(self, iteration):
        larvae = self.units(LARVA)

        if iteration % 100 == 0:
            pprint(vars(self))

        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")

        if iteration == 666:
            await self.chat_send("666 HELLFIRE")

        if self.supply_left < 2 and self.drone_counter != 0:
            if self.can_afford(OVERLORD) and larvae.exists:
                self.overlord_started = iteration
                await self.do(larvae.random.train(OVERLORD))

        if self.drone_counter < 10:
            if self.can_afford(DRONE):
                self.drone_counter += 1
                await self.do(larvae.random.train(DRONE))
