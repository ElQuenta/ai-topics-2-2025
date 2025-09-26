import csv
import io
import random
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel

class RaceEnum(str, Enum):
    orc = "ORC"
    elf = "ELF"
    human = "HUMAN"
    goblin = "GOBLIN"

class Guild(BaseModel):
    id: int
    name: str
    realm: str
    created: datetime

class Character(BaseModel):
    id: int
    name: str
    level: int
    race: RaceEnum
    hp: int
    damage: int | None = None  # opcional
    guild: Guild

class CharacterCreate(BaseModel):
    name: str
    level: int
    race: RaceEnum
    hp: int
    damage: int | None = None
    guild_id: int

app = FastAPI(title="validacion")

guilds: list[Guild] = []
characters: list[Character] = []

@app.post("/guilds", status_code=201)
def create_guild(guild: Guild) -> list[Guild]:
    guilds.append(guild)
    return guilds

@app.post("/characters", status_code=201)
def create_character(character: CharacterCreate):
    id_ = random.randint(0, 9999)
    guilds_found = [g for g in guilds if g.id == character.guild_id]
    if not guilds_found:
        raise HTTPException(status_code=404, detail="guild not found")
    guild = guilds_found[0]
    new_character = Character(id=id_, guild=guild, **character.model_dump(exclude=["guild_id"]))
    characters.append(new_character)
    return characters

@app.get("/reports/guilds", responses={200: {"content": {"text/csv": {}}}})
def download_guilds_report() -> Response:
    fieldnames = ["id", "name", "realm", "created"]
    csv_stream = io.StringIO()
    writer = csv.DictWriter(csv_stream, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    for g in guilds:
        created = g.created.isoformat() if isinstance(g.created, datetime) else str(g.created)
        writer.writerow({
            "id": g.id,
            "name": g.name,
            "realm": g.realm,
            "created": created,
        })

    text = csv_stream.getvalue()
    headers = {"Content-Disposition": 'attachment; filename="guilds.csv"'}
    return Response(content=text, media_type="text/csv", headers=headers)

@app.get("/reports/characters", responses={200: {"content": {"text/csv": {}}}})
def download_characters_report() -> Response:
    fieldnames = ["id", "name", "level", "race", "hp", "damage", "guild_id", "guild_name"]
    csv_stream = io.StringIO()
    writer = csv.DictWriter(csv_stream, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()

    for c in characters:
        writer.writerow({
            "id": c.id,
            "name": c.name,
            "level": c.level,
            "race": c.race.value if isinstance(c.race, Enum) else c.race,
            "hp": c.hp,
            "damage": "" if c.damage is None else c.damage,
            "guild_id": c.guild.id,
            "guild_name": c.guild.name,
        })

    text = csv_stream.getvalue()
    headers = {"Content-Disposition": 'attachment; filename="characters.csv"'}
    return Response(content=text, media_type="text/csv", headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("models_files_api:app", reload=True, port=8008)
