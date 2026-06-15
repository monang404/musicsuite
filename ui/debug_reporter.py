import os

class DebugSearchReporter:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DebugSearchReporter, cls).__new__(cls)
            cls._instance.reset()
        return cls._instance

    def reset(self):
        self.search_returned = 0
        self.signal_sent = 0
        self.signal_received = 0
        self.after_filter = 0
        self.after_tab_filter = 0
        self.cards_created = 0
        self.cards_added_to_layout = 0
        self.visible_cards = 0
        
        self.selected_tab = "None"
        self.selected_sort = "None"
        self.search_query = "None"

    def calculate_root_cause(self):
        if self.search_returned == 0:
            return "Search backend returned no data."
        if self.signal_received == 0:
            return "Signal from worker to UI was lost."
        if self.after_tab_filter == 0 and self.search_returned > 0:
            return "Category filtering bug."
        if self.after_filter == 0 and self.after_tab_filter > 0:
            return "Text filtering bug."
        if self.visible_cards == 0 and self.search_returned > 0:
            if self.cards_created > 0 and self.cards_added_to_layout > 0:
                return "UI rendering/layout bug."
            else:
                return "UI rendering bug."
        return "Success / No Failure"

    def write_report(self):
        os.makedirs("debug", exist_ok=True)
        report_path = "debug/search_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"SEARCH_RETURNED = {self.search_returned}\n")
            f.write(f"SIGNAL_SENT = {self.signal_sent}\n")
            f.write(f"SIGNAL_RECEIVED = {self.signal_received}\n")
            f.write(f"AFTER_FILTER = {self.after_filter}\n")
            f.write(f"AFTER_TAB_FILTER = {self.after_tab_filter}\n")
            f.write(f"CARDS_CREATED = {self.cards_created}\n")
            f.write(f"CARDS_ADDED_TO_LAYOUT = {self.cards_added_to_layout}\n")
            f.write(f"VISIBLE_CARDS = {self.visible_cards}\n")
            f.write("\n")
            f.write(f"Selected Tab: {self.selected_tab}\n")
            f.write(f"Selected Sort: {self.selected_sort}\n")
            f.write(f"Search Query: {self.search_query}\n")
            f.write("\n")
            f.write("ROOT CAUSE:\n")
            f.write(self.calculate_root_cause() + "\n")
