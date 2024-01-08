from enum import Enum
from pprint import pprint
from typing import Any
import keyboard
from time import sleep
from os import system
from random import randint, choice


# Colors
class Color:

    """Colors class:reset all colors with colors.reset; two
    sub classes fg for foreground
    and bg for background; use as colors.subclass.colorname.
    i.e. colors.fg.red or colors.bg.greenalso, the generic bold, disable,
    underline, reverse, strike through,
    and invisible work with the main class i.e. colors.bold"""

    reset = "\033[0m"
    bold = "\033[01m"
    disable = "\033[02m"
    underline = "\033[04m"
    reverse = "\033[07m"
    strikethrough = "\033[09m"
    invisible = "\033[08m"

    class FG:
        black = "\033[30m"
        red = "\033[31m"
        green = "\033[32m"
        orange = "\033[33m"
        blue = "\033[34m"
        purple = "\033[35m"
        cyan = "\033[36m"
        lightgrey = "\033[37m"
        darkgrey = "\033[90m"
        lightred = "\033[91m"
        lightgreen = "\033[92m"
        yellow = "\033[93m"
        lightblue = "\033[94m"
        pink = "\033[95m"
        lightcyan = "\033[96m"

    class BG:
        black = "\033[40m"
        red = "\033[41m"
        green = "\033[42m"
        orange = "\033[43m"
        blue = "\033[44m"
        purple = "\033[45m"
        cyan = "\033[46m"
        lightgrey = "\033[47m"


def cprint(text: str, fg: Color.FG | str = "", bg: Color.BG | str = "") -> None:
    print(f"{fg}{bg}{text}{Color.reset}" if fg or bg else text)


# Enums
class Player(Enum):
    ONE = 1
    TWO = 2


class Ship(Enum):
    CARRIER = 5
    BATTLESHIP = 4
    CRUISER = 3
    SUBMARINE = 3
    DESTROYER = 2

    def __getattribute__(self, __name: str) -> Any:
        if __name == "SUBMARINE":
            return 3
        return super().__getattribute__(__name)


ship_names: dict[str, Ship] = {
    "Carrier": Ship.CARRIER,
    "Battleship": Ship.BATTLESHIP,
    "Cruiser": Ship.CRUISER,
    "Submarine": Ship.SUBMARINE,
    "Destroyer": Ship.DESTROYER,
}

opp_ship_names: dict[Ship, str] = {
    Ship.CARRIER: "Carrier",
    Ship.BATTLESHIP: "Battleship",
    Ship.CRUISER: "Cruiser",
    Ship.SUBMARINE: "Submarine",
    Ship.DESTROYER: "Destroyer",
}


class Direction(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class ShipState(Enum):
    EMPTY = 0
    INTACT = 1
    HIT = 2
    SUNK = 3
    WRONG_GUESS = 4


# Errors
class InvalidShipPlacementError(Exception):
    pass


class InvalidGuessError(Exception):
    pass


class Board:
    def __init__(self) -> None:
        self.player1: list[list[int]] = [
            [ShipState.EMPTY.value] * 10 for _ in range(10)
        ]
        self.player2: list[list[int]] = [
            [ShipState.EMPTY.value] * 10 for _ in range(10)
        ]

        self.player1_ships: dict[str, dict[str, list]] = {}
        self.player2_ships: dict[str, dict[str, list]] = {}

        self.player1_guesses: list[tuple[int, int]] = []
        self.player2_guesses: list[tuple[int, int]] = []

        self.player1_shots: int = 0
        self.player2_shots: int = 0

    def get_player_coords(self, player: Player) -> list[tuple[int, int]]:
        coords = []
        for ship in getattr(self, f"player{player.value}_ships"):
            for x, y in zip(
                getattr(self, f"player{player.value}_ships")[ship]["x"],
                getattr(self, f"player{player.value}_ships")[ship]["y"],
            ):
                coords.append((x, y))
        return coords

    @property
    def player1_coords(self) -> list[tuple[int, int]]:
        return self.get_player_coords(Player.ONE)

    @property
    def player2_coords(self) -> list[tuple[int, int]]:
        return self.get_player_coords(Player.TWO)

    @property
    def ai_x(self) -> list[tuple[int, int]]:
        # return coordinates of hit coordinates
        return [
            (x, y)
            for x in range(10)
            for y in range(10)
            if self.player1[y][x] == ShipState.HIT.value
        ]

    @property
    def all_ai_guesses(self) -> list[tuple[int, int]]:
        return [
            (x, y)
            for x in range(10)
            for y in range(10)
            if self.player1[y][x]
            in [ShipState.HIT.value, ShipState.SUNK.value, ShipState.WRONG_GUESS.value]
        ]

    @property
    def game_ended(self) -> bool:
        return all(
            getattr(self, f"player{player.value}_ships")[ship]["sunk"]
            for player in Player
            for ship in getattr(self, f"player{player.value}_ships")
        )

    def place_ship(
        self, player: Player, ship: str, x: int, y: int, direction: Direction
    ) -> None:
        # Error checking
        if ship in getattr(self, f"player{player.value}_ships"):
            raise InvalidShipPlacementError(
                f"Player {player.value} has already placed a {ship}"
            )

        if direction == Direction.HORIZONTAL and x + ship_names[ship].value > 10:
            raise InvalidShipPlacementError(
                f"Ship {ship} cannot be placed at {x}, {y} horizontally"
            )

        if direction == Direction.VERTICAL and y + ship_names[ship].value > 10:
            raise InvalidShipPlacementError(
                f"Ship {ship} cannot be placed at {x}, {y} vertically"
            )

        for ship_ in getattr(self, f"player{player.value}_ships"):
            for i, j in zip(
                getattr(self, f"player{player.value}_ships")[ship_]["x"],
                getattr(self, f"player{player.value}_ships")[ship_]["y"],
            ):
                if direction == Direction.HORIZONTAL:
                    ship_coords = [
                        (x_, y) for x_ in range(x, x + ship_names[ship].value)
                    ]
                    if any((i, j) == ship_coord for ship_coord in ship_coords):
                        raise InvalidShipPlacementError(
                            f"Ship {ship} cannot be placed at {x}, {y}"
                        )
                else:
                    ship_coords = [
                        (x, y_) for y_ in range(y, y + ship_names[ship].value)
                    ]
                    if any((i, j) == ship_coord for ship_coord in ship_coords):
                        raise InvalidShipPlacementError(
                            f"Ship {ship} cannot be placed at {x}, {y}"
                        )

        # Place ship
        getattr(self, f"player{player.value}_ships")[ship] = {
            "x": [x + i for i in range(ship_names[ship].value)]
            if direction == Direction.HORIZONTAL
            else [x] * ship_names[ship].value,
            "y": [y] * ship_names[ship].value
            if direction == Direction.HORIZONTAL
            else [y + i for i in range(ship_names[ship].value)],
            "sunk": False,
        }

        for i, j in zip(
            getattr(self, f"player{player.value}_ships")[ship]["x"],
            getattr(self, f"player{player.value}_ships")[ship]["y"],
        ):
            getattr(self, f"player{player.value}")[j][i] = ShipState.INTACT.value

    def display(
        self,
        player: Player,
        coord_range: list[tuple[int, int]] | None = None,
        guess: bool = False,
    ) -> None:
        if guess:
            print(f"Player {player.value}'s guesses:")
        else:
            print(f"Player {player.value}'s board:")
        cprint("  0 1 2 3 4 5 6 7 8 9", fg=Color.FG.lightblue)
        for i, row in enumerate(getattr(self, f"player{player.value}")):
            columns = ""
            for j, col in enumerate(row):
                prefix = ""
                if guess:
                    if coord_range and (i, j) in coord_range:
                        prefix = Color.FG.lightgreen
                    if col == ShipState.EMPTY.value:
                        columns += f"{prefix}•{Color.reset} "
                    elif col == ShipState.INTACT.value:
                        columns += f"{prefix}•{Color.reset} "
                    elif col == ShipState.HIT.value:
                        columns += f"{Color.FG.lightred}{prefix}X{Color.reset} "
                    elif col == ShipState.SUNK.value:
                        columns += f"{Color.FG.red}{prefix}S{Color.reset} "
                    elif col == ShipState.WRONG_GUESS.value:
                        columns += f"{Color.FG.cyan}{prefix}•{Color.reset} "
                else:
                    if coord_range and (i, j) in coord_range:
                        prefix = Color.FG.lightgreen
                    if col == ShipState.EMPTY.value:
                        columns += f"{prefix}•{Color.reset} "
                    elif col == ShipState.INTACT.value:
                        columns += f"{Color.FG.yellow}{prefix}O{Color.reset} "
                    elif col == ShipState.HIT.value:
                        columns += f"{Color.FG.lightred}{prefix}X{Color.reset} "
                    elif col == ShipState.SUNK.value:
                        columns += f"{Color.FG.red}{prefix}S{Color.reset} "
                    elif col == ShipState.WRONG_GUESS.value:
                        columns += f"{Color.FG.cyan}{prefix}•{Color.reset} "
            print(f"{Color.FG.lightblue}{i}{Color.reset} {columns}")

    def place_player_ships(self, player: Player) -> None:
        direction = Direction.HORIZONTAL

        def min_max_x_y(direction: Direction, value: Ship) -> tuple[int, int, int, int]:
            min_x = 0
            max_x = 9 - (value.value - 1) if direction == Direction.HORIZONTAL else 9
            min_y = 0
            max_y = 9 - (value.value - 1) if direction == Direction.VERTICAL else 9
            return min_x, max_x, min_y, max_y

        for ship, value in ship_names.items():
            direction = Direction.HORIZONTAL
            leftmost: tuple[int, int] = (0, 0)
            min_x, max_x, min_y, max_y = min_max_x_y(direction, value)
            placed = False
            while not placed:
                print("\n" * 20)
                cprint("Welcome to Battleship!", fg=Color.FG.yellow)
                print(f"Player {int(player.value)}, place your ships:")
                print(f"Place your {ship} ({value.value} spaces)")
                self.display(
                    player,
                    [(leftmost[0], leftmost[1] + i) for i in range(value.value)]
                    if direction == Direction.HORIZONTAL
                    else [(leftmost[0] + i, leftmost[1]) for i in range(value.value)],
                )
                while True:
                    sleep(0.2)
                    key = keyboard.read_key()
                    if isinstance(key, str):
                        key = key.lower()
                    match key:
                        case "v":
                            direction = Direction.VERTICAL
                            min_x, max_x, min_y, max_y = min_max_x_y(direction, value)
                            leftmost = (
                                min(max_y, leftmost[0]),
                                min(max_x, leftmost[1]),
                            )
                            break
                        case "h":
                            direction = Direction.HORIZONTAL
                            min_x, max_x, min_y, max_y = min_max_x_y(direction, value)
                            leftmost = (
                                min(max_y, leftmost[0]),
                                min(max_x, leftmost[1]),
                            )
                            break
                        case "w":
                            leftmost = (max(min_y, leftmost[0] - 1), leftmost[1])
                            break
                        case "a":
                            leftmost = (leftmost[0], max(min_x, leftmost[1] - 1))
                            break
                        case "s":
                            leftmost = (min(max_y, leftmost[0] + 1), leftmost[1])
                            break
                        case "d":
                            leftmost = (leftmost[0], min(max_x, leftmost[1] + 1))
                            break
                        case "enter":
                            try:
                                self.place_ship(
                                    player,
                                    ship,
                                    leftmost[1],
                                    leftmost[0],
                                    direction,
                                )
                                placed = True
                            except InvalidShipPlacementError as e:
                                print(e)
                                continue
                            break

    def change_state(self, player: Player, coord: tuple[int, int]) -> None:
        if coord in getattr(self, f"player{player.value}_guesses"):
            raise InvalidGuessError(
                f"Player {player.value} has already guessed {coord}"
            )
        for ship in getattr(self, f"player{player.value}_ships"):
            for x, y in zip(
                getattr(self, f"player{player.value}_ships")[ship]["x"],
                getattr(self, f"player{player.value}_ships")[ship]["y"],
            ):
                if (y, x) == coord:
                    if (
                        getattr(self, f"player{player.value}")[y][x]
                        == ShipState.HIT.value
                    ):
                        raise InvalidGuessError(
                            f"Player {player.value} has already guessed {coord} HIT"
                        )
                    getattr(self, f"player{player.value}")[y][x] = ShipState.HIT.value
                    if all(
                        getattr(self, f"player{player.value}")[y][x]
                        == ShipState.HIT.value
                        for x, y in zip(
                            getattr(self, f"player{player.value}_ships")[ship]["x"],
                            getattr(self, f"player{player.value}_ships")[ship]["y"],
                        )
                    ):
                        print(f"Player {player.value} sunk {ship}")
                        for x, y in zip(
                            getattr(self, f"player{player.value}_ships")[ship]["x"],
                            getattr(self, f"player{player.value}_ships")[ship]["y"],
                        ):
                            getattr(self, f"player{player.value}")[y][
                                x
                            ] = ShipState.SUNK.value
                        getattr(self, f"player{player.value}_ships")[ship][
                            "sunk"
                        ] = True
                        if all(
                            getattr(self, f"player{player.value}_ships")[ship]["sunk"]
                            for ship in getattr(self, f"player{player.value}_ships")
                        ):
                            print(f"Player {player.value} wins!")
                            # exit(0)
                            return
                    return
        getattr(self, f"player{player.value}")[coord[0]][
            coord[1]
        ] = ShipState.WRONG_GUESS.value

    def place_player_guess(self) -> None:
        coord: tuple[int, int] = (0, 0)
        placed = False
        while not placed:
            print("\n" * 20)
            cprint("Welcome to Battleship!", fg=Color.FG.yellow)
            print("Your board:")
            self.display(Player.ONE)
            print(f"Player 1, place your guess:")
            # self.display(Player.TWO)  # remove
            self.display(
                Player.TWO,
                [coord],
                guess=True,
            )
            while True:
                sleep(0.2)
                key = keyboard.read_key()
                if isinstance(key, str):
                    key = key.lower()
                match key:
                    case "w":
                        coord = (max(0, coord[0] - 1), coord[1])
                        break
                    case "a":
                        coord = (coord[0], max(0, coord[1] - 1))
                        break
                    case "s":
                        coord = (min(9, coord[0] + 1), coord[1])
                        break
                    case "d":
                        coord = (coord[0], min(9, coord[1] + 1))
                        break
                    case "enter":
                        try:
                            self.change_state(Player.TWO, coord)
                            self.player1_shots += 1
                            placed = True
                        except InvalidGuessError as e:
                            print(e)
                            continue
                        break

    def place_ai_guess(self) -> None:
        coord: tuple[int, int] = (0, 0)
        placed = False

        def approach() -> tuple[int, int]:
            # get a random adjacent coordinate
            x, y = choice(self.ai_x)
            coord = (x, y)
            num_attempted = 0
            while (
                coord in self.all_ai_guesses
                or coord[0] < 0
                or coord[0] > 9
                or coord[1] < 0
                or coord[1] > 9
            ):
                if num_attempted > 10:
                    # get a random coordinate
                    coord = (randint(0, 9), randint(0, 9))
                    break
                which = choice([0, 1])
                if which == 0:
                    coord = (
                        x + choice([-1, 1]),
                        y,
                    )
                elif which == 1:
                    coord = (
                        x,
                        y + choice([-1, 1]),
                    )
                num_attempted += 1
            return coord

        while not placed:
            if not self.ai_x:
                coord = (randint(0, 9), randint(0, 9))
            else:
                print(f"{self.ai_x=}")
                if len(self.ai_x) == 1:
                    coord = approach()

                else:
                    coords_in_v_line: list[tuple[int, int]] = []
                    coords_in_h_line: list[tuple[int, int]] = []
                    for x, y in self.ai_x:
                        if x == self.ai_x[0][0]:
                            coords_in_v_line.append((x, y))
                    for x, y in self.ai_x:
                        if y == self.ai_x[0][1]:
                            coords_in_h_line.append((x, y))
                    if len(coords_in_v_line) > 1:
                        # get the top or bottom coordinate of a random coordinate in the vertical line
                        coord = (-1, -1)
                        num_attempted = 0
                        while (
                            coord in self.all_ai_guesses
                            or coord[0] < 0
                            or coord[0] > 9
                            or coord[1] < 0
                            or coord[1] > 9
                        ):
                            if num_attempted > 10:
                                coord = approach()
                            x, y = choice(coords_in_v_line)
                            coord = (
                                x,
                                y + choice([-1, 1]),
                            )
                            num_attempted += 1
                    elif len(coords_in_h_line) > 1:
                        # get the left or right coordinate of a random coordinate in the horizontal line
                        coord = (-1, -1)
                        num_attempted = 0
                        while (
                            coord in self.all_ai_guesses
                            or coord[0] < 0
                            or coord[0] > 9
                            or coord[1] < 0
                            or coord[1] > 9
                        ):
                            if num_attempted > 10:
                                coord = approach()
                            x, y = choice(coords_in_h_line)
                            coord = (
                                x + choice([-1, 1]),
                                y,
                            )
                            num_attempted += 1
                    else:
                        # get a random adjacent coordinate
                        x, y = self.ai_x[0]
                        coord = (x, y)
                        num_attempted = 0
                        while (
                            coord in self.all_ai_guesses
                            or coord[0] < 0
                            or coord[0] > 9
                            or coord[1] < 0
                            or coord[1] > 9
                        ):
                            if num_attempted > 10:
                                coord = approach()
                            which = choice([0, 1])
                            if which == 0:
                                coord = (
                                    x + choice([-1, 1]),
                                    y,
                                )
                            elif which == 1:
                                coord = (
                                    x,
                                    y + choice([-1, 1]),
                                )
                            num_attempted += 1

            try:
                coord = (coord[1], coord[0])
                self.change_state(Player.ONE, coord)
                self.player2_shots += 1
                print("Placed", coord)
                placed = True
            except InvalidGuessError:
                continue

    def place_ai_ships(self) -> None:
        def min_max_x_y(direction: Direction, value: Ship) -> tuple[int, int, int, int]:
            min_x = 0
            max_x = 9 - (value.value - 1) if direction == Direction.HORIZONTAL else 9
            min_y = 0
            max_y = 9 - (value.value - 1) if direction == Direction.VERTICAL else 9
            return min_x, max_x, min_y, max_y

        for ship, value in ship_names.items():
            direction = choice([Direction.HORIZONTAL, Direction.VERTICAL])
            leftmost: tuple[int, int] = (0, 0)
            min_x, max_x, min_y, max_y = min_max_x_y(direction, value)
            placed = False
            while not placed:
                leftmost = (randint(min_x, max_x), randint(min_y, max_y))
                try:
                    self.place_ship(
                        Player.TWO,
                        ship,
                        leftmost[1],
                        leftmost[0],
                        direction,
                    )
                    placed = True
                except InvalidShipPlacementError:
                    continue

    def main(self):
        self.place_player_ships(Player.ONE)
        self.place_ai_ships()

        print("\n" * 20)
        cprint("Welcome to Battleship!", fg=Color.FG.yellow)
        while not self.game_ended:
            self.place_player_guess()
            self.place_ai_guess()
            print(self.ai_x)
            print(self.player1_guesses)
            print(self.player2_guesses)

        print(
            f"Shots fired:\nPlayer 1 (human): {self.player1_shots}\nPlayer 2 (AI): {self.player2_shots}"
        )


board = Board()

board.main()
