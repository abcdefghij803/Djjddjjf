# database.py
from motor.motor_asyncio import AsyncIOMotorClient

DEFAULT_USER = {"nft": 0, "stars": 0, "gifts": 0, "premium": False, "string_session": None}

class Database:
    def __init__(self, url):
        self.client = AsyncIOMotorClient(url)
        self.db = self.client["transferdb"]
        self.users = self.db["users"]

    async def ensure_user(self, user_id: int):
        doc = await self.users.find_one({"user_id": user_id})
        if not doc:
            data = {"user_id": user_id, **DEFAULT_USER}
            await self.users.insert_one(data)
            return data
        return doc

    async def get_user(self, user_id: int):
        return await self.ensure_user(user_id)

    async def set_session(self, user_id: int, session: str):
        await self.ensure_user(user_id)
        return await self.users.update_one({"user_id": user_id}, {"$set": {"string_session": session}})

    async def change_asset(self, user_id: int, asset: str, amount: int):
        await self.ensure_user(user_id)
        return await self.users.update_one({"user_id": user_id}, {"$inc": {asset: amount}})

    async def set_premium(self, user_id: int, value: bool):
        await self.ensure_user(user_id)
        return await self.users.update_one({"user_id": user_id}, {"$set": {"premium": value}})

    async def transfer_asset(self, from_id: int, to_id: int, asset: str, amount: int = 1):
        sender = await self.get_user(from_id)
        if asset == "premium":
            if not sender.get("premium", False):
                return False
            await self.set_premium(from_id, False)
            await self.set_premium(to_id, True)
            return True

        if sender.get(asset, 0) < amount:
            return False

        await self.change_asset(from_id, asset, -amount)
        await self.change_asset(to_id, asset, amount)
        return True
