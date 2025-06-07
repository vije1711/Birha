import csv
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
import pandas as pd
import ast
import re
import random
import unicodedata
import pyperclip
import tkinter as tk
from tkinter import ttk
import threading
import ast
import re
from rapidfuzz import fuzz
import copy


class GrammarApp:
    def __init__(self, root):
        """
        Initialize the application and display the dashboard as the main window.
        """
        self.root = root
        self.root.title("Dashboard")
        self.root.configure(bg='light gray')
        self.root.state('zoomed')  # Maximize window (Windows)

        # Initialize variables for user input options
        self.number_var = tk.StringVar(value="NA")
        self.gender_var = tk.StringVar(value="NA")
        self.pos_var = tk.StringVar(value="NA")

        # Initialize lists/variables for data accumulation
        self.new_entries = []
        self.accumulated_pankti = ""
        self.accumulated_meanings = []
        self.accumulated_grammar_matches = []
        self.accumulated_finalized_matches = []
        self.current_pankti = ""
        self.match_vars = []
        self.all_matches = []
        self.all_new_entries = []  # Global accumulator for all assessed words
        
        # For word-by-word navigation
        self.current_word_index = 0
        self.pankti_words = []

        # Load grammar/dictionary data
        self.grammar_data = self.load_grammar_data("1.1.1_birha.csv")
        self.dictionary_data = pd.read_csv("1.1.2 Grammatical Meanings Dictionary.csv", encoding='utf-8')

        # Show the dashboard directly in the root window
        self.show_dashboard()

    def show_dashboard(self):
        """Creates the dashboard interface directly in the main root window."""
        # Clear any existing widgets from the root
        for widget in self.root.winfo_children():
            widget.destroy()

        # Set up the dashboard appearance in the root window
        self.root.title("Dashboard")
        self.root.configure(bg='light gray')
        self.root.state("zoomed")  # Maximize the window

        # Dashboard header label
        header = tk.Label(
            self.root,
            text="Welcome to Gurbani Software Dashboard",
            font=('Arial', 18, 'bold'),
            bg='dark slate gray',
            fg='white'
        )
        header.pack(fill=tk.X, pady=20)

        # Create a frame to hold dashboard buttons
        button_frame = tk.Frame(self.root, bg='light gray')
        button_frame.pack(expand=True)

        # New Button to open the Verse Analysis Dashboard
        verse_analysis_btn = tk.Button(
            button_frame,
            text="Verse Analysis Dashboard",
            font=('Arial', 14, 'bold'),
            bg='dark cyan',
            fg='white',
            padx=20,
            pady=10,
            command=self.launch_verse_analysis_dashboard
        )
        verse_analysis_btn.pack(pady=10)

        # Placeholder for future features (e.g., Grammar Correction)
        future_btn = tk.Button(
            button_frame,
            text="Upcoming Feature: Grammar Correction",
            font=('Arial', 14, 'bold'),
            bg='gray',
            fg='white',
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        future_btn.pack(pady=10)

    def launch_verse_analysis_dashboard(self):
        """Clears the main dashboard and launches the Verse Analysis Dashboard."""
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.title("Verse Analysis Dashboard")
        self.setup_verse_analysis_dashboard()

    def setup_verse_analysis_dashboard(self):
        """Builds the Verse Analysis Dashboard interface."""
        for widget in self.root.winfo_children():
            widget.destroy()
        self.main_frame = tk.Frame(self.root, bg='light gray', padx=10, pady=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        header_label = tk.Label(
            self.main_frame,
            text="Verse Analysis Dashboard",
            font=('Arial', 18, 'bold'),
            bg='dark slate gray',
            fg='white',
            pady=10
        )
        header_label.pack(fill=tk.X, pady=10)

        # Create a frame for the option buttons
        button_frame = tk.Frame(self.main_frame, bg='light gray')
        button_frame.pack(expand=True)

        # Literal Translation Button
        literal_btn = tk.Button(
            button_frame,
            text="Literal Translation",
            font=('Arial', 14, 'bold'),
            bg='dark cyan',
            fg='white',
            padx=20,
            pady=10,
            command=self.launch_literal_analysis
        )
        literal_btn.pack(pady=10)

        # New button for editing saved literal translation
        edit_saved_btn = tk.Button(
            button_frame,
            text="Edit Saved Literal Translation",
            font=('Arial', 14, 'bold'),
            bg='dark cyan',
            fg='white',
            padx=20,
            pady=10,
            command=self.launch_select_verse  # Updated command
        )
        edit_saved_btn.pack(pady=10)

        # Placeholder for Spiritual Translation (future implementation)
        spiritual_btn = tk.Button(
            button_frame,
            text="Spiritual Translation (Coming Soon)",
            font=('Arial', 14, 'bold'),
            bg='gray',
            fg='white',
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        spiritual_btn.pack(pady=10)

        # Placeholder for Translation Management (future implementation)
        management_btn = tk.Button(
            button_frame,
            text="Translation Management (Coming Soon)",
            font=('Arial', 14, 'bold'),
            bg='gray',
            fg='white',
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        management_btn.pack(pady=10)

        # Back button to return to the main dashboard
        back_btn = tk.Button(
            self.main_frame,
            text="Back to Main Dashboard",
            font=('Arial', 14, 'bold'),
            bg='red',
            fg='white',
            padx=20,
            pady=10,
            command=self.show_dashboard
        )
        back_btn.pack(pady=10)

    def launch_select_verse(self):
        """
        Creates a centered modal window to let the user select a verse by:
        1. Searching by verse content
        2. Filtering by metadata (Raag, Writer, Bani, Page)
        Displays only those verses that already exist in the assessment Excel.
        """

        # === Setup modal ===
        select_win = tk.Toplevel(self.root)
        select_win.title("Select Verse")
        select_win.geometry("800x600")
        select_win.state("zoomed")
        select_win.configure(bg="light gray")

        # === Load Excel data ===
        file_path = "1.2.1 assessment_data.xlsx"
        df_existing = self.load_existing_assessment_data(file_path)

        # === Center content ===
        center_frame = tk.Frame(select_win, bg="light gray")
        center_frame.pack(expand=True)

        content_frame = tk.Frame(center_frame, bg="light gray", width=960)
        content_frame.pack()

        # === Header ===
        header_label = tk.Label(
            content_frame,
            text="Select Verse",
            bg="dark slate gray",
            fg="white",
            font=("Helvetica", 18, "bold"),
            padx=20, pady=10
        )
        header_label.pack(fill=tk.X, pady=(0, 10))

        # === Mode selection (Search or Filter) ===
        mode_var = tk.StringVar(value="search")
        mode_frame = tk.Frame(content_frame, bg="light gray")
        mode_frame.pack(pady=10)

        tk.Radiobutton(mode_frame, text="Search by Verse", variable=mode_var, value="search",
                    bg="light gray", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Filter by Metadata", variable=mode_var, value="filter",
                    bg="light gray", font=("Arial", 12)).pack(side=tk.LEFT, padx=10)

        # === Create container for dynamic frames ===
        main_content_area = tk.Frame(content_frame, bg="light gray")
        main_content_area.pack(fill=tk.BOTH, expand=True)

        # === Search Frame ===
        search_frame = tk.Frame(main_content_area, bg="light gray")
        tk.Label(search_frame, text="Enter or paste a verse to search:", bg="light gray",
                font=("Arial", 12, "bold")).pack(pady=5)

        search_entry = tk.Entry(search_frame, font=("Arial", 12), width=80)
        search_entry.pack(pady=5)

        search_button = tk.Button(
            search_frame, text="Search", font=("Arial", 12, "bold"),
            bg="navy", fg="white", width=12,
            command=lambda: perform_search(search_entry.get())
        )
        search_button.pack(pady=5)

        search_results_list = tk.Listbox(search_frame, font=("Arial", 12), width=80, height=10)
        search_results_list.pack(pady=10)

        # === Filter Frame ===
        filter_frame = tk.Frame(main_content_area, bg="light gray")
        tk.Label(filter_frame, text="Filter verses by metadata:", bg="light gray",
                font=("Arial", 12, "bold")).pack(pady=5)

        filter_controls = tk.Frame(filter_frame, bg="light gray")
        filter_controls.pack(pady=5)

        # === Dropdowns for filter ===
        df = df_existing.copy()
        raag_var, writer_var, bani_var, page_var = tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()
        # Sort Raag, Writer, Bani based on first page appearance
        initial_raag = df.dropna(subset=["Raag (Fixed)"]).drop_duplicates("Raag (Fixed)", keep="first").sort_values("Page Number")["Raag (Fixed)"].tolist()
        initial_writer = df.dropna(subset=["Writer (Fixed)"]).drop_duplicates("Writer (Fixed)", keep="first").sort_values("Page Number")["Writer (Fixed)"].tolist()
        initial_bani = df.dropna(subset=["Bani Name"]).drop_duplicates("Bani Name", keep="first").sort_values("Page Number")["Bani Name"].tolist()
        # Sort Page Numbers numerically
        initial_page = sorted(df["Page Number"].dropna().unique())
        initial_page = [str(p) for p in initial_page]  # Convert back to string for dropdown


        tk.Label(filter_controls, text="Raag:", bg="light gray", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
        raag_dropdown = ttk.Combobox(filter_controls, textvariable=raag_var, values=initial_raag, width=15)
        raag_dropdown.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(filter_controls, text="Writer:", bg="light gray", font=("Arial", 12)).grid(row=0, column=2, padx=5, pady=5)
        writer_dropdown = ttk.Combobox(filter_controls, textvariable=writer_var, values=initial_writer, width=15)
        writer_dropdown.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(filter_controls, text="Bani:", bg="light gray", font=("Arial", 12)).grid(row=0, column=4, padx=5, pady=5)
        bani_dropdown = ttk.Combobox(filter_controls, textvariable=bani_var, values=initial_bani, width=15)
        bani_dropdown.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(filter_controls, text="Page:", bg="light gray", font=("Arial", 12)).grid(row=0, column=6, padx=5, pady=5)
        page_dropdown = ttk.Combobox(filter_controls, textvariable=page_var, values=initial_page, width=10)
        page_dropdown.grid(row=0, column=7, padx=5, pady=5)

        # === Update filter dropdowns dynamically ===
        def update_dropdowns(*args):
            filtered_df = df.copy()
            if raag_var.get():
                filtered_df = filtered_df[filtered_df["Raag (Fixed)"] == raag_var.get()]
            if writer_var.get():
                filtered_df = filtered_df[filtered_df["Writer (Fixed)"] == writer_var.get()]
            if bani_var.get():
                filtered_df = filtered_df[filtered_df["Bani Name"] == bani_var.get()]
            if page_var.get():
                filtered_df = filtered_df[filtered_df["Page Number"].astype(str) == page_var.get()]
            raag_dropdown['values'] = (
                filtered_df.dropna(subset=["Raag (Fixed)"])
                .drop_duplicates("Raag (Fixed)", keep="first")
                .sort_values("Page Number")["Raag (Fixed)"].tolist()
            )

            writer_dropdown['values'] = (
                filtered_df.dropna(subset=["Writer (Fixed)"])
                .drop_duplicates("Writer (Fixed)", keep="first")
                .sort_values("Page Number")["Writer (Fixed)"].tolist()
            )

            bani_dropdown['values'] = (
                filtered_df.dropna(subset=["Bani Name"])
                .drop_duplicates("Bani Name", keep="first")
                .sort_values("Page Number")["Bani Name"].tolist()
            )

            sorted_pages = sorted(filtered_df["Page Number"].dropna().unique())
            page_dropdown['values'] = [str(p) for p in sorted_pages]

        for var in (raag_var, writer_var, bani_var, page_var):
            var.trace_add("write", update_dropdowns)

        # === Filter Button & Listbox ===
        filter_button = tk.Button(filter_frame, text="Apply Filter", font=("Arial", 12, "bold"),
                                bg="navy", fg="white", command=lambda: update_verse_list())
        filter_button.pack(pady=5)

        filter_results_list = tk.Listbox(filter_frame, font=("Arial", 12), width=80, height=10)
        filter_results_list.pack(pady=10)

        # === Toggle mode display ===
        def update_mode():
            filter_frame.pack_forget()
            search_frame.pack_forget()
            if mode_var.get() == "search":
                search_frame.pack(pady=10)
            else:
                filter_frame.pack(pady=10)

        mode_var.trace_add("write", lambda *args: update_mode())
        update_mode()

        # === Search Logic ===
        def perform_search(query):
            search_results_list.delete(0, tk.END)
            if not query:
                search_results_list.insert(tk.END, "No query entered.")
                return
            headers, candidate_matches = self.match_sggs_verse(query)
            candidate_verses = list(dict.fromkeys(candidate["Verse"] for candidate in candidate_matches))
            excel_verses = set(df_existing["Verse"].unique())
            unique_verses = [v for v in candidate_verses if v in excel_verses]
            if unique_verses:
                for verse in unique_verses:
                    search_results_list.insert(tk.END, verse)
            else:
                search_results_list.insert(tk.END, "No analyzed verse matches found.")

        # === Filter Logic ===
        def update_verse_list():
            filter_results_list.delete(0, tk.END)
            filtered_df = df_existing.copy()
            if raag_var.get():
                filtered_df = filtered_df[filtered_df["Raag (Fixed)"].str.contains(raag_var.get(), case=False, na=False)]
            if writer_var.get():
                filtered_df = filtered_df[filtered_df["Writer (Fixed)"].str.contains(writer_var.get(), case=False, na=False)]
            if bani_var.get():
                filtered_df = filtered_df[filtered_df["Bani Name"].str.contains(bani_var.get(), case=False, na=False)]
            if page_var.get():
                filtered_df = filtered_df[filtered_df["Page Number"].astype(str).str.contains(page_var.get(), case=False, na=False)]
            for verse in filtered_df["Verse"].unique():
                filter_results_list.insert(tk.END, verse)

        # === Finalize & Back buttons ===
        def finalize_selection():
            if mode_var.get() == "search":
                sel = search_results_list.curselection()
                final_verse = search_results_list.get(sel[0]) if sel else ""
            else:
                sel = filter_results_list.curselection()
                final_verse = filter_results_list.get(sel[0]) if sel else ""
            if final_verse:
                self.finalized_verse = final_verse
                select_win.destroy()
                self.launch_edit_saved_literal_translation()
            else:
                tk.messagebox.showerror("Error", "Please select a verse before proceeding.")

        bottom_frame = tk.Frame(main_content_area, bg="light gray")
        bottom_frame.pack(side=tk.BOTTOM, pady=10)

        tk.Button(bottom_frame, text="Finalize Selection", font=("Arial", 12, "bold"),
                bg="green", fg="white", padx=15, pady=5,
                command=finalize_selection).pack(side=tk.LEFT, padx=(10, 5))

        tk.Button(bottom_frame, text="Back to Dashboard", font=("Arial", 12, "bold"),
                bg="gray", fg="white", padx=15, pady=5,
                command=lambda: (select_win.destroy(), self.setup_verse_analysis_dashboard())).pack(side=tk.LEFT, padx=(5, 10))

        # === Modal behavior ===
        select_win.transient(self.root)
        select_win.grab_set()
        self.root.wait_window(select_win)

    def launch_edit_saved_literal_translation(self):
        """Launch a window to review and select words for re-analysis from a saved verse."""

        verse = self.finalized_verse
        df = self.load_existing_assessment_data("1.2.1 assessment_data.xlsx")

        # === Clear root ===
        for widget in self.root.winfo_children():
            widget.destroy()

        # === Setup main frame ===
        main_frame = tk.Frame(self.root, bg="light gray", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === Header ===
        header = tk.Label(
            main_frame,
            text="Edit Saved Literal Translation",
            font=("Helvetica", 18, "bold"),
            bg="dark slate gray",
            fg="white",
            pady=10
        )
        header.pack(fill=tk.X, pady=(0, 20))

        # === Display Verse ===
        verse_label = tk.Label(
            main_frame,
            text=f"Verse:\n  {verse}",
            font=("Arial", 14),
            bg="light gray",
            anchor="w",
            justify="left"
        )
        verse_label.pack(fill=tk.X, padx=10)

        # === Display Translation ===
        row_data = df[df['Verse'] == verse].iloc[0]
        translation = row_data.get('Translation', '')
        translation_label = tk.Label(
            main_frame,
            text=f"Translation:\n  {translation}",
            font=("Arial", 13, "italic"),
            bg="light gray",
            anchor="w",
            justify="left"
        )
        translation_label.pack(fill=tk.X, padx=10, pady=(10, 5))

        # === Metadata (Raag, Writer, Bani, Page) ===
        def safe(val):
            return val if pd.notna(val) else "—"

        metadata_frame = tk.Frame(main_frame, bg="light gray")
        metadata_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        for label, col in [("Raag:", "Raag (Fixed)"),
                        ("Writer:", "Writer (Fixed)"),
                        ("Bani:", "Bani Name"),
                        ("Page:", "Page Number")]:
            val = safe(row_data.get(col))
            meta = tk.Label(
                metadata_frame,
                text=f"{label} {val}",
                font=("Arial", 11, "bold"),
                bg="light gray",
                anchor="w",
                justify="left"
            )
            meta.pack(anchor="w")

        # === Word Table Frame ===
        word_frame = tk.LabelFrame(
            main_frame,
            text="Select words to re-analyze:",
            bg="light gray",
            font=("Arial", 12, "bold")
        )
        word_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === Checkbox Simulation ===
        selected_items = set()

        columns = [
            'Select', 'Word', 'Vowel Ending', 'Number / ਵਚਨ',
            'Grammar / ਵਯਾਕਰਣ', 'Gender / ਲਿੰਗ', 'Word Type',
            'Word Root', 'Framework?', 'Explicit?'
        ]

        tree = ttk.Treeview(word_frame, columns=columns, show='headings', selectmode='none')
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor=tk.CENTER, width=110 if col != 'Select' else 60)

        # Add scrollbar
        vsb = ttk.Scrollbar(word_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # Insert rows
        rows = df[df['Verse'] == verse]
        for i, (_, row) in enumerate(rows.iterrows()):
            row_id = f"row{i}"
            values = [
                "",  # checkbox column
                safe(row.get('Word')),
                safe(row.get('Vowel Ending')),
                safe(row.get('Number / ਵਚਨ')),
                safe(row.get('Grammar / ਵਯਾਕਰਣ')),
                safe(row.get('Gender / ਲਿੰਗ')),
                safe(row.get('Word Root')),
                safe(row.get('Word Type')),
                safe(row.get('Framework?')),
                safe(row.get('Explicit?'))
            ]
            tree.insert('', tk.END, iid=row_id, values=values)

        # === Toggle ✓ in first column ===
        def on_tree_click(event):
            region = tree.identify_region(event.x, event.y)
            if region == 'cell':
                row_id = tree.identify_row(event.y)
                col = tree.identify_column(event.x)
                if row_id and col == '#1':
                    if row_id in selected_items:
                        selected_items.remove(row_id)
                        tree.set(row_id, 'Select', "")
                    else:
                        selected_items.add(row_id)
                        tree.set(row_id, 'Select', "✓")

        tree.bind('<Button-1>', on_tree_click)

        # === Action Buttons ===
        btn_frame = tk.Frame(main_frame, bg="light gray")
        btn_frame.pack(pady=20)

        def analyze_selected_words():
            selected_words = [tree.item(rid)['values'][1] for rid in selected_items]
            print("Selected words for analysis:", selected_words)
            # TODO: Hook to grammar/inflection analyzer

        def back_to_search():
            self.launch_select_verse()

        def back_to_dashboard():
            self.setup_verse_analysis_dashboard()

        tk.Button(
            btn_frame,
            text="Analyze Selected Words",
            bg="navy", fg="white",
            font=("Arial", 12, "bold"),
            padx=15, pady=5,
            command=analyze_selected_words
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Back to Search",
            bg="gray", fg="white",
            font=("Arial", 12, "bold"),
            padx=15, pady=5,
            command=back_to_search
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Back to Dashboard",
            bg="red", fg="white",
            font=("Arial", 12, "bold"),
            padx=15, pady=5,
            command=back_to_dashboard
        ).pack(side=tk.LEFT, padx=10)

        # === Optional: Customize style ===
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Arial', 11, 'bold'))
        style.configure("Treeview", rowheight=28, font=('Arial', 11))

    def setup_main_analysis_interface(self):
        """Builds the main analysis interface for Literal Meaning Analysis."""
        # Define a consistent color scheme
        BG_COLOR = "#f0f0f0"        # Light gray background for main area
        HEADER_COLOR = "#2c3e50"    # Dark slate-like header
        HEADER_TEXT_COLOR = "white"
        BUTTON_COLOR = "#007acc"    # A pleasant blue for action buttons
        BUTTON_TEXT_COLOR = "white"
        NAV_BUTTON_COLOR = "#5f9ea0" # CadetBlue for navigation
        LABEL_TEXT_COLOR = "#333333"
        
        # Define fonts
        TITLE_FONT = ("Helvetica", 20, "bold")
        LABEL_FONT = ("Helvetica", 14, "bold")
        ENTRY_FONT = ("Helvetica", 14)
        BUTTON_FONT = ("Helvetica", 14, "bold")
        RESULT_FONT = ("Helvetica", 12)

        # Clear existing widgets in case we re-enter
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=BG_COLOR)

        # Main frame (entire interface)
        self.main_frame = tk.Frame(self.root, bg=BG_COLOR, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Label
        header_label = tk.Label(
            self.main_frame,
            text="Grammar Analyzer",
            bg=HEADER_COLOR,
            fg=HEADER_TEXT_COLOR,
            font=TITLE_FONT,
            pady=10
        )
        header_label.pack(fill=tk.X, pady=(0, 20))

        # Label and Entry for Pankti
        self.pankti_label = tk.Label(
            self.main_frame,
            text="Please share the Pankti:",
            bg=BG_COLOR,
            fg=LABEL_TEXT_COLOR,
            font=LABEL_FONT
        )
        self.pankti_label.pack(anchor="w", pady=(0, 5))

        self.pankti_entry = tk.Entry(
            self.main_frame,
            width=70,
            font=ENTRY_FONT,
            bd=3,
            relief=tk.GROOVE
        )
        self.pankti_entry.pack(pady=(0, 15))

        # Analyze Button
        self.analyze_button = tk.Button(
            self.main_frame,
            text="Analyze",
            command=self.analyze_pankti,
            font=BUTTON_FONT,
            bg=BUTTON_COLOR,
            fg=BUTTON_TEXT_COLOR,
            relief=tk.RAISED,
            padx=30,
            pady=10
        )
        self.analyze_button.pack(pady=(0, 20))

        # Results Text Area
        self.results_text = scrolledtext.ScrolledText(
            self.main_frame,
            width=90,
            height=20,
            font=RESULT_FONT,
            bd=3,
            relief=tk.SUNKEN,
            wrap=tk.WORD
        )
        self.results_text.pack(pady=(0, 20))

        # Navigation Frame
        nav_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        nav_frame.pack(fill=tk.X, pady=10)

        # --- New Word Navigation Panel ---
        # A label to display the current word
        self.word_label = tk.Label(nav_frame, text="", font=("Helvetica", 16, "bold"),
                                bg="white", fg="black", width=20, relief=tk.SUNKEN)
        self.word_label.pack(side=tk.LEFT, padx=10)
        self.update_current_word_label()  # Update this label based on self.current_word_index

        # Previous button for word navigation
        self.prev_button = tk.Button(
            nav_frame,
            text="Previous",
            command=self.prev_word,
            state=tk.DISABLED,
            font=BUTTON_FONT,
            bg=NAV_BUTTON_COLOR,
            fg="white",
            padx=20,
            pady=5
        )
        self.prev_button.pack(side=tk.LEFT, padx=(0, 10))

        # Next button for word navigation
        self.next_button = tk.Button(
            nav_frame,
            text="Next",
            command=self.next_word,
            state=tk.DISABLED,
            font=BUTTON_FONT,
            bg=NAV_BUTTON_COLOR,
            fg="white",
            padx=20,
            pady=5
        )
        self.next_button.pack(side=tk.LEFT, padx=(0, 10))

        # Select Word button to analyze the currently displayed word
        select_word_btn = tk.Button(
            nav_frame,
            text="Select Word",
            command=self.select_current_word,
            font=BUTTON_FONT,
            bg=BUTTON_COLOR,
            fg=BUTTON_TEXT_COLOR,
            padx=20,
            pady=5
        )
        select_word_btn.pack(side=tk.LEFT, padx=(0, 10))
        # --- End Word Navigation Panel ---

        # Copy Analysis Button (initially disabled)
        self.copy_button = tk.Button(
            nav_frame,
            text="Copy Analysis",
            command=self.prompt_copy_to_clipboard,
            font=BUTTON_FONT,
            bg="#1b95e0",   # A slightly different blue for variety
            fg="white",
            padx=20,
            pady=5,
            state=tk.DISABLED
        )
        self.copy_button.pack(side=tk.RIGHT, padx=(10, 0))

        # Back to Dashboard Button
        back_dashboard_btn = tk.Button(
            nav_frame,
            text="Back to Dashboard",
            command=self.back_to_dashboard,
            font=BUTTON_FONT,
            bg="red",
            fg="white",
            padx=20,
            pady=5
        )
        back_dashboard_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Create a new "Save Results" button:
        self.save_results_btn = tk.Button(
            nav_frame,
            text="Save Results",
            command=lambda: self.prompt_save_results(self.all_new_entries, skip_copy=True),
            font=BUTTON_FONT,
            bg="#1b95e0",   # Choose a color you like
            fg="white",
            padx=20,
            pady=5,
            state=tk.DISABLED  # Initially disabled
        )
        self.save_results_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def back_to_dashboard(self):
        """Destroy the current main interface and return to the dashboard."""
        # Destroy the main analysis interface
        self.main_frame.destroy()
        # Optionally, reset any state if needed here.
        # Then, show the dashboard again:
        self.show_dashboard()

    def launch_literal_analysis(self):
        """Clears the dashboard and builds the literal meaning analysis interface."""
        # Clear the root window (removes the dashboard)
        for widget in self.root.winfo_children():
            widget.destroy()

        # Optionally update the window title
        self.root.title("Literal Meaning Analysis")

        # Build the main analysis interface
        self.setup_main_analysis_interface()

    def user_input(self, word, pankti):
        print(f"Opening input window for {word}")
        self.input_submitted = False

        self.input_window = tk.Toplevel(self.root)
        self.input_window.title(f"Input for {word}")
        self.input_window.configure(bg='light gray')
        self.input_window.state('zoomed')
        self.input_window.resizable(True, True)

        # ---------------------------
        # Display the Pankti on top
        # ---------------------------
        pankti_frame = tk.Frame(self.input_window, bg='light gray')
        pankti_frame.pack(fill=tk.X, padx=20, pady=10)

        pankti_display = tk.Text(
            pankti_frame, wrap=tk.WORD, bg='light gray', font=('Arial', 32),
            height=2, padx=5, pady=5
        )
        pankti_display.pack(fill=tk.X, expand=False)
        pankti_display.insert(tk.END, pankti)
        pankti_display.tag_add("center", "1.0", "end")
        pankti_display.tag_configure("center", justify='center')

        # Highlight the word at self.current_word_index
        words = pankti.split()
        start_idx = 0
        for i, w in enumerate(words):
            # When we reach the word at current_word_index, calculate its start/end
            if i == self.current_word_index:
                end_idx = start_idx + len(w)
                pankti_display.tag_add("highlight", f"1.{start_idx}", f"1.{end_idx}")
                pankti_display.tag_config("highlight", foreground="red", font=('Arial', 32, 'bold'))
                break
            # Move the start index past this word plus one space
            start_idx += len(w) + 1

        pankti_display.config(state=tk.DISABLED)

        # ---------------------------
        # Create a horizontal PanedWindow for split layout
        # ---------------------------
        split_pane = tk.PanedWindow(self.input_window, orient=tk.HORIZONTAL, bg='light gray')
        split_pane.pack(fill=tk.BOTH, expand=True)

        # Left pane: Meanings
        self.left_pane = tk.Frame(split_pane, bg='light gray')
        split_pane.add(self.left_pane, stretch="always")
        tk.Label(self.left_pane, text=f"Meanings for {word}:", bg='light gray',
                font=('Arial', 14, 'bold')).pack(anchor='center', pady=(0, 10))
        self.meanings_scrollbar = tk.Scrollbar(self.left_pane, orient=tk.VERTICAL)
        self.meanings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.meanings_canvas = tk.Canvas(self.left_pane, bg='light gray', borderwidth=0,
                                        yscrollcommand=self.meanings_scrollbar.set)
        self.meanings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.meanings_scrollbar.config(command=self.meanings_canvas.yview)
        self.meanings_inner_frame = tk.Frame(self.meanings_canvas, bg='light gray')
        self.meanings_canvas.create_window((0, 0), window=self.meanings_inner_frame, anchor='nw')

        # Right pane: Grammar Options
        right_pane = tk.Frame(split_pane, bg='light gray')
        split_pane.add(right_pane, stretch="always")
        tk.Label(right_pane, text="Select Grammar Options:", bg='light gray',
                font=('Arial', 14, 'bold')).pack(pady=10)
        self.setup_options(
            right_pane,
            "Do you know the Number of the word?",
            [("Singular", "Singular / ਇਕ"), ("Plural", "Plural / ਬਹੁ"), ("Not Applicable", "NA")],
            self.number_var
        )
        self.setup_options(
            right_pane,
            "Do you know the Gender of the word?",
            [("Masculine", "Masculine / ਪੁਲਿੰਗ"), ("Feminine", "Feminine / ਇਸਤਰੀ"), ("Neutral", "Trans / ਨਪੁਂਸਕ")],
            self.gender_var
        )
        self.setup_options(
            right_pane,
            "Do you know the Part of Speech for the word?",
            [("Noun", "Noun / ਨਾਂਵ"), ("Adjective", "Adjectives / ਵਿਸ਼ੇਸ਼ਣ"),
            ("Adverb", "Adverb / ਕਿਰਿਆ ਵਿਸੇਸ਼ਣ"), ("Verb", "Verb / ਕਿਰਿਆ"),
            ("Pronoun", "Pronoun / ਪੜਨਾਂਵ"), ("Postposition", "Postposition / ਸੰਬੰਧਕ"),
            ("Conjunction", "Conjunction / ਯੋਜਕ")],
            self.pos_var
        )

        # ---------------------------
        # Bottom Button Frame
        # ---------------------------
        button_frame = tk.Frame(self.input_window, bg='light gray')
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="Submit", command=self.submit_input,
                font=('Arial', 12, 'bold'), bg='navy', fg='white',
                padx=30, pady=15).pack(side=tk.LEFT, padx=15)
        tk.Button(button_frame, text="Skip", command=self.skip_input,
                font=('Arial', 12, 'bold'), bg='navy', fg='white',
                padx=30, pady=15).pack(side=tk.LEFT, padx=15)

        # ---------------------------
        # Launch the dictionary lookup in a separate thread
        # ---------------------------
        self.start_progress()
        threading.Thread(target=self.lookup_meanings_thread, args=(word,), daemon=True).start()

        self.input_window.transient(self.root)
        self.input_window.grab_set()
        self.root.wait_window(self.input_window)
        print(f"Input window for {word} closed")

    def lookup_meanings_thread(self, word):
        """
        Performs the dictionary lookup in a separate thread and then
        schedules the update of the meanings UI on the main thread.
        """
        meanings = self.lookup_word_in_dictionary(word)
        # Schedule the UI update on the main thread
        self.root.after(0, lambda: self.update_meanings_ui(meanings))

    def update_meanings_ui(self, meanings):
        """
        Updates the meanings UI with the lookup results.
        Stops the progress bar and populates the meanings section.
        """
        self.stop_progress()  # Stop the progress window now that lookup is complete
        self.accumulate_meanings_data(meanings)
        split_meanings = self.split_meanings_for_display(meanings)
        # Clear any existing widgets in the meanings inner frame
        for widget in self.meanings_inner_frame.winfo_children():
            widget.destroy()
        # Repopulate the meanings UI
        for i, column in enumerate(split_meanings.values()):
            column_frame = tk.Frame(self.meanings_inner_frame, bg='light gray')
            column_frame.grid(row=0, column=i, padx=10, pady=10, sticky='nw')
            for meaning in column:
                tk.Label(column_frame, text=f"- {meaning}", bg='light gray',
                        font=('Arial', 12), wraplength=400, justify=tk.LEFT).pack(anchor='w', padx=15, pady=5)
        self.meanings_inner_frame.update_idletasks()
        self.meanings_canvas.config(scrollregion=self.meanings_inner_frame.bbox("all"))

    def split_meanings_for_display(self, meanings): # Helper function to split meanings into two columns
        # Determine if 'meanings' is a dict or list.
        if isinstance(meanings, dict):
            mlist = meanings.get("meanings", [])
        else:
            mlist = meanings  # Assume it's already a list.
            
        # Now split the list into two halves.
        mid = len(mlist) // 2
        left = mlist[:mid]
        right = mlist[mid:]
        return {"left": left, "right": right}

    def submit_matches(self):
        any_selection = False
        current_entries = []  # Local list for entries of the current word

        # Process matching rule checkboxes as before
        for var, match in self.match_vars:
            if var.get():
                match_string = match[0]
                self.results_text.insert(tk.END, f"{match_string}\n")
                self.results_text.insert(tk.END, "-" * 50 + "\n")
                data = match_string.split(" | ")
                new_entry = {
                    "Word": data[0],
                    "Vowel Ending": data[1],
                    "Number / ਵਚਨ": data[2],
                    "Grammar / ਵਯਾਕਰਣ": data[3],
                    "Gender / ਲਿੰਗ": data[4],
                    "Word Root": data[5],
                    "Word Type": data[6]
                }
                current_entries.append(new_entry)
                any_selection = True

        # Also update the accumulated meanings for the current word
        selected_meanings = [meaning for var, meaning in self.meaning_vars if var.get()]
        self.accumulate_meanings_data(selected_meanings)

        # --- NEW BLOCK: Check for repeated word and prompt update for previous occurrences ---
        current_word = self.pankti_words[self.current_word_index]
        # Find the first occurrence index for the current word
        first_index = next((i for i, w in enumerate(self.pankti_words) if w == current_word), self.current_word_index)

        # Get the current selection from the UI for this occurrence.
        current_selected = selected_meanings  # already computed

        # If this is a repeated occurrence, merge prior selections for this word only.
        if self.current_word_index != first_index:
            merged_meanings = []
            for idx in range(first_index, self.current_word_index):
                # Only merge if the word at that index matches the current word.
                if idx < len(self.accumulated_meanings) and self.pankti_words[idx] == current_word:
                    entry = self.accumulated_meanings[idx]
                    if isinstance(entry, dict):
                        merged_meanings.extend(entry.get("meanings", []))
                    else:
                        merged_meanings.extend(entry)
            # Remove duplicates while preserving order.
            prior_meanings = list(dict.fromkeys(merged_meanings))
            
            # Compare the current selection to prior selections.
            if set(current_selected) != set(prior_meanings):
                update_prev = messagebox.askyesno(
                    "Update Previous Meanings",
                    f"You have selected different meanings for the word '{current_word}'.\n"
                    "Do you want to update the meanings for all previous occurrences of this word?"
                )
                if update_prev:
                    for idx in range(first_index, self.current_word_index):
                        if idx < len(self.accumulated_meanings) and self.pankti_words[idx] == current_word:
                            self.accumulated_meanings[idx] = {"word": current_word, "meanings": current_selected}

        # Finally, update (or add) the current occurrence's accumulated meanings with only the current selection.
        if self.current_word_index < len(self.accumulated_meanings):
            self.accumulated_meanings[self.current_word_index] = {"word": current_word, "meanings": current_selected}
        else:
            self.accumulated_meanings.append({"word": current_word, "meanings": current_selected})

        # --- End NEW BLOCK ---

        # --- Assign verse using word index and verse boundaries ---
        verse_boundaries = []
        pointer = 0
        for verse in self.selected_verses:
            verse_words = verse.split()
            start = pointer
            end = pointer + len(verse_words)
            verse_boundaries.append((start, end))
            pointer = end

        current_verse = None
        for i, (start, end) in enumerate(verse_boundaries):
            if start <= self.current_word_index < end:
                current_verse = self.selected_verses[i]
                break

        # Attach current verse to each grammar entry
        for entry in current_entries:
            entry["Verse"] = current_verse

        # Process finalized matches (avoiding duplicates)
        finalized_matches = []
        for var, match in self.match_vars:
            if var.get():
                match_word = match[0].split(" | ")[0]
                for entry in current_entries:
                    if entry["Word"] == match_word and entry not in finalized_matches:
                        finalized_matches.append(entry)
        self.accumulate_finalized_matches(finalized_matches)
            
        if not any_selection:
            messagebox.showwarning("No Selection", "No matches were selected. Please select at least one match.")
        else:
            self.match_window.destroy()
            # Add the current word's entries to the global accumulator
            self.all_new_entries.extend(current_entries)
            self.current_word_index += 1
            self.process_next_word()

    def show_matches(self, matches, pankti, meanings, max_display=30):
        # Destroy any existing match window
        if hasattr(self, 'match_window') and self.match_window.winfo_exists():
            self.match_window.destroy()

        # Create the match window
        self.match_window = tk.Toplevel(self.root)
        self.match_window.title("Select Matches and Meanings")
        self.match_window.configure(bg='light gray')
        self.match_window.state('zoomed')

        # Reset check-variable lists for matches and meanings
        self.match_vars = []      # For matching rule checkboxes
        self.meaning_vars = []    # For meaning checkboxes
        unique_matches = self.filter_unique_matches(matches)
        self.all_matches.append(unique_matches)

        # ---------------------------
        # Display the complete Pankti at the top
        # ---------------------------
        pankti_frame = tk.Frame(self.match_window, bg='light gray')
        pankti_frame.pack(fill=tk.BOTH, padx=30, pady=20)

        pankti_display = tk.Text(pankti_frame, wrap=tk.WORD, bg='light gray',
                                font=('Arial', 32), height=2, padx=5, pady=5)
        pankti_display.pack(fill=tk.BOTH, expand=False)
        pankti_display.insert(tk.END, f"{pankti}")
        pankti_display.tag_add("center", "1.0", "end")
        pankti_display.tag_configure("center", justify='center')
        pankti_display.config(state=tk.DISABLED)

        # Compute the character offset for the word at self.current_word_index
        words = pankti.split()
        start_idx = 0
        for i, w in enumerate(words):
            if i == self.current_word_index:
                break
            # +1 accounts for the space between words
            start_idx += len(w) + 1
        end_idx = start_idx + len(words[self.current_word_index])

        pankti_display.tag_add("highlight", f"1.{start_idx}", f"1.{end_idx}")
        pankti_display.tag_config("highlight", foreground="red", font=('Arial', 32, 'bold'))
        pankti_display.config(state=tk.DISABLED)

        # ---------------------------
        # Create a main frame to hold both the Meanings and the Matching Rules sections
        # ---------------------------
        main_frame = tk.Frame(self.match_window, bg='light gray')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # ---------------------------
        # Left Pane: Display Meanings as Checkboxes
        # ---------------------------
        meanings_frame = tk.Frame(main_frame, bg='light gray')
        meanings_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        tk.Label(meanings_frame, text=f"Select Meanings for {self.pankti_words[self.current_word_index]}:",
                bg='light gray', font=('Arial', 14, 'bold')).pack(pady=10)
        # NEW: Add a toggle checkbutton to select/deselect all meanings
        self.select_all_meanings_var = tk.BooleanVar(value=True)
        tk.Checkbutton(meanings_frame, text="Select/Deselect All Meanings",
                    variable=self.select_all_meanings_var, bg='light gray',
                    font=('Arial', 12), command=self.toggle_all_meanings).pack(pady=5)

        meanings_canvas = tk.Canvas(meanings_frame, bg='light gray', borderwidth=0)
        meanings_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        meanings_scrollbar = tk.Scrollbar(meanings_frame, orient=tk.VERTICAL, command=meanings_canvas.yview)
        meanings_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        meanings_canvas.config(yscrollcommand=meanings_scrollbar.set)

        meanings_content = tk.Frame(meanings_canvas, bg='light gray')
        meanings_canvas.create_window((0, 0), window=meanings_content, anchor='nw')

        # Split the meanings into two columns and create a checkbox for each meaning
        split_meanings = self.split_meanings_for_display(meanings)
        # --- Determine if the current word is repeated and merge prior selections ---
        current_word = self.pankti_words[self.current_word_index]
        first_index = next((i for i, w in enumerate(self.pankti_words) if w == current_word), self.current_word_index)

        # Merge meanings from all occurrences from the first occurrence up to (but not including) the current occurrence.
        merged_meanings = []
        for idx in range(first_index, self.current_word_index):
            if idx < len(self.accumulated_meanings):
                entry = self.accumulated_meanings[idx]
                if isinstance(entry, dict):
                    merged_meanings.extend(entry.get("meanings", []))
                else:
                    merged_meanings.extend(entry)
        # Remove duplicates while preserving order
        prior_meanings = list(dict.fromkeys(merged_meanings))

        # If this is a repeated occurrence (current index is not the first occurrence), reorder the meanings.
        if self.current_word_index != first_index:
            # Obtain the current meanings list
            if isinstance(meanings, dict):
                current_meanings = meanings.get("meanings", [])
            else:
                current_meanings = meanings
            # Reorder: meanings from the first occurrence first, then the rest.
            reordered = [m for m in current_meanings if m in prior_meanings]
            reordered += [m for m in current_meanings if m not in prior_meanings]
            if isinstance(meanings, dict):
                meanings["meanings"] = reordered
            else:
                meanings = reordered

        # Now split the meanings for display using the (possibly) reordered meanings.
        split_meanings = self.split_meanings_for_display(meanings)

        # --- Create the checkboxes as before ---
        for i, column in enumerate(split_meanings.values()):
            column_frame = tk.Frame(meanings_content, bg='light gray')
            column_frame.grid(row=0, column=i, padx=10, pady=10, sticky='nw')
            for meaning in column:
                # For repeated occurrences, preselect if the meaning was chosen in the first occurrence,
                # and highlight those checkbuttons with yellow.
                if self.current_word_index != first_index:
                    preselect = meaning in prior_meanings
                    bg_color = "yellow" if preselect else "light gray"
                else:
                    preselect = True
                    bg_color = "light gray"
                var = tk.BooleanVar(value=preselect)
                chk = tk.Checkbutton(
                    column_frame,
                    text=f"- {meaning}",
                    variable=var,
                    bg=bg_color,
                    font=('Arial', 12),
                    wraplength=325,
                    anchor='w',
                    justify=tk.LEFT,
                    selectcolor='light blue'
                )
                chk.pack(anchor='w', padx=15, pady=5)
                self.meaning_vars.append((var, meaning))

        meanings_content.update_idletasks()
        meanings_canvas.config(scrollregion=meanings_canvas.bbox("all"))

        # ---------------------------
        # Right Pane: Display Matching Rules as Checkboxes
        # ---------------------------
        matches_frame = tk.Frame(main_frame, bg='light gray')
        matches_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        tk.Label(matches_frame, text="Select the matching rules:",
                bg='light gray', font=('Arial', 14, 'bold')).pack(pady=10)

        matches_canvas = tk.Canvas(matches_frame, bg='light gray', borderwidth=0)
        matches_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        matches_scrollbar = tk.Scrollbar(matches_frame, orient=tk.VERTICAL, command=matches_canvas.yview)
        matches_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        matches_canvas.config(yscrollcommand=matches_scrollbar.set)

        matches_content = tk.Frame(matches_canvas, bg='light gray')
        matches_canvas.create_window((0, 0), window=matches_content, anchor='nw')

        # Display each match with a checkbox
        for match in unique_matches[:max_display]:
            var = tk.BooleanVar()
            tk.Checkbutton(matches_content, text=f"{match[0]} (Matching Characters: {match[1]})",
                        variable=var, bg='light gray', selectcolor='light blue', anchor='w'
                        ).pack(fill=tk.X, padx=10, pady=5)
            self.match_vars.append((var, match))

        matches_content.update_idletasks()
        matches_canvas.config(scrollregion=matches_canvas.bbox("all"))

        # ---------------------------
        # Bottom Button Frame: Submit and Back
        # ---------------------------
        button_frame = tk.Frame(self.match_window, bg='light gray')
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Submit", command=self.submit_matches,
                font=('Arial', 12, 'bold'), bg='navy', fg='white', padx=20, pady=10
                ).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Back", command=lambda: self.back_to_user_input_with_pankti(pankti),
                font=('Arial', 12, 'bold'), bg='navy', fg='white', padx=20, pady=10
                ).pack(side=tk.LEFT, padx=5)

        print("Match window created and populated.")

    def toggle_all_meanings(self):
        """Toggle all meaning checkboxes based on the select-all checkbutton."""
        new_value = self.select_all_meanings_var.get()
        for var, meaning in self.meaning_vars:
            var.set(new_value)

    def load_grammar_data(self, file_path):
        """
        Loads grammar data from a CSV file.

        Args:
        file_path (str): The path to the CSV file containing grammar data.

        Returns:
        list: A list of dictionaries containing the grammar data.

        Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If an error occurs while reading the file.
        """
        try:
            with open(file_path, "r", encoding='utf-8') as data_base:
                return list(csv.DictReader(data_base))
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' does not exist.")
            return []
        except IOError as e:
            print(f"Error reading file '{file_path}': {e}")
            return []

    def break_into_characters(self, word):
        """Breaks a word into individual characters."""
        return [char for char in unicodedata.normalize('NFC', word)]

    def match_inflections(self, word, inflection, pos):
        """
        Determines the number of Matching Characters between the word and the inflection pattern,
        considering the part of speech. Matches are weighted by position and continuity.

        Args:
        word (str): The word to check.
        inflection (str): The inflection pattern to match against.
        pos (str): The part of speech to consider.

        Returns:
        int: The number of Matching Characters, weighted by position and continuity.
        """
        # Break the word and inflection into individual characters
        word_chars = self.break_into_characters(word)
        inflection_chars = self.break_into_characters(inflection)

        # Only consider specified endings for nouns
        if (pos == "Noun / ਨਾਂਵ" or pos == "Adjectives / ਵਿਸ਼ੇਸ਼ਣ") and inflection == 'ਮੁਕਤਾ':
            return 0  # No suffix match needed for this case

        # Initialize the match count
        match_count = 0

        # Determine the minimum length between word and inflection for suffix comparison
        min_length = min(len(word_chars), len(inflection_chars))

        # Iterate through the characters in reverse order (from the end of the word and inflection)
        for i in range(1, min_length + 1):
            if word_chars[-i] == inflection_chars[-i]:
                # Increment the match count with a weight factor based on position
                match_count += i  # Giving more weight to matches that occur further back in the word
            else:
                break  # Stop the loop if a mismatch is found (ensuring continuity)

        return match_count  # Return the weighted match count

    def lookup_word_in_dictionary(self, word):
        """
        Looks up the meanings of a word in the dictionary data.

        Args:
        word (str): The word to look up in the dictionary.

        Returns:
        list: A list of meanings for the word.
        """
        meanings = []
        exact_meanings = []

        # Attempt to find the word directly in the dictionary
        result = self.dictionary_data[self.dictionary_data['Word'] == word]
        if not result.empty:
            exact_meanings = ast.literal_eval(result.iloc[0]['Meanings'])
            print(f"Found exact match for: {word}")

        # Search for the word within combined entries regardless of exact match
        combined_entries = []
        for _, row in self.dictionary_data.iterrows():
            combined_word = row['Word']
            combined_word_list = re.split(r'\s+', combined_word)  # Split by whitespace to handle combined words

            if word in combined_word_list:  # Check if the exact word is in the list of combined words
                print(f"Found exact match in combined entry: {row['Word']}")
                combined_entries.append(row)

        # If combined entries are found, proceed with adjacent word search
        adjacent_word_matches = []
        if combined_entries:
            words_in_pankti = self.accumulated_pankti.split()  # Split pankti into words
            word_index = words_in_pankti.index(word) if word in words_in_pankti else -1

            # Identify adjacent words in the pankti
            adjacent_combinations = []
            if word_index != -1:
                # Two-word combinations (main word + adjacent)
                if word_index > 0:  # Previous word
                    adjacent_combinations.append([words_in_pankti[word_index - 1], word])
                if word_index < len(words_in_pankti) - 1:  # Next word
                    adjacent_combinations.append([word, words_in_pankti[word_index + 1]])

                # Three-word combinations (main word + two adjacents)
                if word_index < len(words_in_pankti) - 2:
                    adjacent_combinations.append([words_in_pankti[word_index], words_in_pankti[word_index + 1], words_in_pankti[word_index + 2]])
                if word_index > 0 and word_index < len(words_in_pankti) - 1:
                    adjacent_combinations.append([words_in_pankti[word_index - 1], words_in_pankti[word_index], words_in_pankti[word_index + 1]])
                if word_index >= 2:
                    adjacent_combinations.append([words_in_pankti[word_index - 2], words_in_pankti[word_index - 1], words_in_pankti[word_index]])

            # Now search within combined entries using adjacent word combinations
            for entry in combined_entries:
                combined_word_list = re.split(r'\s+', entry['Word'])  # Split by whitespace to handle combined words

                for combination in adjacent_combinations:
                    # Convert the combination to possible strings to match
                    combination_strings = [' '.join(combination), ' '.join(combination[::-1])]
                    
                    if any(comb_str in entry['Word'] for comb_str in combination_strings):
                        print(f"Found adjacent match in combined entry: {entry['Word']}")
                        combined_meanings = ast.literal_eval(entry['Meanings'])
                        combined_entry = f"{entry['Word']}: {', '.join(combined_meanings)}"
                        adjacent_word_matches.append(combined_entry)

            # Sort the adjacent matches to prioritize three-word matches
            adjacent_word_matches = sorted(adjacent_word_matches, key=lambda x: len(x.split(' ')), reverse=True)

        # If both exact match and adjacent word matches are found, return adjacent first
        if adjacent_word_matches and exact_meanings:
            return adjacent_word_matches + exact_meanings

        # If only exact match is found, return exact match
        if exact_meanings:
            return exact_meanings

        # If only adjacent word matches are found, return them
        if adjacent_word_matches:
            return adjacent_word_matches

        # If no adjacent word matches are found, return original combined entries meanings
        for entry in combined_entries:
            combined_meanings = ast.literal_eval(entry['Meanings'])
            combined_entry = f"{entry['Word']}: {', '.join(combined_meanings)}"
            meanings.append(combined_entry)

        # If meanings are found, return them
        if meanings:
            return meanings

        # If no meaning is found, return a list with a single string message
        return [f"No meanings found for {word}"]

    def back_to_user_input_with_pankti(self, pankti):
        """
        Allows the user to return to the input stage for the current word, with pankti passed as an argument.
        """
        try:
            if hasattr(self, 'match_window') and self.match_window:
                self.match_window.destroy()  # Close the match window if it exists

            # Ensure the current_word_index is within valid range
            if 0 <= self.current_word_index < len(self.pankti_words):
                word = self.pankti_words[self.current_word_index]  # Get the current word
                self.reset_input_variables()  # Reset selections for the new word
                self.user_input(word, pankti)  # Reopen the input window for the current word and pass pankti
            else:
                messagebox.showerror("Error", "No valid word to return to.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def fetch_data(self, word, pankti):
        try:
            self.reset_input_variables()  # Reset selections for the new word
            print(f"Opening input window for {word}")

            self.user_input(word, pankti)  # Opens the input window with the Pankti

            # Check if input_window exists before waiting
            if hasattr(self, 'input_window') and self.input_window.winfo_exists():
                self.root.wait_window(self.input_window)  # Wait for the input window to close
            else:
                print(f"Input window for {word} did not open properly.")
                return  # Exit if the input window was not opened

            print(f"Input window for {word} closed")

            if not self.input_submitted:
                print(f"No input submitted for {word}. Skipping to next word.")
                self.current_word_index += 1
                self.process_next_word()
            else:
                # Process the submitted input
                self.handle_submitted_input(word)

        except Exception as e:
            print(f"An error occurred while fetching data for {word}: {str(e)}")
            # Ensure the input window is closed in case of an error
            if hasattr(self, 'input_window') and self.input_window.winfo_exists():
                try:
                    self.input_window.destroy()
                except Exception as close_error:
                    print(f"Failed to close input window: {str(close_error)}")
            # Optionally, log the error to a file for future debugging
            with open("error_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"Error with word '{word}': {str(e)}\n")

    def process_next_word(self):
        """Process the next valid word or prompt for saving if finished."""
        pankti = " ".join(self.pankti_words)
        self.current_pankti = pankti

        if self.current_word_index < len(self.pankti_words):
            word = self.pankti_words[self.current_word_index]
            if self.is_non_word_character(word):
                self.current_word_index += 1  # Skip non-word characters
                self.process_next_word()
            else:
                self.fetch_data(word, pankti)  # Process current word
        else:
            # All words processed—prompt to save using the global accumulator
            self.save_results_btn.config(state=tk.NORMAL)
            self.prompt_save_results(self.all_new_entries)

    def skip_input(self):
        """
        Handles the action when the user decides to skip the current word.
        """
        try:
            # Ask for user confirmation before skipping
            confirm_skip = messagebox.askyesno("Confirm Skip", "Are you sure you want to skip this word?")
            if not confirm_skip:
                return  # Do nothing if the user cancels the skip

            # Mark input as not submitted and close the input window
            self.input_submitted = False
            self.input_window.destroy()

            # Update the index to move to the next word and process it
            self.current_word_index += 1
            self.process_next_word()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while skipping: {e}")

    def submit_input(self):
        self.input_submitted = True
        if hasattr(self, 'input_window') and self.input_window.winfo_exists():
            self.input_window.destroy()

        # Start the progress bar
        self.start_progress()

        # Run the search in a separate thread
        search_thread = threading.Thread(target=self.perform_search_and_finish)
        search_thread.start()

    def perform_search_and_finish(self):
        current_word = self.pankti_words[self.current_word_index]
        number = self.number_var.get()
        gender = self.gender_var.get()
        pos = self.pos_var.get()

        print(f"Processing word: {current_word}, Number: {number}, Gender: {gender}, POS: {pos}")
        
        matches = []
        
        if number == "NA" and gender == "NA" and pos == "NA":
            matches = self.search_by_inflections(current_word)
        else:
            matches = self.search_by_criteria(current_word, number, gender, pos)
            if not matches:
                messagebox.showinfo("No Matches Found", "No matches were found as per the criteria given by you. Now conducting a general search.")
                matches = self.search_by_inflections(current_word)

        # Check if meanings are already accumulated for the current word index
        if len(self.accumulated_meanings) > self.current_word_index:
            entry = self.accumulated_meanings[self.current_word_index]
            # If the entry is a dictionary, extract the meanings list; otherwise assume it's already a list.
            if isinstance(entry, dict):
                meanings = entry.get("meanings", [])
            else:
                meanings = entry
            self.handle_lookup_results(matches, meanings)
        else:
            # Launch the dictionary lookup in a separate thread if no meanings are accumulated.
            self.perform_dictionary_lookup(current_word, lambda meanings: self.handle_lookup_results(matches, meanings))

        # Stop the progress bar once done (use Tkinter's `after` to ensure it runs in the main thread)
        self.root.after(0, self.stop_progress)

        if matches:
            print(f"Found matches for {current_word}: {matches}")
            # Ensure current_pankti and meanings are passed to show_matches
            self.root.after(0, lambda: self.show_matches(matches, self.current_pankti, meanings))
        else:
            self.root.after(0, lambda: messagebox.showinfo("No Matches", f"No matches found for the word: {current_word}"))
            self.current_word_index += 1
            self.root.after(0, self.process_next_word)

    def is_non_word_character(self, word):
        """
        Determines if the given word consists solely of non-word characters.

        Args:
        word (str): The word to be checked.

        Returns:
        bool: True if the word consists only of non-word characters; False otherwise.
        """
        # Regular expression pattern to match non-word characters and digits
        pattern = r"^[^\w\s]*[\d॥]+[^\w\s]*$"

        # Check if the word matches the pattern
        return re.match(pattern, word) is not None

    def search_by_criteria(self, word, number, gender, pos):
        matches = []
        seen = set()  # To store unique combinations

        # Part of Speech: Noun, Verb
        if pos in ["Noun / ਨਾਂਵ", "Verb / ਕਿਰਿਆ"]:
            specified_endings = [
                "ੌ", "ੋ", "ੈ", "ੇ", "ੂ", "ੁ", "ੀਹੋ", "ੀਹੂ", "ੀਏ", "ੀਈਂ", "ੀਈ",
                "ੀਆ", "ੀਅੈ", "ੀਅਹੁ", "ੀਓ", "ੀਂ", "ੀ", "ਿਨ", "ਿਹੋ", "ਿਈਂ", "ਿਆਂ",
                "ਿਆ", "ਿਅਨ", "ਿਅਹੁ", "ਿ", "ਾਰੂ", "ਾਹੁ", "ਾਹਿ", "ਾਂ", "ਾ", "ਹਿ",
                "ਸੈ", "ਸ", "ਈਦਿ", "ਈ", "ਉ", "ਹਿਉ", "ਗਾ", "ਆ", "ਇ"
            ]

            # Determine if the word is truly inflectionless
            is_inflectionless = all(not word.endswith(ending) for ending in specified_endings)

            # Iterate through each rule in the grammar data
            for rule in self.grammar_data:
                current_number = number if number != "NA" else rule['Number / ਵਚਨ']
                current_gender = gender if gender != "NA" else rule['Gender / ਲਿੰਗ']
                current_pos = pos if pos != "NA" else rule['Type']

                # Handle the 'ਮੁਕਤਾ' case
                include_mukta = is_inflectionless and current_pos == "Noun / ਨਾਂਵ"

                if include_mukta and rule['\ufeffVowel Ending'] == "ਮੁਕਤਾ" and rule['Number / ਵਚਨ'] == current_number and rule['Gender / ਲਿੰਗ'] == current_gender and rule['Type'] == current_pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / ਵਚਨ', ""),
                        rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                        rule.get('Gender / ਲਿੰਗ', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = (1, 100.0)
                    matches.append((result, match_count, match_percentage))
                elif not include_mukta and rule['Number / ਵਚਨ'] == current_number and rule['Gender / ਲਿੰਗ'] == current_gender and rule['Type'] == current_pos:
                    # Regular inflection matching
                    inflections = rule['\ufeffVowel Ending'].split()
                    for inflection in inflections:
                        match_count, match_percentage = self.calculate_match_metrics(word, inflection)
                        if match_count > 0:
                            result = " | ".join([
                                word,
                                inflection,
                                rule.get('Number / ਵਚਨ', ""),
                                rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                                rule.get('Gender / ਲਿੰਗ', ""),
                                rule.get('Word Root', ""),
                                rule.get('Type', "")
                            ])
                            matches.append((result, match_count, match_percentage))

        # Part of Speech: Adjective (Always perform both searches)
        elif pos == "Adjectives / ਵਿਸ਼ੇਸ਼ਣ":
            specified_endings = [
                "ੌ", "ੋ", "ੈ", "ੇ", "ੂ", "ੁ", "ੀਹੋ", "ੀਹੂ", "ੀਏ", "ੀਈਂ", "ੀਈ",
                "ੀਆ", "ੀਅੈ", "ੀਅਹੁ", "ੀਓ", "ੀਂ", "ੀ", "ਿਨ", "ਿਹੋ", "ਿਈਂ", "ਿਆਂ",
                "ਿਆ", "ਿਅਨ", "ਿਅਹੁ", "ਿ", "ਾਰੂ", "ਾਹੁ", "ਾਹਿ", "ਾਂ", "ਾ", "ਹਿ",
                "ਸੈ", "ਸ", "ਈਦਿ", "ਈ", "ਉ", "ਹਿਉ", "ਗਾ", "ਆ", "ਇ"
            ]

            # Determine if the word is truly inflectionless
            is_inflectionless = all(not word.endswith(ending) for ending in specified_endings)

            for rule in self.grammar_data:
                current_number = number if number != "NA" else rule['Number / ਵਚਨ']
                current_gender = gender if gender != "NA" else rule['Gender / ਲਿੰਗ']
                current_pos = pos if pos != "NA" else rule['Type']

                # Handle the 'ਮੁਕਤਾ' case
                include_mukta = is_inflectionless and current_pos == "Adjectives / ਵਿਸ਼ੇਸ਼ਣ"

                # Handle inflections (like Nouns)
                if include_mukta and rule['\ufeffVowel Ending'] == "ਮੁਕਤਾ" and rule['Number / ਵਚਨ'] == current_number and rule['Gender / ਲਿੰਗ'] == current_gender and rule['Type'] == current_pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / ਵਚਨ', ""),
                        rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                        rule.get('Gender / ਲਿੰਗ', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = (1, 100.0)
                    matches.append((result, match_count, match_percentage))
                elif not include_mukta and rule['Number / ਵਚਨ'] == current_number and rule['Gender / ਲਿੰਗ'] == current_gender and rule['Type'] == current_pos:
                    inflections = rule['\ufeffVowel Ending'].split()
                    for inflection in inflections:
                        match_count, match_percentage = self.calculate_match_metrics(word, inflection)
                        if match_count > 0:
                            result = " | ".join([
                                word,
                                inflection,
                                rule.get('Number / ਵਚਨ', ""),
                                rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                                rule.get('Gender / ਲਿੰਗ', ""),
                                rule.get('Word Root', ""),
                                rule.get('Type', "")
                            ])
                            matches.append((result, match_count, match_percentage))

                # Also check for exact matches (like Pronouns)
                if word in rule['\ufeffVowel Ending'] and rule['Number / ਵਚਨ'] == current_number and rule['Gender / ਲਿੰਗ'] == current_gender and rule['Type'] == current_pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / ਵਚਨ', ""),
                        rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                        rule.get('Gender / ਲਿੰਗ', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

        # Part of Speech: Pronoun
        elif pos == "Pronoun / ਪੜਨਾਂਵ":
            for rule in self.grammar_data:
                current_number = number if number != "NA" else rule['Number / ਵਚਨ']
                current_gender = gender if gender != "NA" else rule['Gender / ਲਿੰਗ']

                if word in rule['\ufeffVowel Ending'] and rule['Number / ਵਚਨ'] == current_number and rule['Gender / ਲਿੰਗ'] == current_gender and rule['Type'] == pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / ਵਚਨ', ""),
                        rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                        rule.get('Gender / ਲਿੰਗ', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

        # Part of Speech: Adverb, Postposition, Conjunction
        elif pos in ["Adverb / ਕਿਰਿਆ ਵਿਸੇਸ਼ਣ", "Postposition / ਸੰਬੰਧਕ", "Conjunction / ਯੋਜਕ"]:
            for rule in self.grammar_data:
                if word in rule['\ufeffVowel Ending'] and rule['Type'] == pos:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / ਵਚਨ', ""),
                        rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                        rule.get('Gender / ਲਿੰਗ', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

        # Use filter_unique_matches to remove duplicates and sort the results
        unique_sorted_matches = self.filter_unique_matches(matches)

        return unique_sorted_matches

    def search_by_inflections(self, word):
        """
        Searches for inflection matches for the given word within the grammar data.

        Args:
        word (str): The word to search for inflections.

        Returns:
        list: A list of tuples representing matched grammatical rules for the word,
            along with match count and match percentage.
        """
        matches = []
        seen = set()  # To store unique combinations

        # Define the specified endings for inflectionless check
        specified_endings = [
            "ੌ", "ੋ", "ੈ", "ੇ", "ੂ", "ੁ", "ੀਹੋ", "ੀਹੂ", "ੀਏ", "ੀਈਂ", "ੀਈ",
            "ੀਆ", "ੀਅੈ", "ੀਅਹੁ", "ੀਓ", "ੀਂ", "ੀ", "ਿਨ", "ਿਹੋ", "ਿਈਂ", "ਿਆਂ",
            "ਿਆ", "ਿਅਨ", "ਿਅਹੁ", "ਿ", "ਾਰੂ", "ਾਹੁ", "ਾਹਿ", "ਾਂ", "ਾ", "ਹਿ",
            "ਸੈ", "ਸ", "ਈਦਿ", "ਈ", "ਉ", "ਓ", "ਹਿਉ", "ਗਾ", "ਆ", "ਇ"
        ]

        # Determine if the word is truly inflectionless
        try:
            is_inflectionless = all(not word.endswith(ending) for ending in specified_endings)
        except Exception as e:
            print(f"Error determining if the word '{word}' is inflectionless: {str(e)}")
            is_inflectionless = False  # Default to False if there's an error

        for rule in self.grammar_data:
            rule_pos = rule['Type']

            # Noun, Adjective, and Verb processing
            if rule_pos in ["Noun / ਨਾਂਵ", "Adjectives / ਵਿਸ਼ੇਸ਼ਣ", "Verb / ਕਿਰਿਆ"]:
                include_mukta = is_inflectionless and (rule_pos == "Noun / ਨਾਂਵ" or rule_pos == "Adjectives / ਵਿਸ਼ੇਸ਼ਣ")

                if include_mukta and rule['\ufeffVowel Ending'] == "ਮੁਕਤਾ":
                    # Handle the 'ਮੁਕਤਾ' case
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / ਵਚਨ', ""),
                        rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                        rule.get('Gender / ਲਿੰਗ', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = (1, 100.0)
                    matches.append((result, match_count, match_percentage))
                else:
                    # Regular inflection matching
                    inflections = rule['\ufeffVowel Ending'].split()
                    for inflection in inflections:
                        match_count, match_percentage = self.calculate_match_metrics(word, inflection)
                        if match_count > 0:
                            result = " | ".join([
                                word,
                                inflection,
                                rule.get('Number / ਵਚਨ', ""),
                                rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                                rule.get('Gender / ਲਿੰਗ', ""),
                                rule.get('Word Root', ""),
                                rule.get('Type', "")
                            ])
                            matches.append((result, match_count, match_percentage))
                    # Hybrid handling for Adjectives
                    if rule_pos == "Adjectives / ਵਿਸ਼ੇਸ਼ਣ" and word in rule['\ufeffVowel Ending']:
                        result = " | ".join([
                            word,
                            rule.get('\ufeffVowel Ending', ""),
                            rule.get('Number / ਵਚਨ', ""),
                            rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                            rule.get('Gender / ਲਿੰਗ', ""),
                            rule.get('Word Root', ""),
                            rule.get('Type', "")
                        ])
                        match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                        matches.append((result, match_count, match_percentage))

            # Pronoun processing
            elif rule_pos == "Pronoun / ਪੜਨਾਂਵ":
                if word in rule['\ufeffVowel Ending']:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / ਵਚਨ', ""),
                        rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                        rule.get('Gender / ਲਿੰਗ', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

            # Adverb, Postposition, and Conjunction processing
            elif rule_pos in ["Adverb / ਕਿਰਿਆ ਵਿਸੇਸ਼ਣ", "Postposition / ਸੰਬੰਧਕ", "Conjunction / ਯੋਜਕ"]:
                if word in rule['\ufeffVowel Ending']:
                    result = " | ".join([
                        word,
                        rule.get('\ufeffVowel Ending', ""),
                        rule.get('Number / ਵਚਨ', ""),
                        rule.get('Grammar / ਵਯਾਕਰਣ', ""),
                        rule.get('Gender / ਲਿੰਗ', ""),
                        rule.get('Word Root', ""),
                        rule.get('Type', "")
                    ])
                    match_count, match_percentage = self.calculate_match_metrics(word, rule['\ufeffVowel Ending'])
                    matches.append((result, match_count, match_percentage))

        # Use filter_unique_matches to remove duplicates and sort the results
        unique_sorted_matches = self.filter_unique_matches(matches)

        return unique_sorted_matches

    def analyze_pankti(self):
        """
        1) Get user’s typed verse/pankti.
        2) Fuzzy-match it against SGGS data.
        3) Show radio buttons for each match so user can select exactly one.
        """
        user_input = self.pankti_entry.get().strip()
        if not user_input:
            messagebox.showerror("Error", "Please enter some text to analyze.")
            return

        # 1) Fuzzy-match the verse in SGGS data (example function)
        candidate_matches = self.match_sggs_verse(user_input)
        if not candidate_matches:
            messagebox.showinfo("No SGGS Match", "No matching verses found in SGGS. Continuing with grammar analysis.")
            # If you still want to do grammar analysis with the typed input:
            self.finish_grammar_analysis(user_input)
            return
        else:
            # Show a new window with radio buttons
            self.show_sggs_matches_option(candidate_matches, user_input)

    def load_sggs_data(self):
        """
        Loads the SGGS data from an Excel file while displaying a modal progress bar.
        The main window is disabled (to prevent user interaction) while the heavy work runs in a background thread.
        The main thread enters a loop to update the UI (so the progress bar animates) until the data is loaded.
        """
        # Disable the main window to prevent interaction
        self.root.attributes("-disabled", True)

        # Show the progress bar modally on the main thread
        self.start_progress()
        self.root.update()  # Ensure the progress window appears immediately

        # This flag will be set when loading is complete.
        self.loading_done = False

        import threading

        def heavy_work():
            # Perform the heavy work (reading and processing the Excel file)
            data = pd.read_excel("1.1.3 sggs_extracted_with_page_numbers.xlsx")
            headers = list(data.columns)
            data['NormalizedVerse'] = (
                data['Verse']
                .astype(str)
                .str.lower()
                .str.strip()
            )
            # Schedule the finalization on the main thread.
            def finish():
                self.sggs_data = data
                self.sggs_headers = headers
                self.loading_done = True
            self.root.after(0, finish)

        # Run the heavy work in a background thread
        threading.Thread(target=heavy_work, daemon=True).start()

        # Process the event loop until loading is done (this allows the progress bar to animate)
        while not self.loading_done:
            self.root.update_idletasks()
            self.root.update()

        # Re-enable the main window now that the heavy work is complete
        self.root.attributes("-disabled", False)
        self.stop_progress()

    def match_sggs_verse(self, user_input, max_results=10, min_score=60):
        """
        Fuzzy-match the user's input (pankti) against the SGGS 'Verse' column.
        Return a tuple (headers, candidate_matches) where headers is the list
        of all column names from the Excel file, and candidate_matches is a list
        (up to max_results) of best matches above the min_score similarity.
        """
        # Ensure we have loaded the data and headers
        if not hasattr(self, 'sggs_data'):
            self.load_sggs_data()
        
        headers = self.sggs_headers
        normalized_input = user_input.lower().strip()
        candidate_matches = []

        # Disable the main window to block user interaction during matching
        self.root.attributes("-disabled", True)
        # Start the modal progress bar
        self.start_progress()
        self.root.update()  # Ensure progress window appears

        total_rows = len(self.sggs_data)
        # Iterate over the rows in SGGS data
        for i, (_, row) in enumerate(self.sggs_data.iterrows()):
            verse_text = row['NormalizedVerse']
            # Remove extra spaces around numbers within "॥" markers
            verse_text = re.sub(r'॥\s*(\d+)\s*॥', r'॥\1॥', verse_text)
            score = fuzz.token_sort_ratio(normalized_input, verse_text)
            if score >= min_score:
                candidate_matches.append({
                    'S. No.': row['S. No.'],
                    'Verse': row['Verse'],
                    'Verse No.': row.get('Verse No.'),
                    'Stanza No.': row['Stanza No.'],
                    'Text Set No.': row.get('Text Set No.'),
                    'Raag (Fixed)': row['Raag (Fixed)'],
                    'Sub-Raag': row.get('Sub-Raag'),
                    'Writer (Fixed)': row['Writer (Fixed)'],
                    'Verse Configuration (Optional)': row.get('Verse Configuration (Optional)'),
                    'Stanza Configuration (Optional)': row.get('Stanza Configuration (Optional)'),
                    'Bani Name': row['Bani Name'],
                    'Musical Note Configuration': row.get('Musical Note Configuration'),
                    'Special Type Demonstrator': row.get('Special Type Demonstrator'),
                    'Type': row.get('Type'),
                    'Page Number': row['Page Number'],
                    'Score': score
                })
            if i % 50 == 0:
                self.root.update_idletasks()
                self.root.update()

        # Sort the candidate matches by descending score and select the top results.
        candidate_matches.sort(key=lambda x: x['Score'], reverse=True)

        # Stop the progress bar and re-enable the main window.
        self.stop_progress()
        self.root.attributes("-disabled", False)

        return headers, candidate_matches[:max_results]

    def show_sggs_matches_option(self, candidate_matches, user_input):
        """
        Display fuzzy SGGS matches as radio buttons so the user can choose one.
        The header will also include the user input verse.
        """

        # 1) If the first item is a header list, strip it off:
        if candidate_matches and isinstance(candidate_matches[0], list):
            # This is presumably the header row
            self.header_row = candidate_matches[0]
            # If there's a second element and it's a list of dicts, use that
            if len(candidate_matches) > 1 and isinstance(candidate_matches[1], list):
                candidate_matches = candidate_matches[1]
            else:
                # No real data after the header
                candidate_matches = []

        # 2) Store matches for later reference
        self.candidate_matches = candidate_matches

        # 3) Destroy if there's an existing option window
        if hasattr(self, 'sggs_option_window') and self.sggs_option_window.winfo_exists():
            self.sggs_option_window.destroy()

        # 4) Create a new Toplevel window
        self.sggs_option_window = tk.Toplevel(self.root)
        self.sggs_option_window.title("Select One Matching Verse")
        self.sggs_option_window.configure(bg='light gray')
        self.sggs_option_window.state("zoomed")

        # 5) A Tk variable that holds the index of the selected match
        self.sggs_option_var = tk.IntVar(value=-1)  # -1 = nothing selected

        # 6) Header label
        header_label = tk.Label(
            self.sggs_option_window,
            text=f"Fuzzy Matches Found for '{user_input}'. Please select one:",
            bg='dark slate gray',
            fg='white',
            font=('Arial', 16, 'bold'),
            pady=10
        )
        header_label.pack(fill=tk.X)

        # 7) Scrollable frame for radio buttons
        frame = tk.Frame(self.sggs_option_window, bg='light gray')
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(frame, bg='light gray', borderwidth=0)
        vsb = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg='light gray')

        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # 8) Populate the scroll_frame with radio buttons
        for idx, match in enumerate(candidate_matches):
            # We now expect match to be a dict. But if there's a chance
            # it might be something else, you can still do an isinstance check:
            if isinstance(match, dict):
                # Get the score value
                raw_score = match.get('Score', '?')
                # Attempt to convert it to float and format with 2 decimals
                try:
                    score_float = float(raw_score)
                    score_str = f"{score_float:.2f}"
                except ValueError:
                    # If it's not a valid float (e.g. '?'), just show it as is
                    score_str = str(raw_score)
                verse = match.get('Verse', '')
                raag = match.get('Raag (Fixed)', '')
                writer = match.get('Writer (Fixed)', '')
                bani = match.get('Bani Name', '')
                page = match.get('Page Number', '')
            else:
                # Fallback if it's not a dict, adjust indices to your structure
                score = match[7] if len(match) > 7 else '?'
                verse = match[1] if len(match) > 1 else ''
                raag = match[2] if len(match) > 2 else ''
                writer = match[3] if len(match) > 3 else ''
                bani = match[4] if len(match) > 4 else ''
                page = match[5] if len(match) > 5 else ''

            # Convert them to strings and handle 'nan' or empty strings
            def clean_value(val):
                if not val or str(val).lower() == 'nan':
                    return ''
                return str(val)

            raag = clean_value(raag)
            writer = clean_value(writer)
            bani = clean_value(bani)
            page = clean_value(page)

            # Build the info line with only non-empty fields
            info_parts = []
            if raag:
                info_parts.append(f"Raag: {raag}")
            if writer:
                info_parts.append(f"Writer: {writer}")
            if bani:
                info_parts.append(f"Bani: {bani}")
            if page:
                info_parts.append(f"Page: {page}")
            info_line = " | ".join(info_parts)

            # Build the label text
            label_text = f"Match #{idx+1} - Score: {score_str}%\nVerse: {verse}"
            if info_line:
                label_text += f"\n{info_line}"

            rb = tk.Radiobutton(
                scroll_frame, text=label_text,
                variable=self.sggs_option_var, value=idx,
                bg='light gray', anchor='w', justify=tk.LEFT,
                wraplength=800,  # adjust as needed
                font=('Arial', 12), selectcolor='light blue'
            )
            rb.pack(fill=tk.X, padx=10, pady=5)

        scroll_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        # 9) Buttons
        btn_frame = tk.Frame(self.sggs_option_window, bg='light gray')
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="Submit",
            command=self.handle_sggs_option_submit,
            font=('Arial', 12, 'bold'), bg='navy', fg='white',
            padx=20, pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame, text="Cancel",
            command=self.sggs_option_window.destroy,
            font=('Arial', 12, 'bold'), bg='red', fg='white',
            padx=20, pady=10
        ).pack(side=tk.LEFT, padx=10)

        print("Match window created and populated.")

    def handle_sggs_option_submit(self):
        idx = self.sggs_option_var.get()
        if idx < 0:
            messagebox.showwarning("No Selection", "Please select one verse match.")
            return

        chosen_match = self.candidate_matches[idx]
        final_input = chosen_match.get('Verse', '')

        if not final_input.strip():
            messagebox.showerror("Error", "The selected verse text is empty. Cannot proceed.")
            return

        # Optionally close the first match window
        self.sggs_option_window.destroy()

        # Now, show the consecutive lines selection
        self.show_consecutive_verses_option(chosen_match, final_input)

    def show_consecutive_verses_option(self, chosen_match, main_verse_text):
        """
        After the user picks the main verse from fuzzy matches,
        let them select additional consecutive lines from the same stanza or text set.
        Ensure the main verse is highlighted and only consecutive verses can be selected.
        """
        # 1) Query your data to find consecutive lines
        stanza_lines = self.fetch_stanza_lines(chosen_match)
        self.chosen_match = stanza_lines
        if not stanza_lines:
            messagebox.showinfo("No Consecutive Lines", "No additional consecutive verses found. Proceeding.")
            self.finish_grammar_analysis(main_verse_text)
            return

        # 2) Store the main user input so that we can return to SGGS matches later.
        self.last_user_input = main_verse_text

        # 3) Create a window to show these lines as checkboxes
        self.consecutive_window = tk.Toplevel(self.root)
        self.consecutive_window.title("Select Consecutive Verses")
        self.consecutive_window.configure(bg='light gray')
        self.consecutive_window.state('zoomed')

        # Adjust header text based on the stored user's choice.
        if hasattr(self, 'verses_choice') and self.verses_choice:
            header_text = f"Select Additional Lines from the '{chosen_match['Special Type Demonstrator']}'"
        else:
            header_text = "Select Additional Lines from the Stanza"

        header_label = tk.Label(
            self.consecutive_window,
            text=header_text,
            bg='dark slate gray',
            fg='white',
            font=('Arial', 16, 'bold'),
            pady=10
        )
        header_label.pack(fill=tk.X)

        frame = tk.Frame(self.consecutive_window, bg='light gray')
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(frame, bg='light gray', borderwidth=0)
        vsb = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg='light gray')

        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        # Populate with checkboxes for each consecutive line.
        # Highlight the main verse (pre-selected and disabled) and add normal checkboxes for others.
        self.stanza_checkvars = []
        for idx, line_info in enumerate(stanza_lines):
            line_text = line_info.get('Verse', '')
            if line_text.strip() == main_verse_text.strip():
                # Highlight the main verse
                var = tk.BooleanVar(value=True)
                chk = tk.Checkbutton(
                    scroll_frame,
                    text=line_text,
                    variable=var,
                    bg='yellow',           # highlight color
                    font=('Arial', 12, 'bold'),
                    anchor='w',
                    justify=tk.LEFT,
                    wraplength=800,
                    state='disabled',      # force it to remain selected
                    selectcolor='light blue'
                )
            else:
                var = tk.BooleanVar(value=False)
                chk = tk.Checkbutton(
                    scroll_frame,
                    text=line_text,
                    variable=var,
                    bg='light gray',
                    font=('Arial', 12),
                    anchor='w',
                    justify=tk.LEFT,
                    wraplength=800,
                    selectcolor='light blue'
                )
            chk.pack(fill=tk.X, padx=10, pady=5)
            self.stanza_checkvars.append((var, line_text))

        scroll_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        # ---------------------------
        # Button Frame: Submit, Cancel, and Back
        # ---------------------------
        btn_frame = tk.Frame(self.consecutive_window, bg='light gray')
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Submit",
            command=lambda: self.validate_and_submit_consecutive(main_verse_text),
            font=('Arial', 12, 'bold'),
            bg='navy',
            fg='white',
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.consecutive_window.destroy,
            font=('Arial', 12, 'bold'),
            bg='red',
            fg='white',
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="Back",
            command=self.back_to_sggs_matches_option,
            font=('Arial', 12, 'bold'),
            bg='gray',
            fg='white',
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=10)

        print("Consecutive verses window created and populated.")

    def validate_and_submit_consecutive(self, main_verse_text):
        """
        Validate that the selected verses form a consecutive block that includes the main verse.
        If valid, proceed with handling the submission.
        """
        # Get indices of all selected verses
        selected_indices = [i for i, (var, _) in enumerate(self.stanza_checkvars) if var.get()]
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please ensure at least the main verse is selected.")
            return

        # Find the index of the main verse (which should be pre-selected)
        main_indices = [i for i, (_, line_text) in enumerate(self.stanza_checkvars)
                        if line_text.strip() == main_verse_text.strip()]
        if not main_indices:
            messagebox.showerror("Error", "Main verse not found in the list.")
            return
        main_index = main_indices[0]

        # Check if the selected indices form a consecutive block.
        if max(selected_indices) - min(selected_indices) != len(selected_indices) - 1:
            messagebox.showerror("Non-Consecutive Selection", "Please select only consecutive verses.")
            return

        # Ensure the consecutive block includes the main verse.
        if main_index < min(selected_indices) or main_index > max(selected_indices):
            messagebox.showerror("Selection Error", "The selected consecutive block must include the main verse.")
            return

        # If validation passes, proceed with the submission.
        self.handle_consecutive_submit(main_verse_text)

    def back_to_sggs_matches_option(self):
        """
        Close the consecutive verses window and re-display the SGGS matches option window.
        """
        self.consecutive_window.destroy()
        # Re-open the SGGS matches option window using the stored candidate matches and user input.
        self.show_sggs_matches_option(self.candidate_matches, self.last_user_input)

    def handle_consecutive_submit(self, main_verse_text):
        """
        Combine the main verse text with the lines selected by the user,
        then proceed with grammar analysis. Ensures that the main verse is
        not duplicated if it was also selected by the user.
        Also, store the individual selected verses in self.selected_verses 
        (as a list of tuples: (start_index, end_index, verse_text)) for later use.
        """
        # Strip the main verse text
        main_line = main_verse_text.strip()

        # Gather the lines that were checked; strip extra whitespace
        selected_lines = [line.strip() for var, line in self.stanza_checkvars if var.get()]

        # Store each selected line as an individual verse in self.selected_verses.
        self.selected_verses = list(selected_lines)

        # Keep only matches where the verse is in self.selected_verses.
        self.chosen_match = [match for match in self.chosen_match if match['Verse'] in self.selected_verses]

        # Filter out any line that is exactly the same as the main verse
        extra_lines = [line for line in selected_lines if line != main_line]

        # Combine all selected lines (including the main verse, already in correct order) into a single string,
        # ensuring the original sequence of the verse is maintained.
        if extra_lines:
            combined_text = " ".join(selected_lines)
        else:
            combined_text = main_line
        
        # Close the consecutive window
        self.consecutive_window.destroy()

        # Proceed with grammar analysis using the combined text
        self.finish_grammar_analysis(combined_text)

    def fetch_stanza_lines(self, chosen_match):
        """
        Return a list of dictionaries representing consecutive lines from either the current stanza or the entire text set,
        based on the user's choice.
        This function uses the SGGS data loaded by load_sggs_data() (stored in self.sggs_data).
        """
        # Ensure the SGGS data is loaded
        if not hasattr(self, 'sggs_data'):
            self.load_sggs_data()

        # Retrieve the Stanza No. and Text Set No. from the chosen match.
        stanza_no = chosen_match.get('Stanza No.')
        text_set_no = chosen_match.get('Text Set No.')

        if stanza_no is None or text_set_no is None:
            print("Chosen match does not contain required 'Stanza No.' or 'Text Set No.' information.")
            return []

        # Get the Special Type Demonstrator value.
        special_type = chosen_match.get('Special Type Demonstrator', '')

        # If it's 'ਸ਼ਲੋਕ', then we don't ask the user because a ਸ਼ਲੋਕ is always a stanza.
        if special_type == 'ਸ਼ਲੋਕ':
            choice = False
        else:
            choice = messagebox.askyesno(
                "Select Verses",
                f"Do you want to fetch verses from the entire '{special_type}'?\n\n"
                f"(Yes = Entire '{special_type}', No = Only the current Stanza)"
            )
        # Store the user's choice for later use
        self.verses_choice = choice

        if choice:
            # User selected the entire text set.
            subset = self.sggs_data[self.sggs_data['Text Set No.'] == text_set_no]
        else:
            # User selected only the current stanza.
            subset = self.sggs_data[
                (self.sggs_data['Stanza No.'] == stanza_no) &
                (self.sggs_data['Text Set No.'] == text_set_no)
            ]

        # Optionally sort by 'Verse No.' if available
        if 'Verse No.' in subset.columns:
            subset = subset.sort_values(by='Verse No.')

        lines = subset.to_dict(orient='records')

        return lines

    def finish_grammar_analysis(self, user_input):
        """
        Runs grammar analysis after the user has selected or typed a final verse.
        """
        self.pankti_words = user_input.split()
        self.accumulate_pankti_data(user_input)
        self.current_word_index = 0
        self.all_new_entries = []  # Reset global accumulator

        self.update_navigation_buttons()
        self.process_next_word()

    def prompt_for_assessment(self, metadata_entry):
        """
        Opens a modal window that lets the user paste the analysis result (translation)
        and choose options for 'Framework?' and 'Explicit?'.
        The metadata_entry is a dictionary containing the existing metadata (e.g., Word, Vowel Ending, etc.).
        """
        assessment_win = tk.Toplevel(self.root)
        assessment_win.title("Enter Translation Assessment")
        assessment_win.configure(bg='light gray')

        instruction_label = tk.Label(assessment_win, 
                                    text="Paste the analysis result below:",
                                    font=("Helvetica", 14), bg="light gray")
        instruction_label.pack(pady=10)

        analysis_text = scrolledtext.ScrolledText(assessment_win, width=80, height=10,
                                                font=("Helvetica", 12), wrap=tk.WORD)
        analysis_text.pack(padx=20, pady=10)

        cb_frame = tk.Frame(assessment_win, bg="light gray")
        cb_frame.pack(pady=10)

        framework_var = tk.BooleanVar()
        explicit_var = tk.BooleanVar()

        framework_cb = tk.Checkbutton(cb_frame, text="Framework?", variable=framework_var,
                                    font=("Helvetica", 12), bg="light gray")
        framework_cb.pack(side=tk.LEFT, padx=10)

        explicit_cb = tk.Checkbutton(cb_frame, text="Explicit?", variable=explicit_var,
                                    font=("Helvetica", 12), bg="light gray")
        explicit_cb.pack(side=tk.LEFT, padx=10)

        def on_save():
            translation = analysis_text.get("1.0", tk.END).strip()
            if not translation:
                messagebox.showerror("Error", "Please paste the analysis result.")
                return
            # Merge the metadata with the new assessment data
            new_entry = metadata_entry.copy()
            new_entry["Translation"] = translation
            new_entry["Framework?"] = framework_var.get()
            new_entry["Explicit?"] = explicit_var.get()
            # Revision is computed in save_assessment_data
            self.save_assessment_data(new_entry)
            assessment_win.destroy()

        save_btn = tk.Button(assessment_win, text="Save Assessment",
                            command=on_save, font=("Helvetica", 14, "bold"),
                            bg="#007acc", fg="white", padx=20, pady=10)
        save_btn.pack(pady=20)

        assessment_win.transient(self.root)
        assessment_win.grab_set()
        self.root.wait_window(assessment_win)

    def load_existing_assessment_data(self, file_path):
        expected_columns = [
            "Verse", "Translation", "Translation Revision",
            "Word", "Selected Darpan Meaning", "Vowel Ending", "Number / ਵਚਨ", "Grammar / ਵਯਾਕਰਣ", "Gender / ਲਿੰਗ", "Word Root", "Word Type", "Grammar Revision", "Word Index",
            "S. No.", "Verse No.", "Stanza No.", "Text Set No.", "Raag (Fixed)", "Sub-Raag", "Writer (Fixed)",
            "Verse Configuration (Optional)", "Stanza Configuration (Optional)", "Bani Name", "Musical Note Configuration",
            "Special Type Demonstrator", "Verse Type", "Page Number",
            "Framework?", "Explicit?"
        ]
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                if df.empty or len(df.columns) == 0:
                    df = pd.DataFrame(columns=expected_columns)
                else:
                    # Ensure the DataFrame has exactly the expected columns.
                    df = df.reindex(columns=expected_columns)
                return df
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        return pd.DataFrame(columns=expected_columns)

    def save_assessment_data(self, new_entry):
        """
        Saves a new assessment entry to an Excel file with the following behavior:
        - For a given verse, update the "Translation" field for all entries.
        - For the specific word being assessed in that verse, group all matching rows.
        - If any grammar field differs from the new entry, increment the Grammar Revision once for the group
            and update all matching rows with the new grammar details.
        - Update "Selected Darpan Meaning" for the specific word occurrence.
        - If any word's grammar is revised in the verse, increment the "Translation Revision" for all words of that verse.
        - If no matching entry exists for the word in that verse, append the new entry with a Grammar Revision of 1,
            and initialize the Translation Revision.
        """
        file_path = "1.2.1 assessment_data.xlsx"
        df_existing = self.load_existing_assessment_data(file_path)
        
        # Define the grammar keys to compare (excluding Translation, which is updated separately).
        grammar_keys = [
            'Vowel Ending', 'Number / ਵਚਨ', 'Grammar / ਵਯਾਕਰਣ',
            'Gender / ਲਿੰਗ', 'Word Root', 'Word Type'
        ]
        
        # Update the Translation for all rows in the same verse.
        df_existing.loc[df_existing["Verse"] == new_entry["Verse"], "Translation"] = new_entry["Translation"]
        
        # Filter for rows with the same word, same verse, and same word index.
        matching_rows = df_existing[
            (df_existing["Word"] == new_entry["Word"]) &
            (df_existing["Verse"] == new_entry["Verse"]) &
            (df_existing["Word Index"] == new_entry["Word Index"])
        ]
        
        if not matching_rows.empty:
            # For repeated occurrences, pick the highest Grammar Revision as a representative.
            latest_idx = matching_rows["Grammar Revision"].idxmax()
            latest_row = df_existing.loc[latest_idx]
            
            # Check if any grammar field is different.
            differences = any(new_entry.get(key) != latest_row.get(key) for key in grammar_keys)
            
            if differences:
                # Compute new Grammar Revision number for the group.
                new_grammar_revision = matching_rows["Grammar Revision"].max() + 1
                new_entry["Grammar Revision"] = new_grammar_revision
                
                # Update all matching rows with new grammar values and new Grammar Revision.
                for idx in matching_rows.index:
                    for key in grammar_keys:
                        df_existing.at[idx, key] = new_entry.get(key)
                    df_existing.at[idx, "Grammar Revision"] = new_grammar_revision
                    # Update additional fields from new_entry if needed.
                    for key, value in new_entry.items():
                        if key not in grammar_keys and key not in ["Translation"]:
                            if key in ("Framework?", "Explicit?"):
                                df_existing.at[idx, key] = int(value)  # Cast Boolean to int (False->0, True->1)
                            else:
                                df_existing.at[idx, key] = value
                # Update Selected Darpan Meaning for these rows.
                for idx in matching_rows.index:
                    # --- Compute correct global index for the current word using the current verse ---
                    current_verse_words = self.accumulated_pankti.split()

                    def find_sublist_index(haystack, needle):
                        for i in range(len(haystack) - len(needle) + 1):
                            if haystack[i:i+len(needle)] == needle:
                                return i
                        return -1

                    start_index = find_sublist_index(self.pankti_words, current_verse_words)
                    if start_index == -1:
                        start_index = 0

                    # Assume new_entry["Word Index"] is the local index within the verse.
                    global_index = start_index + new_entry.get("Word Index", 0)

                    # Retrieve the selected Darpan meaning using the global index.
                    if len(self.accumulated_meanings) > global_index:
                        acc_entry = self.accumulated_meanings[global_index]
                        if isinstance(acc_entry, dict):
                            selected_meaning = ", ".join(acc_entry.get("meanings", []))
                        else:
                            selected_meaning = ", ".join(acc_entry)
                    else:
                        selected_meaning = ""

                    df_existing.at[idx, "Selected Darpan Meaning"] = selected_meaning

                # Now update the Translation Revision for all rows in the verse 
                # to reflect the latest Grammar Revision (without extra +1).
                verse_mask = df_existing["Verse"] == new_entry["Verse"]
                latest_grammar_revision = df_existing.loc[verse_mask, "Grammar Revision"].max()
                df_existing.loc[verse_mask, "Translation Revision"] = latest_grammar_revision
            else:
                # No differences detected; no update necessary.
                return
        else:
            # No existing entry for this word in the verse; add it with Grammar Revision 1.
            new_entry["Grammar Revision"] = 1
            # Initialize Selected Darpan Meaning if not provided.
            if "Selected Darpan Meaning" not in new_entry:
                new_entry["Selected Darpan Meaning"] = ""
            # Determine Translation Revision for the verse.
            current_translation_revision = df_existing[df_existing["Verse"] == new_entry["Verse"]]["Translation Revision"].max()
            new_entry["Translation Revision"] = (current_translation_revision + 1) if current_translation_revision is not None else 1
            df_existing = pd.concat([df_existing, pd.DataFrame([new_entry])], ignore_index=True)
        
        try:
            df_existing.to_excel(file_path, index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save assessment data: {e}")

    def setup_options(self, parent_frame, label_text, options, variable):
        """
        Sets up radio button options in the specified parent frame.

        Args:
        parent_frame (tk.Frame): The frame in which to pack the radio buttons.
        label_text (str): The label text to display above the radio buttons.
        options (list of tuple): A list of tuples where each tuple contains the option text and the value to set in the variable.
        variable (tk.StringVar): The control variable for the group of radio buttons.
        """
        # Create a label for the option group with styling
        tk.Label(parent_frame, text=label_text, bg='light gray', font=('Arial', 12)).pack(pady=(10, 5))

        # Create radio buttons for each option
        for opt_text, opt_value in options:
            tk.Radiobutton(
                parent_frame,
                text=opt_text,
                variable=variable,
                value=opt_value,
                bg='light gray',
                selectcolor='light blue',
                anchor='w',
                font=('Arial', 11)
            ).pack(anchor='w', padx=20, pady=2)

    def navigation_controls(self, parent_frame):
        """
        Add navigation controls to the parent frame to navigate through words.
        """
        nav_frame = tk.Frame(parent_frame, bg='light gray')
        nav_frame.pack(pady=10)

        tk.Button(nav_frame, text="Previous", command=self.previous_word, bg='dark gray', fg='white').pack(side='left', padx=5)
        tk.Button(nav_frame, text="Next", command=self.next_word, bg='dark gray', fg='white').pack(side='left', padx=5)

    def update_navigation_buttons(self):
        """Enable or disable navigation buttons based on the current word index."""
        print(f"Updating buttons, current index: {self.current_word_index}, total words: {len(self.pankti_words)}")
        
        # Disable 'Previous' button if at the start
        if self.current_word_index <= 0:
            self.prev_button.config(state=tk.DISABLED)
        else:
            self.prev_button.config(state=tk.NORMAL)
        
        # Disable 'Next' button if at the end
        if self.current_word_index >= len(self.pankti_words) - 1:
            self.next_button.config(state=tk.DISABLED)
        else:
            self.next_button.config(state=tk.NORMAL)

    def update_current_word_label(self):
        """Update the word label to display the current word."""
        if hasattr(self, 'pankti_words') and self.pankti_words:
            # Clamp the index to valid range:
            if self.current_word_index < 0:
                self.current_word_index = 0
            if self.current_word_index >= len(self.pankti_words):
                self.current_word_index = len(self.pankti_words) - 1
            current_word = self.pankti_words[self.current_word_index]
            self.word_label.config(text=current_word)
        else:
            self.word_label.config(text="No Word Available")

    def prev_word(self):
        if self.current_word_index > 0:
            self.current_word_index -= 1
            self.update_current_word_label()
        self.update_navigation_buttons()

    def next_word(self):
        if self.current_word_index < len(self.pankti_words) - 1:
            self.current_word_index += 1
            self.update_current_word_label()
        self.update_navigation_buttons()

    def select_current_word(self):
        """Trigger analysis for the currently displayed word."""
        if hasattr(self, 'pankti_words') and self.pankti_words:
            # Ensure current_word_index is within range:
            if self.current_word_index >= len(self.pankti_words):
                self.current_word_index = len(self.pankti_words) - 1
            word = self.pankti_words[self.current_word_index]
            self.fetch_data(word, " ".join(self.pankti_words))
        else:
            print("No word available for selection.")

    def close_window(self, window):
        """Closes the given Tkinter window."""
        if window and window.winfo_exists():
            window.destroy()

    def reset_input_variables(self):
        """Reset input variables for number, gender, and part of speech."""
        self.number_var.set("NA")
        self.gender_var.set("NA")
        self.pos_var.set("NA")

    def compose_clipboard_text_for_chatgpt(self):
        clipboard_text = "### Detailed Analysis & Literal Translation\n\n"
        clipboard_text += (
            f"The verse **'{self.accumulated_pankti}'** holds deep meaning. Below is a breakdown of each word with "
            "user-selected meanings and grammar details, which together form the basis for a literal translation prompt.\n\n"
        )
        
        # --- Preceding Verses & Translations ---
        # Load existing assessment data.
        existing_data = self.load_existing_assessment_data("1.2.1 assessment_data.xlsx")
        
        # Identify the candidate matching the current verse.
        current_candidate = next((cand for cand in self.chosen_match 
                                if cand.get("Verse", "").strip() == self.accumulated_pankti.strip()), None)
        
        preceding_verses_text = ""
        if current_candidate:
            text_set_no = current_candidate.get("Text Set No.")
            try:
                current_verse_no = int(current_candidate.get("Verse No."))
            except (ValueError, TypeError):
                current_verse_no = None
            
            if current_verse_no is not None:
                # Filter for the same Text Set No.
                filtered_data = existing_data[existing_data["Text Set No."] == text_set_no]
                consecutive_verses = []
                target_verse_no = current_verse_no - 1
                # Collect consecutive preceding verses.
                while True:
                    row = filtered_data[filtered_data["Verse No."] == target_verse_no]
                    if row.empty:
                        break
                    row_data = row.iloc[0]
                    consecutive_verses.insert(0, row_data)  # earlier verses first
                    target_verse_no -= 1
                
                if consecutive_verses:
                    preceding_verses_text += "\n### Preceding Verses & Translations\n\n"
                    for row_data in consecutive_verses:
                        verse_no = row_data.get("Verse No.", "")
                        verse_text = row_data.get("Verse", "")
                        translation = row_data.get("Translation", "")
                        preceding_verses_text += f"**Verse {verse_no}:** {verse_text}\n"
                        preceding_verses_text += f"**Translation:** {translation}\n\n"
        
        clipboard_text += preceding_verses_text
        
        # --- Current Verse Analysis ---
        current_verse_words = self.accumulated_pankti.split()
        
        def find_sublist_index(haystack, needle):
            # Find a consecutive occurrence of 'needle' in 'haystack'
            for i in range(len(haystack) - len(needle) + 1):
                if haystack[i:i+len(needle)] == needle:
                    return i
            return -1

        start_index = find_sublist_index(self.pankti_words, current_verse_words)
        if start_index == -1:
            start_index = 0  # Fallback if no match is found

        for i, word in enumerate(current_verse_words):
            actual_index = start_index + i
            clipboard_text += f"**Word {i+1}: {word}**\n"
            
            # Retrieve the entry for the current word (if available)
            acc_entry = self.accumulated_meanings[actual_index] if actual_index < len(self.accumulated_meanings) else {}
            # If the entry is a dictionary, extract the 'meanings' list; otherwise, assume it's already a list
            if isinstance(acc_entry, dict):
                meanings_list = acc_entry.get("meanings", [])
            else:
                meanings_list = acc_entry
            # Create a string of meanings, or a default message if none are available
            meanings_str = ", ".join(meanings_list) if meanings_list else "No user-selected meanings available"
            clipboard_text += f"- **User-Selected Meanings:** {meanings_str}\n"
            
            clipboard_text += "- **Grammar Options:**\n"
            finalized_matches_list = self.accumulated_finalized_matches[actual_index] if actual_index < len(self.accumulated_finalized_matches) else []
            
            if finalized_matches_list:
                for option_idx, match in enumerate(finalized_matches_list, start=1):
                    clipboard_text += (
                        f"  - **Option {option_idx}:**\n"
                        f"      - **Word:** {match.get('Word', 'N/A')}\n"
                        f"      - **Vowel Ending:** {match.get('Vowel Ending', 'N/A')}\n"
                        f"      - **Number / ਵਚਨ:** {match.get('Number / ਵਚਨ', 'N/A')}\n"
                        f"      - **Grammar / ਵਯਾਕਰਣ:** {match.get('Grammar / ਵਯਾਕਰਣ', 'N/A')}\n"
                        f"      - **Gender / ਲਿੰਗ:** {match.get('Gender / ਲਿੰਗ', 'N/A')}\n"
                        f"      - **Word Root:** {match.get('Word Root', 'N/A')}\n"
                        f"      - **Type:** {match.get('Word Type', 'N/A')}\n"
                    )
                    clipboard_text += (
                        f"      - **Literal Translation (Option {option_idx}):** The word '{word}' functions as a "
                        f"'{match.get('Word Type', 'N/A')}' with '{match.get('Grammar / ਵਯਾਕਰਣ', 'N/A')}' usage, in the "
                        f"'{match.get('Number / ਵਚਨ', 'N/A')}' form and '{match.get('Gender / ਲਿੰਗ', 'N/A')}' gender. Translation: …\n"
                    )
            else:
                clipboard_text += "  - No finalized grammar options available\n"
            
            clipboard_text += "\n"
        
        if '॥' in current_verse_words:
            clipboard_text += (
                "**Symbol:** ॥\n"
                "- **Meaning:** End of verse or sentence\n"
                "- **Context:** Denotes the conclusion of the verse.\n\n"
            )
        
        clipboard_text += "\n### Literal Translation Prompt\n"
        clipboard_text += (
            f"Using the above user-selected meanings and grammar details for the verse '{self.accumulated_pankti}', "
            "please generate a literal translation that adheres strictly to the grammatical structure, "
            "capturing the tense, number, gender, and function accurately."
        )
        
        return clipboard_text

    def prompt_copy_to_clipboard(self):
        print("Prompting to copy text to clipboard...")
        copy_prompt = messagebox.askyesno(
            "Copy to Clipboard", 
            f"Would you like to copy the detailed analysis for the verse '{self.accumulated_pankti}' to your clipboard?"
        )
        if copy_prompt:
            if not self.accumulated_pankti or not self.accumulated_meanings or not self.accumulated_grammar_matches or not self.accumulated_finalized_matches:
                print("Error: Accumulated data is not populated.")
                messagebox.showerror("Error", "Failed to copy data to clipboard: Data not populated.")
            else:
                clipboard_text = self.compose_clipboard_text_for_chatgpt()
                pyperclip.copy(clipboard_text)
                messagebox.showinfo("Copied", "The analysis has been copied to the clipboard!")
                print("Clipboard text copied successfully!")

    def prompt_for_final_grammar(self, word_entries):
        """
        Opens a modal window showing all grammar options for a given word.
        Generates a prompt text for ChatGPT to help finalize the grammar choice,
        copies it to the clipboard (with a button to re-copy if needed), and then
        allows the user to select the final applicable grammar.
        
        word_entries: a list of dictionaries (each corresponding to one grammar option for the word)
        """
        final_choice = {}

        final_win = tk.Toplevel(self.root)
        final_win.title(f"Finalize Grammar for '{word_entries[0]['Word']}'")
        final_win.configure(bg='light gray')

        # --- Build the ChatGPT prompt text ---
        prompt_lines = []
        prompt_lines.append(f"Finalise the applicable grammar for the word: {word_entries[0]['Word']}")
        prompt_lines.append("The following grammar options are available:")
        for idx, entry in enumerate(word_entries, start=1):
            summary = " | ".join([
                entry.get("Vowel Ending", ""),
                entry.get("Number / ਵਚਨ", ""),
                entry.get("Grammar / ਵਯਾਕਰਣ", ""),
                entry.get("Gender / ਲਿੰਗ", ""),
                entry.get("Word Root", ""),
                entry.get("Word Type", "")
            ])
            prompt_lines.append(f"Option {idx}: {summary}")
        prompt_text = "\n".join(prompt_lines)
        # --- End building prompt text ---

        # --- Display the prompt text and add a copy button ---
        prompt_frame = tk.Frame(final_win, bg="light gray")
        prompt_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        prompt_label = tk.Label(prompt_frame, 
                                text="ChatGPT Prompt for Grammar Finalisation:",
                                font=("Helvetica", 14, "bold"),
                                bg="light gray")
        prompt_label.pack(anchor="w", pady=(0,5))

        prompt_text_widget = scrolledtext.ScrolledText(prompt_frame, width=80, height=6,
                                                        font=("Helvetica", 12), wrap=tk.WORD)
        prompt_text_widget.pack(fill=tk.BOTH, expand=True)
        prompt_text_widget.insert(tk.END, prompt_text)
        prompt_text_widget.config(state=tk.DISABLED)

        def copy_prompt():
            self.root.clipboard_clear()
            self.root.clipboard_append(prompt_text)
            messagebox.showinfo("Copied", "Prompt text copied to clipboard!")

        copy_btn = tk.Button(prompt_frame, text="Copy Prompt", command=copy_prompt,
                            font=("Helvetica", 12, "bold"),
                            bg="#007acc", fg="white", padx=10, pady=5)
        copy_btn.pack(anchor="e", pady=5)
        # --- End prompt display ---

        # Instruction for selecting final grammar
        instruction = tk.Label(final_win,
                            text="Multiple grammar options found for this word.\nPlease select the final applicable grammar:",
                            font=("Helvetica", 14),
                            bg="light gray")
        instruction.pack(pady=10)

        # Tk variable to hold the selected option index
        choice_var = tk.IntVar(value=0)

        # --- Create a scrollable area for the radio buttons ---
        options_container = tk.Frame(final_win, bg="light gray")
        options_container.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        # Create a canvas in the container
        canvas = tk.Canvas(options_container, bg="light gray", highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a vertical scrollbar to the container
        vsb = tk.Scrollbar(options_container, orient="vertical", command=canvas.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=vsb.set)

        # Create a frame inside the canvas to hold the radio buttons
        options_frame = tk.Frame(canvas, bg="light gray")
        canvas.create_window((0,0), window=options_frame, anchor="nw")

        # Update the scroll region when the frame's size changes
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        options_frame.bind("<Configure>", on_frame_configure)
        # --- End scrollable area creation ---

        # Create radio buttons with option text as "Option {number}: {summary}"
        for idx, entry in enumerate(word_entries):
            summary = " | ".join([
                entry.get("Vowel Ending", ""),
                entry.get("Number / ਵਚਨ", ""),
                entry.get("Grammar / ਵਯਾਕਰਣ", ""),
                entry.get("Gender / ਲਿੰਗ", ""),
                entry.get("Word Root", ""),
                entry.get("Word Type", "")
            ])
            rb_text = f"Option {idx+1}: {summary}"
            rb = tk.Radiobutton(options_frame,
                                text=rb_text,
                                variable=choice_var,
                                value=idx,
                                bg="light gray",
                                font=("Helvetica", 12),
                                anchor='w',
                                justify=tk.LEFT,
                                selectcolor='light blue')
            rb.pack(anchor="w", padx=10, pady=5)

        def on_save():
            selected_index = choice_var.get()
            nonlocal final_choice
            final_choice = word_entries[selected_index]
            final_win.destroy()

        save_btn = tk.Button(final_win, text="Save Choice",
                            command=on_save,
                            font=("Helvetica", 14, "bold"),
                            bg="#007acc", fg="white", padx=20, pady=10)
        save_btn.pack(pady=20)

        final_win.transient(self.root)
        final_win.grab_set()
        self.root.wait_window(final_win)
        return final_choice

    def prompt_save_results(self, new_entries, skip_copy=False):
        """
        For each verse in self.selected_verses, prompts the user to save new entries (accumulated from all words),
        checking for duplicates first. Then opens a modal prompt for assessment and saves the finalized data
        (including verse-level metadata) to an Excel file.
        """
        file_path = "1.2.1 assessment_data.xlsx"
        existing_data = self.load_existing_assessment_data(file_path)
        
        # Save the original accumulated_pankti so it can be restored later.
        original_accumulated_pankti = self.accumulated_pankti

        # Process each verse in the selected verses
        for verse in self.selected_verses:
            # Update the current verse for processing.
            self.accumulated_pankti = verse

            # Build a set of words for the current verse.
            # (Adjust the cleaning/splitting logic if needed.)
            cleaned_verse = verse.replace('॥', '')
            current_verse_words = cleaned_verse.split()
            selected_words = set(current_verse_words)

            # Filter new_entries to only those whose "Word" is present in the current verse.
            filtered_new_entries = [
                entry for entry in new_entries
                if entry["Word"] in selected_words and entry.get("Verse", "").strip() == verse.strip()
            ]

            duplicate_entries = []
            unique_entries = []

            # Duplicate check: for each filtered entry, compare against existing data.
            for new_entry in filtered_new_entries:
                if any(
                    new_entry["Word"] == existing_entry.get("Word") and
                    new_entry["Vowel Ending"] == existing_entry.get("Vowel Ending") and
                    new_entry["Number / ਵਚਨ"] == existing_entry.get("Number / ਵਚਨ") and
                    new_entry["Grammar / ਵਯਾਕਰਣ"] == existing_entry.get("Grammar / ਵਯਾਕਰਣ") and
                    new_entry["Gender / ਲਿੰਗ"] == existing_entry.get("Gender / ਲਿੰਗ") and
                    new_entry["Word Root"] == existing_entry.get("Word Root") and
                    new_entry["Word Type"] == existing_entry.get("Type") and
                    new_entry["Verse"] == existing_entry.get("Verse")  # Comparing verses as well
                    for existing_entry in existing_data.to_dict('records')
                ):
                    duplicate_entries.append(new_entry)
                else:
                    unique_entries.append(new_entry)

            if duplicate_entries:
                duplicate_message = "Some entries are already present:\n" + "\n".join(map(str, duplicate_entries))
                messagebox.showinfo("Duplicates Found", duplicate_message)

            if not skip_copy:
                self.prompt_copy_to_clipboard()

            if unique_entries:
                save = messagebox.askyesno(
                    "Save Results", 
                    f"Would you like to save the new entries for the following verse?\n\n{verse}"
                )
                if save:
                    # Open one assessment prompt for the current verse.
                    assessment_data = self.prompt_for_assessment_once()

                    # --- Extract verse metadata from candidate matches ---
                    verse_to_match = self.accumulated_pankti.strip()
                    candidate = None
                    if hasattr(self, 'candidate_matches') and self.chosen_match:
                        for cand in self.chosen_match:
                            if cand.get("Verse", "").strip() == verse_to_match:
                                candidate = cand
                                break
                        if candidate is None:
                            candidate = self.chosen_match[0]
                        verse_metadata = {
                            "Verse": verse_to_match,
                            "S. No.": candidate.get("S. No.", ""),
                            "Verse No.": candidate.get("Verse No.", ""),
                            "Stanza No.": candidate.get("Stanza No.", ""),
                            "Text Set No.": candidate.get("Text Set No.", ""),
                            "Raag (Fixed)": candidate.get("Raag (Fixed)", ""),
                            "Sub-Raag": candidate.get("Sub-Raag", ""),
                            "Writer (Fixed)": candidate.get("Writer (Fixed)", ""),
                            "Verse Configuration (Optional)": candidate.get("Verse Configuration (Optional)", ""),
                            "Stanza Configuration (Optional)": candidate.get("Stanza Configuration (Optional)", ""),
                            "Bani Name": candidate.get("Bani Name", ""),
                            "Musical Note Configuration": candidate.get("Musical Note Configuration", ""),
                            "Special Type Demonstrator": candidate.get("Special Type Demonstrator", ""),
                            "Verse Type": candidate.get("Type", ""),
                            "Page Number": candidate.get("Page Number", "")
                        }
                    else:
                        verse_metadata = {}
                    # -------------------------------------------------------

                    # --- Finalize grammar options per word (handling repeated words by occurrence order via clustering) ---
                    # --- Group unique_entries by word ---
                    word_groups = {}
                    for entry in unique_entries:
                        word = entry["Word"]
                        word_groups.setdefault(word, []).append(entry)
                        
                    final_entries = []
                    occurrence_mapping = {}  # Mapping from (word, occurrence_position) to list of entries (options)

                    # For each unique word in the current verse, partition its entries into clusters based on occurrence count.
                    for word in set(current_verse_words):
                        count = current_verse_words.count(word)  # number of times the word appears in the verse
                        if word not in word_groups:
                            continue
                        entries_list = word_groups[word]  # all unique entries for that word (in sequence)
                        n = len(entries_list)
                        k = count  # expected number of clusters
                        groups = []
                        start = 0
                        # Partition entries_list into k groups using a chunking method.
                        # If n isn't exactly divisible by k, distribute the remainder to the first few groups.
                        group_size = n // k
                        remainder = n % k
                        for i in range(k):
                            size = group_size + (1 if i < remainder else 0)
                            group = entries_list[start:start+size]
                            groups.append(group)
                            start += size
                        # Find the indices (positions) in current_verse_words where this word occurs, in order.
                        occurrence_positions = [i for i, w in enumerate(current_verse_words) if w == word]
                        for occ, pos in zip(range(k), occurrence_positions):
                            occurrence_mapping[(word, pos)] = groups[occ]

                    # Now, iterate over current_verse_words (which are in order) and process each occurrence.
                    for idx, word in enumerate(current_verse_words):
                        key = (word, idx)  # Unique key for the occurrence at position idx.
                        entries = occurrence_mapping.get(key, [])
                        if not entries:
                            continue  # No entries for this occurrence.

                        # Remove duplicate entries within this occurrence group (local deduplication).
                        dedup_entries = []
                        seen = set()
                        for entry in entries:
                            entry_tuple = tuple(sorted(entry.items()))
                            if entry_tuple not in seen:
                                seen.add(entry_tuple)
                                dedup_entries.append(entry)
                        entries = dedup_entries

                        # If more than one unique option exists for this occurrence, prompt the user to choose.
                        if len(entries) > 1:
                            chosen_entry = self.prompt_for_final_grammar(entries)
                        else:
                            chosen_entry = entries[0]

                        # Capture the occurrence index.
                        chosen_entry['Word Index'] = idx

                        # Ensure self.accumulated_finalized_matches is long enough.
                        if len(self.accumulated_finalized_matches) <= idx:
                            self.accumulated_finalized_matches.extend([[]] * (idx - len(self.accumulated_finalized_matches) + 1))
                        self.accumulated_finalized_matches[idx] = [chosen_entry]
                        final_entries.append(chosen_entry)
                    # -------------------------------------------------------

                    # Now update each finalized entry with the assessment and verse metadata, then save.
                    for entry in final_entries:
                        entry.update(assessment_data)
                        entry.update(verse_metadata)
                        self.save_assessment_data(entry)
                    messagebox.showinfo("Saved", "Assessment data saved successfully for verse:\n" + verse)

        # Restore the original accumulated_pankti after processing all verses.
        self.accumulated_pankti = original_accumulated_pankti

        if hasattr(self, 'copy_button') and self.copy_button.winfo_exists():
            self.copy_button.config(state=tk.NORMAL)

    def prompt_for_assessment_once(self):
        """Opens a modal prompt for the entire verse assessment and returns the collected data."""
        assessment_win = tk.Toplevel(self.root)
        assessment_win.title(f"Enter Translation Assessment for: '{self.accumulated_pankti}'")
        assessment_win.configure(bg='light gray')

        instruction_label = tk.Label(
            assessment_win, 
            text="Paste the analysis result for the entire verse below:",
            font=("Helvetica", 14), bg="light gray"
        )
        instruction_label.pack(pady=10)

        analysis_text = scrolledtext.ScrolledText(assessment_win, width=80, height=10,
                                                font=("Helvetica", 12), wrap=tk.WORD)
        analysis_text.pack(padx=20, pady=10)

        cb_frame = tk.Frame(assessment_win, bg="light gray")
        cb_frame.pack(pady=10)

        framework_var = tk.BooleanVar()
        explicit_var = tk.BooleanVar()

        framework_cb = tk.Checkbutton(cb_frame, text="Framework?", variable=framework_var,
                                    font=("Helvetica", 12), bg="light gray")
        framework_cb.pack(side=tk.LEFT, padx=10)

        explicit_cb = tk.Checkbutton(cb_frame, text="Explicit?", variable=explicit_var,
                                    font=("Helvetica", 12), bg="light gray")
        explicit_cb.pack(side=tk.LEFT, padx=10)

        assessment_data = {}

        def on_save():
            translation = analysis_text.get("1.0", tk.END).strip()
            if not translation:
                messagebox.showerror("Error", "Please paste the analysis result.")
                return
            assessment_data["Translation"] = translation
            assessment_data["Framework?"] = framework_var.get()
            assessment_data["Explicit?"] = explicit_var.get()
            assessment_win.destroy()

        save_btn = tk.Button(assessment_win, text="Save Assessment",
                            command=on_save, font=("Helvetica", 14, "bold"),
                            bg="#007acc", fg="white", padx=20, pady=10)
        save_btn.pack(pady=20)

        assessment_win.transient(self.root)
        assessment_win.grab_set()
        self.root.wait_window(assessment_win)

        return assessment_data

    def accumulate_pankti_data(self, pankti):
        self.accumulated_pankti = pankti

    def accumulate_meanings_data(self, meanings):
        """
        Accumulate the meanings for the current word, along with the word itself and its index.
        This creates a mapping for each word occurrence.
        """
        # Ensure the list is long enough for the current word index.
        while len(self.accumulated_meanings) <= self.current_word_index:
            self.accumulated_meanings.append({"word": None, "meanings": []})
        
        # Store the word if it hasn't been stored yet.
        if self.accumulated_meanings[self.current_word_index]["word"] is None:
            # Assuming self.pankti_words is defined and holds the current verse's words.
            self.accumulated_meanings[self.current_word_index]["word"] = self.pankti_words[self.current_word_index]
        
        # Update the meanings for the current word occurrence.
        self.accumulated_meanings[self.current_word_index]["meanings"] = meanings

    def accumulate_grammar_matches(self, matches):
        self.accumulated_grammar_matches.append(matches)

    def accumulate_finalized_matches(self, finalized_matches):
        # Ensure the list is long enough to hold the current index
        if len(self.accumulated_finalized_matches) <= self.current_word_index:
            # Expand the list to the required length with empty lists
            self.accumulated_finalized_matches.extend([[]] * (self.current_word_index - len(self.accumulated_finalized_matches) + 1))
        
        # Store the finalized matches at the correct index
        self.accumulated_finalized_matches[self.current_word_index] = finalized_matches

    def start_progress(self):
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Please Wait...")
        self.progress_window.geometry("350x120")
        self.progress_window.resizable(False, False)
        self.progress_window.attributes("-topmost", True)
        self.progress_window.configure(bg="#f0f0f0")
        self.progress_window.attributes('-alpha', 0.0)  # Start fully transparent

        # Center the progress window
        self.progress_window.update_idletasks()
        x = (self.progress_window.winfo_screenwidth() - self.progress_window.winfo_width()) // 2
        y = (self.progress_window.winfo_screenheight() - self.progress_window.winfo_height()) // 3
        self.progress_window.geometry(f"+{x}+{y}")

        # Fade-in effect
        def fade_in(window, alpha=0.0):
            alpha = round(alpha + 0.05, 2)
            if alpha <= 1.0:
                window.attributes('-alpha', alpha)
                window.after(30, lambda: fade_in(window, alpha))

        fade_in(self.progress_window)

        # Custom style
        style = ttk.Style(self.progress_window)
        style.theme_use('default')

        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor="#e0e0e0",
                        bordercolor="#e0e0e0",
                        background="#4a90e2",
                        lightcolor="#4a90e2",
                        darkcolor="#4a90e2",
                        thickness=20)

        label = ttk.Label(self.progress_window, text="Processing, please wait...", background="#f0f0f0", font=("Segoe UI", 10))
        label.pack(pady=(20, 5))

        self.progress_bar = ttk.Progressbar(self.progress_window,
                                            mode='indeterminate',
                                            style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(padx=30, fill=tk.X)
        self.progress_bar.start(7)

        self.root.update_idletasks()

    def stop_progress(self):
        self.progress_bar.stop()
        self.progress_window.destroy()

    def handle_submitted_input(self, word):
        # Implement your logic for handling the submitted input here
        print(f"Handling submitted input for: {word}")
        # You can add your logic here, such as saving or processing the input further

    def filter_unique_matches(self, matches):
        """
        Eliminate duplicates based on the grammatical parts and return unique matches.

        Args:
        matches (list): The list of matches to filter.

        Returns:
        list: The list of unique matches.
        """
        # Sort matches by match_count first and then by match_percentage, both in descending order
        matches_sorted = sorted(matches, key=lambda x: (x[1], x[2]), reverse=True)

        unique_matches = []
        seen_grammar = set()
        for match in matches_sorted:
            grammar_info = match[0].split(" | ")[2:]  # Extract grammar info (e.g., Number, Gender, POS, etc.)
            grammar_tuple = tuple(grammar_info)
            if grammar_tuple not in seen_grammar:
                unique_matches.append(match)
                seen_grammar.add(grammar_tuple)

        # Accumulate Grammar Matches data
        self.accumulate_grammar_matches(unique_matches)
        return unique_matches

    def perform_dictionary_lookup(self, word, callback):
        """
        Runs the dictionary lookup (with its progress bar) in a separate thread.
        Once the lookup completes, the callback is called on the main thread with the lookup result.
        """
        def lookup_worker():
            # Call your lookup function (which already shows the progress bar)
            meanings = self.lookup_word_in_dictionary(word)
            # Schedule the callback on the main thread with the obtained meanings
            self.root.after(0, lambda: callback(meanings))
        threading.Thread(target=lookup_worker, daemon=True).start()

    def handle_lookup_results(self, matches, meanings):
        """
        Called when the dictionary lookup is finished.
        'matches' are those computed earlier and 'meanings' is the result from the lookup.
        This method updates the UI by calling show_matches.
        """
        print(f"Lookup completed for {self.pankti_words[self.current_word_index]}. Meanings: {meanings}")
        self.show_matches(matches, self.current_pankti, meanings)

    def calculate_match_metrics(self, word, vowel_ending):
        """
        Calculates the number of matching characters from the end of vowel_ending and word, 
        and the percentage of matching characters with respect to the matched part of vowel_ending.
        
        Parameters:
        word (str): The word to be compared.
        vowel_ending (str): The vowel ending to be compared, possibly containing multiple parts.
        
        Returns:
        tuple: A tuple containing:
            - match_count (int): Number of matching characters from the end.
            - match_percentage (float): Percentage of matching characters based on the matched part of vowel_ending.
        """
        word_chars = list(word)  # Convert word to a list of characters
        vowel_parts = vowel_ending.split()  # Split vowel ending into parts

        total_match_count = 0
        max_match_percentage = 0.0

        # Iterate through each part of the vowel ending
        for part in vowel_parts:
            part_chars = list(part)  # Convert each part to a list of characters

            match_count = 0

            # Reverse iterate through both word and part to compare characters from the end
            for i in range(1, min(len(word_chars), len(part_chars)) + 1):
                if word_chars[-i] == part_chars[-i]:
                    match_count += 1
                else:
                    break  # Stop when characters no longer match

            if match_count > 0:
                # Calculate match percentage based on the length of the matched part
                match_percentage = (match_count / len(part_chars)) * 100
                total_match_count += match_count
                
                # Track the highest match percentage found
                if match_percentage > max_match_percentage:
                    max_match_percentage = match_percentage

            # Stop if there was any match in the current part
            if match_count > 0:
                break

        return total_match_count, max_match_percentage


if __name__ == "__main__":
    root = tk.Tk()
    app = GrammarApp(root)
    root.mainloop()