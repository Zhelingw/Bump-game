import random


class Hand:
    "the class that represents the hands of a player"

    numbers: list = [1, 1]
    " the numbers of the two hands "

    def __init__(self):
        "initializes a hand which starts with 1 and 1"
        self.numbers = [1, 1]

    def _addition(self, self_num: int, opponent_num: int) -> int:
        """private method to add together the numbers to be bumped
        according to Bump's rules"""

        total = self_num + opponent_num
        if total < 10:
            return total
        elif total > 10:
            return total - 10
        else:
            return 0

    def bump(self, self_hand: int, opponent, opponent_hand: int) -> list:
        "function that bumps the numbers"

        changed_num = self._addition(
            self.numbers[self_hand], opponent.numbers[opponent_hand]
        )
        self.numbers[self_hand] = changed_num
        return self.numbers

    def copy(self):
        """function that allows hands to be copied to not change the original value;
        returns a Hand"""

        new_hand = Hand()
        new_hand.numbers = self.numbers.copy()
        return new_hand

    def choose_hand(self) -> int:
        "randomly chooses a hand"
        active_hands = [i for i, num in enumerate(self.numbers) if num != 0]
        if not active_hands:
            return None
        return random.choice(active_hands)

    def random_move(self, opponent) -> None:
        "performs random move, and bumps the hands"

        self_hand = self.choose_hand()
        opponent_hand = opponent.choose_hand()
        if self_hand is not None and opponent_hand is not None:
            self.bump(self_hand, opponent, opponent_hand)


class Game:
    "class that manages a session of bump game"

    def __init__(self, p1, p2):
        "initializes a Game instance with two players"
        self.player1 = p1
        self.player2 = p2

    def display_players(self) -> None:
        """displays current player statuses;
        this is only used in the first prototype and not in the final product"""

        print(
            f"\nnow: \nplayer 1 status: {self.player1.numbers} \nplayer 2 status: {self.player2.numbers}"
        )

    def prompt(self, player: Hand, opponent: Hand) -> list:
        """asks for the player's hands inputs;
        this is only used in the first prototype and not in the final product"""

        hand_check = False
        while not hand_check:
            print(
                "please pick your hand to bump (enter 0 for left hand or 1 for right hand): "
            )
            temp = input().strip()
            if temp not in ["0", "1"]:
                print("please enter 0 or 1!")
            else:
                self_hand = int(temp)
                if player.numbers[self_hand] == 0:
                    print("this hand is gone! please choose another one!")
                else:
                    hand_check = True

        hand_check = False
        while not hand_check:
            print("please pick your opponent's hand to be bumped: ")
            temp = input().strip()
            if temp not in ["0", "1"]:
                print("please enter 0 or 1!")
            else:
                opponent_hand = int(temp)
                if opponent.numbers[opponent_hand] == 0:
                    print("this hand is gone! please choose another one!")
                else:
                    hand_check = True

        return [self_hand, opponent_hand]

    def alert_hand(self, player: Hand) -> None:
        "checks whether player misses a hand"

        if player.numbers[0] == 0:
            print("your left hand is gone!")
        if player.numbers[1] == 0:
            print("your right hand is gone!")

    def system_turn_basic(self, sys: Hand, opponent: Hand) -> list:
        """proof of concept in the prototype;
        this is only used in the first prototype and not in the final product"""

        def choose_hand(player) -> int:
            if player.numbers[0] == 0:
                return 1
            elif player.numbers[1] == 0:
                return 0
            else:
                return random.randrange(0, 2)

        self_hand = choose_hand(sys)
        opponent_hand = choose_hand(opponent)
        sys.bump(self_hand, opponent, opponent_hand)
        print(f"system bumped its hand {self_hand} with your hand {opponent_hand}")
        return sys

    def _simulate(
        self, simulations: int, sys: Hand, opponent: Hand, level: int = 0
    ) -> list[int, int]:
        """internal method that performs Monte-Carlo simulations for the difficulty levels"""

        wins = [[0, 0], [0, 0]]
        win_count = 0
        for i in range(simulations):
            tie_counter = 0
            move_counter = 0

            # making a backup to not change the original hands' values
            sys_copy: Hand = sys.copy()
            opponent_copy: Hand = opponent.copy()
            self_hand: int = sys_copy.choose_hand()
            opponent_hand: int = opponent_copy.choose_hand()

            if self_hand is not None and opponent_hand is not None:
                sys_copy.bump(self_hand, opponent_copy, opponent_hand)

            # randomly move until the game ends, which is judged by the rules of Bump
            while not self.won(sys_copy) and not self.won(opponent_copy):
                move_counter += 1
                if move_counter > 500:
                    break
                opponent_copy.random_move(sys_copy)
                if self.won(sys_copy) or self.won(opponent_copy):
                    break
                sys_copy.random_move(opponent_copy)
                if self.won(sys_copy) or self.won(opponent_copy):
                    break

                # ensuring that the game doesn't reach a tie and run forever
                if (
                    sys_copy.numbers[0] + sys_copy.numbers[1] == 1
                    and opponent_copy.numbers[0] + opponent_copy.numbers[1] == 1
                ):
                    tie_counter += 1
                    if tie_counter > 20:
                        break

            # counting in favor of system for moderate and hard mode
            if not level and self.won(sys_copy):
                wins[self_hand][opponent_hand] += 1
                win_count += 1
            # counting in favor of player for easy mode (which sets level = 1)
            elif level and self.won(opponent_copy):
                wins[self_hand][opponent_hand] += 1
                win_count += 1

        # looking for the best move to return
        max_wins = -1
        best_move = [0, 0]
        for i in range(2):
            for j in range(2):
                if wins[i][j] > max_wins:
                    max_wins = wins[i][j]
                    best_move = [i, j]

        # line below can be used to check the results of the simulation
        # print(f"number of simulated wins: {win_count}, with number of simulated loses: {simulations - win_count}")
        return best_move

    def system_turn_easy(self, sys, opponent) -> None:
        "simulates 10 times for an easy game"
        self_hand, opponent_hand = self._simulate(
            10, sys, opponent, level=1
        )  # to make the algorithm be very simple
        sys.bump(self_hand, opponent, opponent_hand)
        # line below outputs the system's actions in the prototype
        print(f"system bumped its hand {self_hand} with your hand {opponent_hand}!")
        return sys

    def system_turn_moderate(self, sys, opponent) -> None:
        "simulates 50 times for an easy game"
        self_hand, opponent_hand = self._simulate(50, sys, opponent)
        sys.bump(self_hand, opponent, opponent_hand)
        # line below outputs the system's actions in the prototype
        print(f"system bumped its hand {self_hand} with your hand {opponent_hand}!")
        return sys

    def system_turn_hard(self, sys, opponent) -> None:
        "simulates 500 times for an easy game"
        self_hand, opponent_hand = self._simulate(500, sys, opponent)
        sys.bump(self_hand, opponent, opponent_hand)
        # line below outputs the system's actions in the prototype
        print(f"system bumped its hand {self_hand} with your hand {opponent_hand}!")
        return sys

    def won(self, player: Hand) -> bool:
        "checks whether either player has won"
        return player.numbers[0] == 0 and player.numbers[1] == 0


def play(level: int) -> None:
    "runs the whole game using Hand and Game classes"

    print("Welcome to Bump! ")

    player1 = Hand()
    system = Hand()
    game = Game(player1, system)
    brain = [game.system_turn_easy, game.system_turn_moderate, game.system_turn_hard][
        level
    ]

    while not game.won(player1) and not game.won(system):
        game.display_players()

        # Player 1's turn
        print("\nPlayer's turn!")
        prompt = game.prompt(player1, system)
        player1.bump(prompt[0], system, prompt[1])
        game.alert_hand(player1)

        if game.won(player1):
            print("Player wins!")
            break

        game.display_players()

        # Player 2's turn
        print("\nSystem's turn!")

        system = brain(system, player1)

        if game.won(system):
            print("System wins!")
            break


# Run the play function
play(level=2)
