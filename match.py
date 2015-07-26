#!/usr/bin/env python

__author__ = 'jlyman'

# TOURNAMENT MATCHUP APPLICATION
# Simulates 1-on-1 matchups and swiss ranked matches. Queries a pgSQL database
# for match and player information.

# ordering imports alphabetically is good a good pythonism.

import argparse as arg
import config as cfg
import database as db
from decimal import Decimal
from prettytable import PrettyTable
import random
import re
import sys
import time
import tools


def check_version(sys_version):
    if sys_version < (2, 7):
        message = "Version out of spec."
        print message
        time.sleep(3.0)  # long enough, I think.
        verstat = 1
    else:
        verstat = 0
    return verstat


# PLAYER ORIENTED FUNCTIONS #


# Create a new player based on their name and country of origin.
def new_player(player_name="", country=""):
    if re.search('[0-9]', player_name):
        raise AttributeError("Player name is invalid (contains numbers)")
    if len(player_name) < 2:
        raise AttributeError("Player name is less than 2 characters.")
    if " " not in player_name:
        raise AttributeError("Player name is invalid. (missing surname)")
    if re.search('[!@#$%^&*\(\)~`+=]', player_name):
        raise AttributeError("Player name is invalid. (contains symbol(s))")
    tools.logger("Received player name " + player_name, "new_player()")
    print "Please enter the player's Country of Origin: "
    if not country:
        country = raw_input("Country of Origin: ")
    tools.logger("Received player country " + country, "new_player()")
    print "Creating new entry for %s from %s" % (player_name, country)
    code = player_name[:4].lower() + str(random.randrange(1000001, 9999999))
    start = time.time()
    db.register_player(player_name, country, code)
    stop = time.time()
    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    print "Successfully created new entry in %s seconds" % dur[:5]
    tools.logger("Database entry created for " + player_name + " from " +
                 country + ".",
                 "new_player()")
    return 0


# Delete an existing player based on their ID.
def edit_player(option="", player="", new_name="", new_country=""):
    if option == "delete":
        start = time.time()
        search = db.search("players", "ID", player)
        if not search:
            raise AttributeError("Invalid Player ID.")
        db.delete_player(player)
        tools.logger("Deleted %s from the database" % player, "edit_player()")
        stop = time.time()
    elif option == "edit":
        if not (new_name and new_country):
            raise AttributeError("EDIT chosen, but new info not given.")
        player_name = new_name
        player_country = new_country
        start = time.time()
        search = db.search("players", "ID", player)
        if not search:
            raise AttributeError("Invalid Player ID.")
        db.update_player(player, player_name, player_country)
        tools.logger("Updated %s." % player, "edit_player()")
        stop = time.time()
    else:
        raise AttributeError("OPTION Not Supported: '%s'" % option)

    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    print "Complete. Operation took %s seconds." % dur[:5]
    return 0


# Get a list of players based on criteria and display method.
def list_players():
    count = 0
    print "List All Players."
    print "Here's a list of all players in the database: "
    print "=============================================="
    tools.logger("Requesting all players in the database.", "list_players()")
    start = time.time()
    results = db.search("players", "ALL", "null")
    # table = PrettyTable(['#', 'Unique ID', 'Name', 'Country', 'Wins'])
    table = PrettyTable(['#', 'Unique ID', 'Name', 'Country', 'Code'])
    table.align = "l"
    for row in results:
        count += 1
        # wins = db.count_wins(row[3])
        # for win in wins:
        #     wincount = win[0]
        # table.add_row([count, row[0], row[1], row[2], wincount])
        table.add_row([count, row[0], row[1], row[2], row[3]])
    print table
    stop = time.time()

    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    tools.logger(("Returned %i results in %s seconds" % (count, dur[:5])),
                 "list_players()")
    print "Returned %s results in %s seconds" % (count, dur[:5])
    return 0


# MATCH ORIENTED FUNCTIONS #


# Initiate a match. Player_1 and Player_2 should be IDs.
def go_match(match_type="REG", player_1="", player_2=""):
    player_1_code = ''
    player_2_code = ''
    player_1_name = ''
    player_2_name = ''
    if match_type == "REG":
        if not player_1:
            player_1 = raw_input("ID# for Player 1: ")
        if not player_2:
            player_2 = raw_input("ID# for Player 2: ")
    tools.logger("Starting match between " + player_1 + " and " + player_2,
                 "go_match()")
    code_lookup = db.search("players", "ID", player_1)
    for row in code_lookup:
        player_1_code = row[3]
        player_name = db.search("players", "CODE", player_1_code)
        for result in player_name:
            player_1_name = result[1]
    code_lookup = db.search("players", "ID", player_2)
    for row in code_lookup:
        player_2_code = row[3]
        player_name = db.search("players", "CODE", player_2_code)
        for result in player_name:
            player_2_name = result[1]
    print "Match between %s and %s" % (player_1_name, player_2_name)
    if (not player_1_name) or (not player_2_name):
        raise ValueError("One of the two players you entered doesn't exist.")
    # Randomly pick between one or two.
    random_int = random.randrange(1, 3)
    tools.logger("Generated random number " + str(random_int), "go_match()")
    # If the random number is even: player 1 wins. Else: player 2 wins.
    if random_int == 2:
        # the random number is even:
        print player_1_name + " wins!"
        tools.logger("Stated that player 1 wins.", "go_match()")
        winner = player_1_code
    else:
        # the random number is odd:
        print "Player " + player_2_name + " wins!"
        tools.logger("Stated that player 2 wins.", "go_match()")
        winner = player_2_code
    db.report_match(winner, player_1, player_2)
    tools.logger("Reported win to database.", "go_match()")
    print "Finished."
    return 0


# match up each of the players in the database and swiss-ify them.
def swiss_match():
    bye = ''
    round_number = 0
    start = time.time()
    players_list1 = db.count_players()
    # Count the number of players in the list
    count = len(players_list1)
    tools.logger("Found %i players in list for swiss matchups." % count,
                 "swiss_match()")
    # If there isn't an even amount:
    if count % 2:
        tools.logger("Popping off the odd player (#%i) out." % count,
                     "swiss_match()")
        # simple math.
        bye = players_list1[count - 1]
        players_list1.pop(count - 1)
    # Since it's technically pure coincidence that the entries were in order,
    # we need to explicitly sort them. Defaults to the ID for sorting as it's
    # the first non-symbol in each entry.
    players_list1 = sorted(players_list1)
    # Flip the second dict; faster than using the reversed() builtin.
    players_list2 = sorted(players_list1, reverse=True)
    print "The matchups are as follows:"

    table_master = PrettyTable(["TEAM A", "TEAM B"])
    table_master.align = "c"
    table_master.hrules = False
    table_master.vrules = True
    table_master.left_padding_width = 0
    table_master.right_padding_width = 0
    tools.logger("Generated MASTER table for display.", "swiss_match()")
    table_slave_a = PrettyTable(["#", "NAME", "COUNTRY"])
    table_slave_a.align = "l"
    table_slave_a.border = False
    for a in players_list1:
        table_slave_a.add_row([a[0], a[1], a[2]])
    if bye:
        table_slave_a.add_row([bye[0], bye[1], bye[2]])
    tools.logger("Generated SLAVE A table for display.", "swiss_match()")
    table_slave_b = PrettyTable(["#", "NAME", "COUNTRY"])
    table_slave_b.align = "l"
    table_slave_b.border = False
    for b in players_list2:
        table_slave_b.add_row([b[0], b[1], b[2]])
    if bye:
        table_slave_b.add_row(["--", "------BYE------", "--------"])
    tools.logger("Generated SLAVE B table for display.", "swiss_match()")
    table_master.add_row([table_slave_a, table_slave_b])
    tools.logger("Generated COMPLETE table for display", "swiss_match()")
    print table_master
    stop = time.time()
    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    print "Complete. Operation took %s seconds." % dur[:5]
    run_swiss_matchup = raw_input("Do you want to run matches through this "
                                  "list of players?\n(Keep in mind: A "
                                  "player in BYE will not be run) [Y/n]")

    while run_swiss_matchup in ["Yes", "Y", "y"]:
        tools.logger("User opted to run matches against swiss matchups.",
                     "swiss_match()")
        # smoosh (technical term) the two lists together and make them fight
        # for their dinner!
        start = time.time()
        for a, b in zip(players_list1, players_list2):
            round_number += 1
            print "Round %i..." % round_number
            tools.logger("Initiating round %i against go_match()" %
                         round_number, "swiss_match()")
            go_match(match_type="SWISS", player_1=str(a[0]), player_2=str(b[0]))
            tools.logger("Completed round %i against go_match()" %
                         round_number, "swiss_match()")
            print "Round %i complete.\n" % round_number
        stop = time.time()
        dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                        rounding="ROUND_UP"))
        print "Complete. Operation took %s seconds." % dur[:5]
        break  # remove if you're psycho.
    else:
        tools.logger("User opted to not run matches against swiss matchups.",
                     "swiss_match()")
        print "User neglected to run matches."
    print "Swiss matchups complete."
    # cake.
    # profit.
    # THE CAKE IS A LIE.
    return 0


# Delete an existing match
def delete_match(match=""):
    count = 0
    if not match:
        raise ValueError("An ID # is required.")
    start = time.time()
    db.delete_match(match)
    tools.logger("Deleted match %s from the database" % match,
                 "delete_match()")
    stop = time.time()

    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    print "Complete. Operation took %s seconds." % dur[:5]
    return 0


# Display all historical matches.
def list_matches():
    count = 0
    tools.logger("Listing all matches.", "list_matches()")
    print "List All Matches"
    # display all matches in the matches table, (in groups of ten,
    # with names, eventually).
    start = time.time()
    results = db.search("matches", "ALL", "null")

    table = PrettyTable(['#', 'ID#', 'P1 ID', 'P2 ID', 'WINNER', 'TIME'])
    table.align = 'l'
    for row in results:
        count += 1
        player = db.search("players", "CODE", row[3])
        for entry in player:
            name = entry[1]
        if name == '':
            name = "[PLAYER DELETED]"
        table.add_row([count, row[0], row[1], row[2], name, row[4]])
    print table
    stop = time.time()
    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    tools.logger(("Returned %i results in %s seconds" % (count, dur[:5])),
                 "list_matches")
    print "Returned %s results in %s seconds" % (count, dur[:5])
    return 0


# Get the latest match's information
def latest_match():
    print "The Latest Match"
    count = 0
    returned_id = 0
    start = time.time()
    results = db.search("matches", "LATEST", "1")
    tools.logger("Retrieved latest result.", "lookup")
    table = PrettyTable(['#', 'ID#', 'P1 ID', 'P2 ID', 'WINNER', 'TIME'])
    table.align = 'l'
    for row in results:
        count += 1
        player = db.search("players", "CODE", row[3])
        for entry in player:
            name = entry[1]
        if name == '':
            name = "[PLAYER DELETED]"
        table.add_row([count, row[0], row[1], row[2], name, row[4]])
        returned_id = row[0]
    print table
    stop = time.time()
    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    tools.logger(("Returned %i results in %s seconds" % (count, dur[:5])),
                 "list_matches")
    print "Returned %s results in %s seconds" % (count, dur[:5])
    return returned_id


# Get the latest match's information
def lookup_match(match=""):
    if not match:
        raise Exception("Missing a match ID.")
    count = 0
    # defining 'name' here prevents "UnboundLocalError: referenced before
    # assignment" that comes up if we lookup and the player was deleted.
    name = ''
    start = time.time()
    results = db.search("matches", "ID", match)
    tools.logger("Retrieved latest result.", "lookup")
    table = PrettyTable(['#', 'ID#', 'P1 ID', 'P2 ID', 'WINNER', 'TIME'])
    table.align = 'l'
    for row in results:
        count += 1
        player = db.search("players", "CODE", row[3])
        for entry in player:
            name = entry[1]
        if name == '':
            name = "[PLAYER DELETED]"
        table.add_row([count, row[0], row[1], row[2], name, row[4]])
    print table
    stop = time.time()
    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    tools.logger(("Returned %i results in %s seconds" % (count, dur[:5])),
                 "list_matches")
    print "Returned %s results in %s seconds" % (count, dur[:5])
    return 0


# Rank Players by Number of Wins
def list_win_ranking():
    print "List Ranking of Players by Wins"
    count = 0
    name = ''
    # get list of players and their IDs
    # for each player, count the number of times they won in every match
    start = time.time()
    results = db.player_standings()
    table = PrettyTable(['#', 'PLAYER', 'WINS'])
    table.align = 'l'
    for row in results:
        count += 1
        player = db.search("players", "CODE", row[0])
        for entry in player:
            name = entry[1]
        if name == '':
            name = "[PLAYER DELETED]"
        table.add_row([count, name, row[1]])
    print table
    stop = time.time()
    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    tools.logger(("Returned %i results in %s seconds" % (count, dur[:5])),
                 "list_matches")
    print "Returned %s results in %s seconds" % (count, dur[:5])
    return 0


# Any good app keeps a log.
def display_log():
    tools.logger("Displaying log entries.", "display_log()")
    count = 20
    print "Displaying last 20 entries."
    start = time.time()
    results = db.search("auditlog", "LOGS", count)
    tools.logger("Retrieved results x20.", "display_log()")
    table = PrettyTable(['#', 'ENTRY', 'ACTION', 'UNIQUE ID', 'TIMESTAMP'])
    table.align = 'l'
    for row in results:
        table.add_row([row[0], row[1], row[2], row[3], row[4]])
    tools.logger("Created audit log table.", "display_log()")
    print table
    stop = time.time()
    tools.logger("Printed audit log table.", "display_log()")
    dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                    rounding="ROUND_UP"))
    tools.logger(("Returned %i results in %s seconds" % (count, dur[:5])),
                 "display_log()")
    print "Returned %s results in %s seconds" % (count, dur[:5])
    see_all = raw_input("Want to see all entries? [Yes/No]: ")
    if see_all == "Yes":
        tools.logger("User requested ALL entries.", "display_log()")
        count = 9999999
        start = time.time()
        results = db.search("auditlog", "LOGS", count)
        tools.logger("Retrieved results x9999999.", "display_log()")
        table = PrettyTable(['#', 'ENTRY', 'ACTION', 'UNIQUE ID', 'TIMESTAMP'])
        table.align = 'l'
        for row in results:
            table.add_row([row[0], row[1], row[2], row[3], row[4]])
        tools.logger("Created audit log table.", "display_log()")
        print table
        stop = time.time()
        tools.logger("Printed audit log table.", "display_log()")
        dur = str(Decimal(float(stop - start)).quantize(Decimal('.01'),
                                                        rounding="ROUND_UP"))
        tools.logger(("Returned %i results in %s seconds" %
                      (count, dur[:5])), "display_log()")
        print "Returned %s results in %s seconds" % (count, dur[:5])
    else:
        print "Ok."
    return 0


# Using command-line arguments to control actions. User can use flags to run
# certain, pre-defined scenarios. This will also allow for reuse of code where
# applicable.


def argument_parser():
    parser = arg.ArgumentParser(description=cfg.APP_DESCRIPTION)

    # NEW PLAYER function
    parser.add_argument('--new-player', '-n',
                        dest='new_player',
                        action='store',
                        metavar='\"FIRST LAST\"',
                        help='Create a new player. '
                             'Give a Name wrapped in quotes.')

    # NEW MATCH function
    parser.add_argument('--new-match', '-m',
                        dest='new_match',
                        action='store',
                        nargs="+",
                        metavar='ID#1 ID#2',
                        help='Create a new match. Provide two player IDs.')

    # SWISS MATCHUP function
    parser.add_argument('--swiss-match', '-s',
                        dest='swiss_match',
                        action='store_true',
                        default=False,
                        help='Create a new match with swiss pairing.')

    # GET LATEST RESULTS function
    parser.add_argument('--latest-match' '-l',
                        dest='latest_match',
                        action='store_true',
                        default=False,
                        help='Get the results from the latest match.')

    # GET LATEST RESULTS function
    parser.add_argument('--lookup-match', '-r',
                        dest='lookup_match',
                        action='store',
                        metavar='ID',
                        help='Get the results from a specific match.')

    # DELETE PLAYER function
    parser.add_argument('--delete-player', '-d',
                        dest='delete_player',
                        action='store',
                        metavar='ID',
                        help='Remove a player from the match system.')

    # EDIT PLAYER function
    parser.add_argument('--edit-player', '-e',
                        dest='edit_player',
                        action='store',
                        metavar='ID',
                        help='Edit a player\'s exiting information.')

    # DELETE MATCH function
    parser.add_argument('--delete-match', '-f',
                        dest='delete_match',
                        action='store',
                        metavar='ID',
                        help='Remove a match from the match system.')

    # LIST RESULTS function
    parser.add_argument('--list-matches', '-k',
                        dest='list_matches',
                        action='store_true',
                        default=False,
                        help='List Results from a recent match.')

    # LIST PLAYERS function
    parser.add_argument('--list-players', '-p',
                        dest='list_players',
                        action='store_true',
                        default=False,
                        help='List all players.')

    # LIST RANKED function
    parser.add_argument('--list-ranking', '-t',
                        dest='list_ranking',
                        action='store_true',
                        default=False,
                        help='List rankings.')

    # VIEW AUDIT LOG function
    parser.add_argument('--audit-log', '-a',
                        dest='audit_log',
                        action='store_true',
                        default=False,
                        help='Display the Audit Logs.')

    return parser


# ROUTING LOGIC #
def main():
    parser = argument_parser()
    args = parser.parse_args()
    if args.new_player:
        new_player(player_name=args.new_player)

    if args.new_match:
        players = args.new_match
        go_match(match_type="REG", player_1=players[0], player_2=players[1])

    if args.swiss_match:
        swiss_match()

    if args.delete_player:
        edit_player(option="delete",
                    player=str(args.delete_player))

    if args.edit_player:
        edit_player(option="edit",
                    player=str(args.edit_player))

    if args.list_players:
        list_players()

    if args.delete_match:
        delete_match(match=str(args.delete_match))

    if args.list_matches:
        list_matches()

    if args.lookup_match:
        lookup_match(match=str(args.lookup_match))

    if args.latest_match:
        latest_match()

    if args.list_ranking:
        list_win_ranking()

    if args.audit_log:
        display_log()


    # IF NO ARGUMENTS #

    if len(sys.argv) == 1:
        print ""


if __name__ == "__main__":
    check_version(sys.version_info)
    main()
