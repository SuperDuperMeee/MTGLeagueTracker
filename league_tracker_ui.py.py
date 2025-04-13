import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import json
import csv
import datetime
import platform
import subprocess


def is_dark_mode_mac():
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            return "Dark" in result.stdout
        except:
            return False
    return False


class CommanderLeague:
    def __init__(self, players=None):
        if players is None:
            players = []
        team_colors = ["red", "blue", "green", "orange", "purple", "magenta", "cyan", "yellow", "pink"]
        self.players = {
            player: {"points": 0, "games_played": 0, "mvp_count": 0, "color": team_colors[i % len(team_colors)]}
            for i, player in enumerate(players)
        }
        self.history = []

    def record_game_results(self, results_dict, notes="", mvp="", deck_used=""):
        placement_points = {
            "1st": 5,
            "2nd": 3,
            "3rd": 2,
            "4th": 1,
            "5th+": 0
        }
        game = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": results_dict,
            "notes": notes,
            "mvp": mvp,
            "deck_used": deck_used
        }
        self.history.append(game)

        for player, place in results_dict.items():
            if place == "Did Not Play":
                continue
            points = placement_points.get(place, 0)
            self.players[player]["points"] += points
            self.players[player]["games_played"] += 1

        if mvp and mvp in self.players:
            self.players[mvp]["points"] += 1
            self.players[mvp]["mvp_count"] += 1

    def get_standings(self, sort_by='average'):
        standings = []
        for player, data in self.players.items():
            points = data["points"]
            games = data["games_played"]
            mvp_count = data.get("mvp_count", 0)
            avg = (points / games) if games > 0 else 0
            standings.append((player, points, games, avg, mvp_count))
        if sort_by == 'games':
            return sorted(standings, key=lambda x: x[2], reverse=True)
        return sorted(standings, key=lambda x: x[3], reverse=True)

    def save_to_file(self, filename='league_scores.json'):
        data = {"players": self.players, "history": self.history}
        with open(filename, 'w') as f:
            json.dump(data, f)

    def load_from_file(self, filename='league_scores.json'):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.players = data.get("players", {})
                self.history = data.get("history", [])
        except FileNotFoundError:
            print("Save file not found. Starting new league.")

    def export_to_csv(self, filename='league_export.csv'):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Player", "Points", "Games Played", "Average Points per Game", "MVP Awards"])
            for player, points, games, avg, mvps in self.get_standings():
                writer.writerow([player, points, games, f"{avg:.2f}", mvps])

    def add_player(self, name):
        if name and name not in self.players:
            team_colors = ["red", "blue", "green", "orange", "purple", "magenta", "cyan", "yellow", "pink"]
            color = team_colors[len(self.players) % len(team_colors)]
            self.players[name] = {"points": 0, "games_played": 0, "mvp_count": 0, "color": color}

    def remove_player(self, name):
        if name in self.players:
            del self.players[name]

    def reset_league(self):
        for player in self.players:
            self.players[player]["points"] = 0
            self.players[player]["games_played"] = 0
            self.players[player]["mvp_count"] = 0
        self.history = []


class LeagueApp:
    def __init__(self, root, league):
        self.root = root
        self.league = league
        self.sort_mode = 'average'
        self.dark_mode = is_dark_mode_mac()
        self.bg_color = "#1e1e1e" if self.dark_mode else "white"
        self.fg_color = "white" if self.dark_mode else "black"
        self.btn_bg = "#333333" if self.dark_mode else "SystemButtonFace"
        self.btn_fg = "white" if self.dark_mode else "black"
        self.root.title("Commander League Tracker")
        self.root.configure(bg=self.bg_color)
        self.build_main_ui()

    def build_main_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.root, padx=10, pady=10, bg=self.bg_color)
        main_frame.pack()

        buttons = [
            ("Record Game Result", self.open_record_game_dialog),
            ("Show Standings", self.show_standings),
            ("Show History", self.show_history),
            ("Add Player", self.add_player),
            ("Remove Player", self.remove_player),
            ("Reset League", self.reset_league),
            ("Save League", self.save_league),
            ("Load League", self.load_league),
            ("Export to CSV", self.export_csv),
            ("Toggle Sort", self.toggle_sort)
        ]

        for i, (label, action) in enumerate(buttons):
            tk.Button(main_frame, text=label, width=20, command=action,
                      bg=self.btn_bg, fg=self.btn_fg).grid(row=i // 3, column=i % 3, padx=5, pady=5)

    def open_record_game_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Record Game Result")
        dialog.configure(bg=self.bg_color)

        placement_options = ["1st", "2nd", "3rd", "4th", "5th+", "Did Not Play"]
        entries = {}

        player_frame = tk.Frame(dialog, bg=self.bg_color)
        player_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(player_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(player_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.bg_color)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for player in self.league.players:
            row = tk.Frame(scrollable, bg=self.bg_color)
            row.pack(anchor="w", fill="x", pady=2)

            color = self.league.players[player].get("color", "gray")
            tk.Label(row, bg=color, width=2).pack(side="left", padx=(5, 5))
            tk.Label(row, text=player, bg=self.bg_color, fg=self.fg_color, width=15, anchor="w").pack(side="left")
            var = tk.StringVar(value="Did Not Play")
            tk.OptionMenu(row, var, *placement_options).pack(side="left", padx=5)
            entries[player] = var

        form = tk.Frame(dialog, bg=self.bg_color, padx=10, pady=10)
        form.pack(fill="x")

        tk.Label(form, text="Game Notes:", bg=self.bg_color, fg=self.fg_color).pack(anchor="w")
        notes_entry = tk.Entry(form, width=50)
        notes_entry.pack(anchor="w", pady=(0, 10))

        tk.Label(form, text="MVP:", bg=self.bg_color, fg=self.fg_color).pack(anchor="w")
        mvp_var = tk.StringVar()
        mvp_choices = list(self.league.players.keys())
        if mvp_choices:
            mvp_var.set(mvp_choices[0])
        tk.OptionMenu(form, mvp_var, *mvp_choices).pack(anchor="w", pady=(0, 10))

        tk.Label(form, text="Deck Used:", bg=self.bg_color, fg=self.fg_color).pack(anchor="w")
        deck_entry = tk.Entry(form, width=50)
        deck_entry.pack(anchor="w", pady=(0, 10))

        def record():
            results = {p: var.get() for p, var in entries.items()}
            if all(r == "Did Not Play" for r in results.values()):
                messagebox.showerror("Error", "At least one player must have a placement.")
                return

            self.league.record_game_results(
                results,
                notes=notes_entry.get().strip(),
                mvp=mvp_var.get().strip(),
                deck_used=deck_entry.get().strip()
            )
            messagebox.showinfo("Success", "Game result recorded.")
            dialog.destroy()

        tk.Button(form, text="Record Game", command=record, bg=self.btn_bg, fg=self.btn_fg).pack(pady=5)

    def show_standings(self):
        standings = self.league.get_standings(sort_by=self.sort_mode)
        message = f"Standings (sorted by {self.sort_mode}):\n\n"
        for i, (player, points, games, avg, mvps) in enumerate(standings, 1):
            message += f"{i}. {player}: {points} pts | {games} games | {avg:.2f} avg | {mvps} MVPs\n"
        messagebox.showinfo("League Standings", message)

    def show_history(self):
        if not self.league.history:
            messagebox.showinfo("History", "No games recorded yet.")
            return
        message = "Game History:\n\n"
        for game in self.league.history:
            message += f"{game['timestamp']}:\n"
            for player, result in game["results"].items():
                message += f"  {player}: {result}\n"
            if game["notes"]:
                message += f"  Notes: {game['notes']}\n"
            if game.get("mvp"):
                message += f"  MVP: {game['mvp']}\n"
            if game.get("deck_used"):
                message += f"  Deck Used: {game['deck_used']}\n"
            message += "\n"
        messagebox.showinfo("Game History", message)

    def save_league(self):
        self.league.save_to_file()
        messagebox.showinfo("Saved", "League progress saved.")

    def load_league(self):
        self.league.load_from_file()
        self.build_main_ui()
        self.show_standings()

    def export_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file:
            self.league.export_to_csv(file)
            messagebox.showinfo("Exported", f"Data exported to {file}")

    def toggle_sort(self):
        self.sort_mode = 'games' if self.sort_mode == 'average' else 'average'
        self.show_standings()

    def add_player(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Player")
        dialog.configure(bg=self.bg_color)
        tk.Label(dialog, text="Enter new player name:", bg=self.bg_color, fg=self.fg_color).pack(padx=10, pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(padx=10, pady=5)
        name_entry.focus_set()

        def confirm():
            name = name_entry.get().strip()
            if name:
                self.league.add_player(name)
                self.build_main_ui()
            dialog.destroy()

        tk.Button(dialog, text="Add", command=confirm,
                  bg=self.btn_bg, fg=self.btn_fg).pack(pady=10)

    def remove_player(self):
        name = simpledialog.askstring("Remove Player", "Enter player name to remove:")
        if name and name in self.league.players:
            self.league.remove_player(name.strip())
            self.build_main_ui()
        else:
            messagebox.showerror("Error", f"Player '{name}' not found.")

    def reset_league(self):
        if messagebox.askyesno("Reset League", "Are you sure you want to reset all scores and history?"):
            self.league.reset_league()
            self.build_main_ui()
            messagebox.showinfo("Reset", "League has been reset.")


if __name__ == "__main__":
    players = ["Mike", "Mez", "Dan", "Vik", "Noah", "Lucas", "Isaac", "Layla", "Steve"]
    league = CommanderLeague(players)
    league.load_from_file()
    if not league.players:
        league = CommanderLeague(players)
    root = tk.Tk()
    app = LeagueApp(root, league)
    root.mainloop()