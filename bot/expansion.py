
if self.can_afford(HATCHERY) and larvae.exists and self.hatchery_counter < 5:
    location = await self.get_next_expansion()
    await self.build(HATCHERY, location)
