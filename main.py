import fastapi
import uvicorn
import random
import time

global games

games = {}


class Game:
    def __init__(self):
        self.players = {}  # "id": [name, color, pos, charge, range, health, vote]
        self.existing_ids = []
        self.host = 0
        self.positions = []
        self.game_state = False
        self.board = []
        self.last_update = 0
        self.start_time = 0
        self.settings = {"board_size": [5, 5],  # vert, hor
                         "round_duration": 0,
                         "jury_bonus_count": 1,
                         "jury_bonus": 1,
                         "visible_range": False,
                         "visible_vote": True}
        self.password = int(random.random() * 100000)

    def authenticate(self, identification):
        if identification in self.existing_ids:
            return True
        else:
            return False

    ####################################################################################################################
    # player functions

    def add_host(self, name, color):
        self.host = random.randint(100000000, 999999999)
        self.players[self.host] = [name, color, [-1, -1], 0, 2, 3, None]
        self.existing_ids.append(self.host)
        return self.host

    def add_player(self, name, color):
        if self.game_state:
            return False
        else:
            while True:
                player_id = random.randint(100000000, 999999999)
                if player_id not in self.existing_ids:
                    break
            self.players[player_id] = [name, color, [-1, -1], 0, 2, 3, None]
            self.existing_ids.append(player_id)

            player_datas = []

            for player in self.players:
                player_datas.append([self.players[player][0], self.players[player][1]])

            return player_id, player_datas


    def move(self, player_id, new_position):
        if self.game_state:
            self.players[player_id][2] = new_position
            return True
        else:
            return False

    def shoot(self, shooting_player_id, hitting_player_id):
        if self.game_state:
            self.players[shooting_player_id][3] -= 1
            self.players[hitting_player_id][5] -= 1
            return True
        else:
            return False

    def transfer(self, shooting_player_id, hitting_player_id):
        if self.game_state:
            self.players[shooting_player_id][3] -= 1
            self.players[hitting_player_id][3] += 1
            return True
        else:
            return False

    def upgrade(self, upgrading_player_id):
        if self.game_state:
            self.players[upgrading_player_id][3] -= 3
            self.players[upgrading_player_id][4] += 1
            return True
        else:
            return False

    def vote(self, voting_player_id, target_player_id):
        if self.game_state:
            self.players[voting_player_id][6] = target_player_id
            return True
        else:
            return False

    ####################################################################################################################
    # turn functions

    def start(self, player_id, settings):  # creates board, set player position, initiate game
        if player_id != self.host:
            return False
        self.settings = settings
        self.game_state = 1
        for i in range(self.settings["board_size"][0]):
            temp = []
            for f in range(self.settings["board_size"][1]):
                temp.append(None)
            self.board.append(temp)

        for player in self.players:
            while True:
                position = [random.randint(0, self.settings["board_size"][0] - 1),
                            random.randint(0, self.settings["board_size"][1] - 1)]
                if position not in self.positions:
                    break
            self.positions.append(position)
            self.players[player][3] = position
            self.board[position[0]][position[1]] = self.players[player][0]
            self.players[player][4] = 1

        self.last_update = time.time()
        self.start_time = time.time()

        return True

    def update(self, player_id):
        if self.game_state:  # update round, players, info
            if self.start_time + (self.game_state * self.settings["round_duration"]) > 0:
                self.game_state += 1
                for player in self.players:
                    self.players[player][4] += 1

            returned_data = {}

            returned_players = []
            if self.settings["visible_range"]:
                if self.settings["visible_vote"]:
                    for player in self.players:
                        returned_players.append([self.players[player][0], self.players[player][1],
                                                 self.players[player][2], self.players[player][4],
                                                 self.players[player][5], self.players[player][6]])
                else:
                    for player in self.players:
                        returned_players.append([self.players[player][0], self.players[player][1],
                                                 self.players[player][2], self.players[player][4],
                                                 self.players[player][5]])
            else:
                if self.settings["visible_vote"]:
                    for player in self.players:
                        returned_players.append([self.players[player][0], self.players[player][1],
                                                 self.players[player][2], self.players[player][5],
                                                 self.players[player][6]])
                else:
                    for player in self.players:
                        returned_players.append([self.players[player][0], self.players[player][1],
                                                 self.players[player][2], self.players[player][5]])
            returned_data["players"] = returned_players

            returned_data["current_player"] = self.players[player_id]

            returned_data["state"] = [self.game_state, self.settings["round_duration"]]

            returned_data["settings"] = self.settings

            return returned_data  # all players, current player, other

        else:
            returned_data = []
            for player in self.players:
                returned_data.append(self.players[player][1:2])
            returned_data.append(self.settings["round_duration"])
            return returned_data


app = fastapi.FastAPI()


@app.post("/create_game")  # create_game
async def read_root(data: dict):
    game_id = int(random.random() * 100000)
    games[game_id] = Game()
    return [game_id, games[game_id].add_host(data["datas"][1], data["datas"][2])]


@app.post("/player/add_player")  # add_player
async def read_root(data: dict):
    try:
        returned = games[int(data["game"])].add_player(data["datas"][0], data["datas"][1])
    except KeyError:
        raise fastapi.HTTPException(status_code=404)
    if returned:
        return {"data": returned}
    else:
        raise fastapi.HTTPException(status_code=418)


@app.patch("/start_game")  # start_game
async def read_root(data: dict):
    if games[data["game"]].start(data["player_id"], data["settings"]):
        return True
    else:
        raise fastapi.HTTPException(status_code=401)


@app.get("/update")  # update
async def read_root(data: dict):
    if games[data["game"]].authenticate(data["player_id"]):
        return games[data["game"]].update(data["player_id"])
    else:
        raise fastapi.HTTPException(status_code=401)


@app.put("/player/move")  # move
async def read_root(data: dict):
    if games[data["game"]].authenticate(data["player_id"]):
        return games[data["game"]].move(data["player_id"], data["new_position"])
    else:
        raise fastapi.HTTPException(status_code=401)


@app.put("/player/shoot")  # shoot
async def read_root(data: dict):
    if games[data["game"]].authenticate(data["player_id"]):
        return games[data["game"]].shoot(data["shooter"], data["hitter"])
    else:
        raise fastapi.HTTPException(status_code=401)


@app.put("/player/transfer")  # transfer
async def read_root(data: dict):
    if games[data["game"]].authenticate(data["player_id"]):
        return games[data["game"]].transfer(data["shooter"], data["hitter"])
    else:
        raise fastapi.HTTPException(status_code=401)


@app.put("/player/upgrade")  # upgrade
async def read_root(data: dict):
    if games[data["game"]].authenticate(data["player_id"]):
        return games[data["game"]].upgrade(data["upgrading"])
    else:
        raise fastapi.HTTPException(status_code=401)


@app.put("/player/vote")  # vote
async def read_root(data: dict):
    if games[data["game"]].authenticate(data["player_id"]):
        return games[data["game"]].vote(data["voter"], data["receiver"])
    else:
        raise fastapi.HTTPException(status_code=401)


game_id = 0
games[game_id] = Game()
player_id = games[game_id].add_host("__self__", (0, 0, 0))
print(game_id, player_id)
'''
print(games[game_id].start(player_id, {"board_size": [5, 5],  # vert, hor
                               "round_duration": 0,
                               "jury_bonus_count": 1,
                               "jury_bonus": 1,
                               "visible_range": False,
                               "visible_vote": True}))
'''
uvicorn.run(app, host="127.0.0.1", port=4196)
