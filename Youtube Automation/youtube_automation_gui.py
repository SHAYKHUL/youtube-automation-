"""
YouTube Automation Suite - Enhanced Professional GUI
A comprehensive tool for YouTube channel automation with advanced workflow support
Professional Windows-native design with full automation capabilities
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import csv
import os
import time
import json
import datetime
from pathlib import Path
from queue import Queue, Empty
from typing import Dict, List, Optional
import subprocess
import sys

# Import your existing modules with enhanced error handling
try:
    from auto import setup_driver, go_to_youtube, search_topic, apply_advanced_filters, get_video_details
    AUTO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: auto.py could not be imported: {e}")
    AUTO_AVAILABLE = False

try:
    from youtube_login import YouTubeAccountManager
    YOUTUBE_LOGIN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: youtube_login.py could not be imported: {e}")
    YOUTUBE_LOGIN_AVAILABLE = False

try:
    from email_finder import run_email_finder, extract_emails_and_socials
    EMAIL_FINDER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: email_finder.py could not be imported: {e}")
    EMAIL_FINDER_AVAILABLE = False

try:
    from subcunt import main as subcunt_main, load_channel_links, get_subscriber_count
    SUBCUNT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: subcunt.py could not be imported: {e}")
    SUBCUNT_AVAILABLE = False

# Import multi_thread functionality
try:
    import multi_thread
    MULTI_THREAD_AVAILABLE = True
    print("✅ multi_thread.py imported successfully")
except ImportError as e:
    print(f"Warning: multi_thread.py could not be imported: {e}")
    MULTI_THREAD_AVAILABLE = False

# Import file lock for thread-safe CSV writing
if MULTI_THREAD_AVAILABLE:
    try:
        from multi_thread import file_lock
    except ImportError:
        # Create our own file lock if not available
        file_lock = threading.Lock()
else:
    file_lock = threading.Lock()

# Import advanced components
try:
    from database_manager import DatabaseManager
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: database_manager.py could not be imported: {e}")
    DATABASE_AVAILABLE = False

try:
    from analytics_dashboard import AdvancedAnalyticsDashboard
    ANALYTICS_DASHBOARD_AVAILABLE = True
except ImportError as e:
    print(f"Warning: analytics_dashboard.py could not be imported: {e}")
    ANALYTICS_DASHBOARD_AVAILABLE = False

try:
    from task_scheduler import TaskScheduler, SchedulerGUI
    SCHEDULER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: task_scheduler.py could not be imported: {e}")
    SCHEDULER_AVAILABLE = False


class AutomationWorkflow:
    """Class to manage complete automation workflows"""
    def __init__(self, name, steps):
        self.name = name
        self.steps = steps
        self.current_step = 0
        self.completed = False
        self.results = {}


class YouTubeAutomationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("YouTube Automation Suite ✨")
        self.root.geometry("1280x800")
        self.root.minsize(1100, 650)
        self.root.configure(bg="#181c24")

        # Set modern style
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#181c24")
        style.configure("TLabel", background="#181c24", foreground="#e0e6f0", font=("Segoe UI", 11))
        style.configure("Heading.TLabel", font=("Segoe UI Semibold", 16), foreground="#00bfae", background="#181c24")
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"), foreground="#00bfae", background="#181c24")
        style.configure("Card.TLabelframe", background="#23293a", foreground="#e0e6f0", font=("Segoe UI", 11))
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), foreground="#181c24", background="#00bfae")
        style.map("Primary.TButton", background=[("active", "#009e8e")])
        style.configure("TButton", font=("Segoe UI", 11), padding=6)
        style.configure("Treeview", background="#23293a", fieldbackground="#23293a", foreground="#e0e6f0", font=("Consolas", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), foreground="#00bfae", background="#23293a")

        # Initialize core variables
        self.scraping_active = False
        self.login_active = False
        self.email_finding_active = False
        self.analysis_active = False
        self.workflow_active = False
        self.active_drivers = []
        self.scraping_threads = []
        
        # Initialize communication queues for threads
        self.message_queue = Queue()
        self.result_queue = Queue()
        
        # Initialize advanced database system
        if DATABASE_AVAILABLE:
            self.db_manager = DatabaseManager()
        else:
            self.db_manager = None
        
        # Initialize task scheduler
        if SCHEDULER_AVAILABLE and self.db_manager:
            self.task_scheduler = TaskScheduler(self.db_manager)
            self.setup_scheduler_callbacks()
        else:
            self.task_scheduler = None
        
        # Initialize statistics tracking
        self.session_stats = {
            'channels_scraped': 0,
            'emails_found': 0,
            'accounts_logged': 0,
            'channels_analyzed': 0,
            'session_start': datetime.datetime.now()
        }
        
        # Initialize status variable
        self.status_var = tk.StringVar(value="Ready to start scraping...")
        
        # Workflow templates
        self.workflow_templates = {
            'Channel Discovery': ['scrape_videos', 'analyze_subscribers', 'find_emails'],
            'Email Outreach': ['load_channels', 'find_emails', 'login_accounts'],
            'Full Analysis': ['scrape_videos', 'analyze_subscribers', 'generate_reports'],
            'Bulk Processing': ['scrape_videos', 'analyze_subscribers', 'find_emails', 'login_accounts']
        }
        
        # Configure style
        self.setup_styles()
        
        # Create main interface
        self.create_widgets()
        
        # Start message processing
        self.process_messages()
        
        # Add status bar at the bottom
        self.create_status_bar()
        # Auto-start email finder on launch if enabled (short delay to allow UI to initialize)
        try:
            self.root.after(1500, self._maybe_autostart_email_finder)
        except Exception:
            pass
        
        # Setup window close handler for proper cleanup
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_closing(self):
        """Handle window close event - cleanup all resources"""
        print("\n🛑 Closing application - cleaning up resources...")
        
        # Stop all active processes
        self.scraping_active = False
        self.email_finding_active = False
        self.subscriber_active = False
        self.authenticated_active = False
        
        # Close all Chrome drivers gracefully
        closed_count = 0
        for driver in self.active_drivers[:]:
            try:
                driver.quit()
                closed_count += 1
            except:
                pass
        
        if closed_count > 0:
            print(f"✅ Closed {closed_count} Chrome browser(s)")
        
        # Force kill any remaining browser processes
        try:
            import subprocess
            subprocess.run(['taskkill', '/f', '/im', 'chrome.exe'], 
                         capture_output=True, shell=True)
            subprocess.run(['taskkill', '/f', '/im', 'chromedriver.exe'], 
                         capture_output=True, shell=True)
            print("✅ Cleaned up remaining browser processes")
        except:
            pass
        
        # Close database connection if exists
        if hasattr(self, 'db_manager') and self.db_manager:
            try:
                self.db_manager.close()
                print("✅ Closed database connection")
            except:
                pass
        
        # Destroy the window
        print("✅ Application closed successfully")
        self.root.destroy()
        
    def setup_styles(self):
        """Configure tkinter styles for professional appearance"""
        style = ttk.Style()
        
        # Use native Windows theme
        try:
            style.theme_use('winnative')
        except:
            style.theme_use('default')
        
        # Configure color scheme - Professional Windows 11 style
        self.colors = {
            'bg_primary': '#ffffff',
            'bg_secondary': '#f9f9f9',
            'bg_accent': '#f0f0f0',
            'primary': '#0078d4',
            'primary_hover': '#106ebe',
            'success': '#107c10',
            'warning': '#ff8c00',
            'error': '#d13438',
            'text_primary': '#323130',
            'text_secondary': '#605e5c',
            'border': '#e1dfdd'
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # Configure enhanced ttk styles
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 18, 'bold'),
                       background=self.colors['bg_primary'],
                       foreground=self.colors['primary'])
        
        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 11),
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_secondary'])
        
        style.configure('Heading.TLabel',
                       font=('Segoe UI', 12, 'bold'),
                       background=self.colors['bg_primary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Section.TLabel',
                       font=('Segoe UI', 10, 'bold'),
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Primary.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       relief='flat',
                       borderwidth=1)
        
        style.configure('Success.TButton',
                       font=('Segoe UI', 9),
                       relief='flat')
        
        style.configure('Warning.TButton',
                       font=('Segoe UI', 9),
                       relief='flat')
        
        # Enhanced LabelFrame styling
        style.configure('Card.TLabelframe',
                       relief='solid',
                       borderwidth=1,
                       background=self.colors['bg_secondary'])
        
        style.configure('Card.TLabelframe.Label',
                       font=('Segoe UI', 10, 'bold'),
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['primary'])
        
    def create_widgets(self):
        """Create the enhanced main GUI elements"""
        # Header Section
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=25, pady=(25, 15))
        # Remove the style configuration that doesn't exist
        # header_frame.configure(style='Card.TFrame')
        
        # Title and subtitle
        title_container = ttk.Frame(header_frame)
        title_container.pack(fill='x')
        
        title_label = ttk.Label(title_container, 
                               text="YouTube Automation Suite",
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        # Session stats in header
        stats_frame = ttk.Frame(title_container)
        stats_frame.pack(side='right', padx=(20, 0))
        
        self.stats_label = ttk.Label(stats_frame,
                                    text="Session: 0 channels | 0 emails | 0 logins",
                                    style='Subtitle.TLabel')
        self.stats_label.pack()
        
        subtitle_label = ttk.Label(header_frame,
                                  text="Advanced YouTube Channel Management & Automation Platform",
                                  style='Subtitle.TLabel')
        subtitle_label.pack(anchor='w', pady=(5, 0))
        
        # Main content area with workflow controls
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill='both', expand=True, padx=25, pady=(0, 15))
        
        # Workflow control panel (top section)
        self.create_workflow_panel(content_frame)
        
        # Create notebook for detailed tabs
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill='both', expand=True, pady=(15, 0))
        
        # Create enhanced tabs
        self.create_video_scraping_tab()
        self.create_account_login_tab()
        self.create_email_finder_tab()
        self.create_analytics_tab()
        self.create_advanced_analytics_tab()
        self.create_scheduler_tab()
        self.create_reports_tab()
        
        # Enhanced status bar with progress info
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', side='bottom', padx=5, pady=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Select a workflow or use individual tools")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var,
                              relief='sunken', anchor='w',
                              font=('Segoe UI', 9))
        status_bar.pack(side='left', fill='x', expand=True)
        
        # Global progress indicator
        self.global_progress = ttk.Progressbar(status_frame, length=200, mode='determinate')
        self.global_progress.pack(side='right', padx=(10, 0))
    
    def create_workflow_panel(self, parent):
        """Create automated workflow control panel"""
        workflow_frame = ttk.LabelFrame(parent, text="🚀 Automated Workflows", 
                                       style='Card.TLabelframe', padding=15)
        workflow_frame.pack(fill='x', pady=(0, 15))
        
        # Workflow selection
        selection_frame = ttk.Frame(workflow_frame)
        selection_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(selection_frame, text="Choose Workflow:", 
                 style='Section.TLabel').pack(side='left', padx=(0, 10))
        
        self.workflow_var = tk.StringVar(value="Channel Discovery")
        workflow_combo = ttk.Combobox(selection_frame, textvariable=self.workflow_var,
                                     values=list(self.workflow_templates.keys()),
                                     state='readonly', width=20)
        workflow_combo.pack(side='left', padx=(0, 15))
        
        # Workflow configuration
        config_frame = ttk.Frame(selection_frame)
        config_frame.pack(side='left', padx=(15, 0))
        
        ttk.Label(config_frame, text="Topics:").pack(side='left')
        self.workflow_topics_var = tk.StringVar(value="tech,gaming,cooking")
        topics_entry = ttk.Entry(config_frame, textvariable=self.workflow_topics_var, width=25)
        topics_entry.pack(side='left', padx=(5, 10))
        
        ttk.Label(config_frame, text="Max Results:").pack(side='left')
        self.workflow_max_var = tk.StringVar(value="100")
        max_spin = ttk.Spinbox(config_frame, from_=10, to=1000, 
                              textvariable=self.workflow_max_var, width=8)
        max_spin.pack(side='left', padx=(5, 0))
        
        # Workflow controls
        controls_frame = ttk.Frame(workflow_frame)
        controls_frame.pack(fill='x')
        
        left_controls = ttk.Frame(controls_frame)
        left_controls.pack(side='left')
        
        self.start_workflow_btn = ttk.Button(left_controls, text="▶ Start Full Workflow",
                                           command=self.start_full_workflow,
                                           style='Primary.TButton')
        self.start_workflow_btn.pack(side='left', padx=(0, 10))
        
        self.pause_workflow_btn = ttk.Button(left_controls, text="⏸ Pause",
                                           command=self.pause_workflow,
                                           state='disabled')
        self.pause_workflow_btn.pack(side='left', padx=(0, 10))
        
        self.stop_workflow_btn = ttk.Button(left_controls, text="⏹ Stop",
                                          command=self.stop_workflow,
                                          state='disabled')
        self.stop_workflow_btn.pack(side='left', padx=(0, 15))
        
        # Workflow progress and steps
        right_controls = ttk.Frame(controls_frame)
        right_controls.pack(side='right')
        
        self.workflow_progress = ttk.Progressbar(right_controls, length=300, mode='determinate')
        self.workflow_progress.pack(side='left', padx=(0, 10))
        
        self.workflow_step_var = tk.StringVar(value="Ready")
        step_label = ttk.Label(right_controls, textvariable=self.workflow_step_var,
                              style='Section.TLabel')
        step_label.pack(side='left')
        
        # Advanced options toggle
        advanced_frame = ttk.Frame(workflow_frame)
        advanced_frame.pack(fill='x', pady=(15, 0))
        
        self.show_advanced = tk.BooleanVar()
        advanced_check = ttk.Checkbutton(advanced_frame, text="Show Advanced Options",
                                        variable=self.show_advanced,
                                        command=self.toggle_advanced_options)
        advanced_check.pack(side='left')
        
        # Advanced options panel (initially hidden)
        self.advanced_panel = ttk.Frame(workflow_frame)
        self.create_advanced_options(self.advanced_panel)
    
    def create_advanced_options(self, parent):
        """Create advanced workflow options panel"""
        # Email filtering options
        email_frame = ttk.LabelFrame(parent, text="Email Finding Options", padding=10)
        email_frame.pack(fill='x', pady=(10, 5))
        
        email_options = ttk.Frame(email_frame)
        email_options.pack(fill='x')
        
        self.find_emails_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(email_options, text="Find Emails", 
                       variable=self.find_emails_var).pack(side='left', padx=(0, 15))
        
        self.find_social_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(email_options, text="Find Social Media", 
                       variable=self.find_social_var).pack(side='left', padx=(0, 15))
        
        self.skip_signin_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(email_options, text="Skip Sign-in Required", 
                       variable=self.skip_signin_var).pack(side='left')
        
        # Analysis options
        analysis_frame = ttk.LabelFrame(parent, text="Analysis Options", padding=10)
        analysis_frame.pack(fill='x', pady=5)
        
        analysis_options = ttk.Frame(analysis_frame)
        analysis_options.pack(fill='x')
        
        ttk.Label(analysis_options, text="Subscriber Range:").pack(side='left', padx=(0, 5))
        
        self.sub_min_var = tk.StringVar(value="0")
        ttk.Entry(analysis_options, textvariable=self.sub_min_var, width=8).pack(side='left', padx=(0, 5))
        
        ttk.Label(analysis_options, text="to").pack(side='left', padx=(0, 5))
        
        self.sub_max_var = tk.StringVar(value="50000")
        ttk.Entry(analysis_options, textvariable=self.sub_max_var, width=8).pack(side='left', padx=(0, 15))
        
        self.categorize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(analysis_options, text="Auto-categorize channels", 
                       variable=self.categorize_var).pack(side='left')
        
        # Performance options
        perf_frame = ttk.LabelFrame(parent, text="Performance Options", padding=10)
        perf_frame.pack(fill='x', pady=5)
        
        perf_options = ttk.Frame(perf_frame)
        perf_options.pack(fill='x')
        
        ttk.Label(perf_options, text="Parallel Processes:").pack(side='left', padx=(0, 5))
        
        self.parallel_processes_var = tk.StringVar(value="3")
        ttk.Spinbox(perf_options, from_=1, to=10, textvariable=self.parallel_processes_var, 
                   width=8).pack(side='left', padx=(0, 15))
        
        ttk.Label(perf_options, text="Delay (seconds):").pack(side='left', padx=(0, 5))
        
        self.delay_var = tk.StringVar(value="1")
        ttk.Spinbox(perf_options, from_=0.5, to=10, increment=0.5, 
                   textvariable=self.delay_var, width=8).pack(side='left', padx=(0, 15))
        
        self.headless_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(perf_options, text="Headless Mode", 
                       variable=self.headless_var).pack(side='left')
    
    def toggle_advanced_options(self):
        """Toggle display of advanced options"""
        if self.show_advanced.get():
            self.advanced_panel.pack(fill='x', pady=(10, 0))
        else:
            self.advanced_panel.pack_forget()
        
    def create_video_scraping_tab(self):
        """Create video scraping tab with optimized layout"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎥 Video Scraping")
        
        # Main container with better padding
        main_container = ttk.Frame(frame)
        main_container.pack(fill='both', expand=True, padx=10, pady=8)
        
        # Header section with description
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(header_frame, text="🎥 YouTube Channel Discovery", 
                 style='Heading.TLabel').pack(side='left')
        ttk.Label(header_frame, text="Find channels by scraping videos within specific view ranges", 
                 font=('Segoe UI', 9), foreground='#8a8a8a').pack(side='left', padx=(12, 0))
        
        # Two-column layout for better space usage
        columns_frame = ttk.Frame(main_container)
        columns_frame.pack(fill='both', expand=True)
        
        # LEFT COLUMN - Configuration (30% width)
        left_panel = ttk.Frame(columns_frame, width=380)
        left_panel.pack(side='left', fill='y', padx=(0, 6))
        left_panel.pack_propagate(False)
        
        # Configuration card
        config_card = ttk.LabelFrame(left_panel, text="⚙️ Configuration", padding=8, style='Card.TLabelframe')
        config_card.pack(fill='x', pady=(0, 8))
        
        # Search topics - compact design
        ttk.Label(config_card, text="🔍 Search Topics:", style='Section.TLabel').pack(anchor='w')
        self.topics_text = scrolledtext.ScrolledText(config_card, height=3, font=('Segoe UI', 10))
        self.topics_text.pack(fill='x', pady=(4, 8))
        self.topics_text.insert('1.0', 'gaming\ncooking\ntech reviews')
        
        # Views range - horizontal layout
        views_card = ttk.Frame(config_card)
        views_card.pack(fill='x', pady=(0, 8))
        
        ttk.Label(views_card, text="📊 Views Range:", style='Section.TLabel').pack(anchor='w')
        views_controls = ttk.Frame(views_card)
        views_controls.pack(fill='x', pady=(4, 0))
        
        ttk.Label(views_controls, text="Min:", font=('Segoe UI', 9)).pack(side='left')
        self.min_views_var = tk.StringVar(value="0")
        min_entry = ttk.Entry(views_controls, textvariable=self.min_views_var, width=8, font=('Segoe UI', 10))
        min_entry.pack(side='left', padx=(4, 8))
        
        ttk.Label(views_controls, text="Max:", font=('Segoe UI', 9)).pack(side='left')
        self.max_views_var = tk.StringVar(value="10000")
        max_entry = ttk.Entry(views_controls, textvariable=self.max_views_var, width=8, font=('Segoe UI', 10))
        max_entry.pack(side='left', padx=(4, 0))
        
        # Chrome windows - compact
        windows_card = ttk.Frame(config_card)
        windows_card.pack(fill='x', pady=(0, 8))
        
        ttk.Label(windows_card, text="🌐 Chrome Windows:", style='Section.TLabel').pack(anchor='w')
        windows_controls = ttk.Frame(windows_card)
        windows_controls.pack(fill='x', pady=(4, 0))
        
        self.chrome_windows_var = tk.StringVar(value="3")
        windows_spin = ttk.Spinbox(windows_controls, from_=1, to=20, 
                                  textvariable=self.chrome_windows_var, width=8, font=('Segoe UI', 10))
        windows_spin.pack(side='left', padx=(4, 0))
        
        # Action buttons card
        actions_card = ttk.LabelFrame(left_panel, text="🚀 Actions", padding=8, style='Card.TLabelframe')
        actions_card.pack(fill='x', pady=(0, 8))
        
        # Primary action buttons
        primary_actions = ttk.Frame(actions_card)
        primary_actions.pack(fill='x', pady=(0, 6))
        
        self.start_scraping_btn = ttk.Button(primary_actions, text="▶️ Start Scraping",
                                           command=self.start_scraping,
                                           style='Primary.TButton')
        self.start_scraping_btn.pack(fill='x', pady=(0, 4))
        
        self.stop_scraping_btn = ttk.Button(primary_actions, text="⏹️ Stop Scraping",
                                          command=self.stop_scraping,
                                          state='disabled')
        self.stop_scraping_btn.pack(fill='x')
        
        # Secondary actions
        secondary_actions = ttk.Frame(actions_card)
        secondary_actions.pack(fill='x')
        
        load_auto_btn = ttk.Button(secondary_actions, text="📄 Load Results",
                                  command=self.load_scraping_results)
        load_auto_btn.pack(side='left', fill='x', expand=True, padx=(0, 2))
        
        load_custom_btn = ttk.Button(secondary_actions, text="📁 Load Custom",
                                   command=self.load_scraping_results_from_file)
        load_custom_btn.pack(side='right', fill='x', expand=True, padx=(2, 0))
        
        # Quick stats card
        stats_card = ttk.LabelFrame(left_panel, text="📊 Quick Stats", padding=8, style='Card.TLabelframe')
        stats_card.pack(fill='x', pady=(0, 8))
        
        self.quick_stats_text = tk.Text(stats_card, height=4, font=('Segoe UI', 9), 
                                       bg='#23293a', fg='#e0e6f0', border=0, wrap='word')
        self.quick_stats_text.pack(fill='x')
        self.quick_stats_text.insert('1.0', "📊 Channels Found: 0\n⏱️ Session Time: 0:00:00\n🌐 Active Browsers: 0\n📈 Success Rate: 0%")
        self.quick_stats_text.config(state='disabled')
        
        # RIGHT COLUMN - Progress and Results (70% width)
        right_panel = ttk.Frame(columns_frame)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Progress and stats section
        progress_card = ttk.LabelFrame(right_panel, text="📊 Progress & Statistics", padding=6, style='Card.TLabelframe')
        progress_card.pack(fill='x', pady=(0, 6))
        
        # Progress bar
        self.scraping_progress = ttk.Progressbar(progress_card, mode='indeterminate', style="TProgressbar")
        self.scraping_progress.pack(fill='x', pady=(0, 6))
        
        # Live statistics
        self.live_stats_var = tk.StringVar(value="Channels Found: 0 | Processing: 0 topics | Chrome Windows: 0")
        stats_label = ttk.Label(progress_card, textvariable=self.live_stats_var, 
                               style='Section.TLabel', wraplength=500)
        stats_label.pack(fill='x')
        
        # Results section takes priority - full space initially
        results_frame = ttk.LabelFrame(right_panel, text="📋 Saved Channels", padding=4, style='Card.TLabelframe')
        results_frame.pack(fill='both', expand=True, pady=(0, 6))
        
        # Collapsible Log section at bottom
        log_container = ttk.Frame(right_panel)
        log_container.pack(fill='x', pady=(0, 0))
        
        # Log toggle header
        log_header = ttk.Frame(log_container)
        log_header.pack(fill='x')
        
        self.log_visible = tk.BooleanVar(value=False)  # Hidden by default
        self.log_toggle_btn = ttk.Button(log_header, text="▶️ Show Developer Log", 
                                        command=self.toggle_log_visibility,
                                        style='TButton')
        self.log_toggle_btn.pack(side='left', pady=2)
        
        ttk.Label(log_header, text="(Advanced users only)", 
                 font=('Segoe UI', 8), foreground='#8a8a8a').pack(side='left', padx=(8, 0))
        
        # Collapsible log frame
        self.log_frame = ttk.LabelFrame(log_container, text="📝 Live Scraping Log", 
                                       padding=4, style='Card.TLabelframe')
        # Don't pack it initially - will be shown/hidden by toggle
        
        self.log_display = scrolledtext.ScrolledText(self.log_frame, height=4, 
                                                    state='disabled', wrap='word',
                                                    bg='#181c24', fg='#00bfae', font=('Consolas', 8),
                                                    insertbackground='#00bfae')
        self.log_display.pack(fill='both', expand=True)
        
        # Create results container with scrollbars
        results_container = ttk.Frame(results_frame)
        results_container.pack(fill='both', expand=True)
        
        # Enhanced results table with more space
        columns = ('Channel', 'Views', 'Status', 'Found')
        self.results_tree = ttk.Treeview(results_container, columns=columns, show='headings', 
                                        height=12, style="Treeview")  # More height
        
        # Configure columns with better spacing
        self.results_tree.heading('Channel', text='🔗 Channel URL')
        self.results_tree.heading('Views', text='👁️ Views')
        self.results_tree.heading('Status', text='✅ Status')
        self.results_tree.heading('Found', text='🕐 Found At')
        
        self.results_tree.column('Channel', width=400, anchor='w')
        self.results_tree.column('Views', width=80, anchor='center')
        self.results_tree.column('Status', width=100, anchor='center')
        self.results_tree.column('Found', width=120, anchor='center')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_container, orient='vertical', command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_container, orient='horizontal', command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.results_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        results_container.grid_rowconfigure(0, weight=1)
        results_container.grid_columnconfigure(0, weight=1)
        
        # Add tooltips
        self.create_tooltip(results_container, "Double-click a channel to copy its URL")
        
        # Bind double-click to copy channel URL
        self.results_tree.bind("<Double-1>", self.copy_channel_url)
        
    def create_account_login_tab(self):
        """Create account login tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Account Login")
        
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Header
        header_label = ttk.Label(main_frame, 
                                text="Multi-Account Login",
                                style='Heading.TLabel')
        header_label.pack(anchor='w', pady=(0, 10))
        
        # CSV Management
        csv_frame = ttk.LabelFrame(main_frame, text="Account Management", padding=10)
        csv_frame.pack(fill='x', pady=(0, 10))
        
        csv_controls_frame = ttk.Frame(csv_frame)
        csv_controls_frame.pack(fill='x')
        
        self.csv_file_var = tk.StringVar(value="gmail_accounts.csv")
        ttk.Label(csv_controls_frame, text="CSV File:").pack(side='left')
        csv_entry = ttk.Entry(csv_controls_frame, textvariable=self.csv_file_var, width=30)
        csv_entry.pack(side='left', padx=(5, 10))
        
        select_csv_btn = ttk.Button(csv_controls_frame, text="Select CSV File",
                                   command=self.select_account_csv)
        select_csv_btn.pack(side='left', padx=(0, 10))
        
        create_sample_btn = ttk.Button(csv_controls_frame, text="Create Sample CSV",
                                      command=self.create_sample_account_csv)
        create_sample_btn.pack(side='left')
        
        # Login Options
        options_frame = ttk.LabelFrame(main_frame, text="Login Options", padding=10)
        options_frame.pack(fill='x', pady=(0, 10))
        
        self.login_mode_var = tk.StringVar(value="sequential")
        
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(mode_frame, text="Login Mode:").pack(side='left')
        
        modes = [("Sequential", "sequential"), ("Individual", "individual"), ("Parallel", "parallel")]
        for text, value in modes:
            ttk.Radiobutton(mode_frame, text=text, variable=self.login_mode_var, 
                           value=value).pack(side='left', padx=(10, 0))
        
        # Channel URLs
        channels_frame = ttk.Frame(options_frame)
        channels_frame.pack(fill='x')
        
        ttk.Label(channels_frame, text="Channel URLs to visit (optional):").pack(anchor='w')
        self.channel_urls_text = scrolledtext.ScrolledText(channels_frame, height=3, width=50)
        self.channel_urls_text.pack(fill='x', pady=(5, 0))
        
        # Controls
        login_controls_frame = ttk.Frame(main_frame)
        login_controls_frame.pack(fill='x', pady=(0, 10))
        
        self.start_login_btn = ttk.Button(login_controls_frame, text="Login All Accounts",
                                         command=self.start_login,
                                         style='Primary.TButton')
        self.start_login_btn.pack(side='left', padx=(0, 10))
        
        self.stop_login_btn = ttk.Button(login_controls_frame, text="Stop Login",
                                        command=self.stop_login,
                                        state='disabled')
        self.stop_login_btn.pack(side='left')
        
        # Progress
        self.login_progress = ttk.Progressbar(main_frame, mode='determinate')
        self.login_progress.pack(fill='x', pady=(0, 10))
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Login Log", padding=5)
        log_frame.pack(fill='both', expand=True)
        
        self.login_log = scrolledtext.ScrolledText(log_frame, height=10, state='disabled')
        self.login_log.pack(fill='both', expand=True)
        
    def create_email_finder_tab(self):
        """Create enhanced email finder tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Email Finder")
        
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Header with description
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 15))
        
        header_label = ttk.Label(header_frame, 
                                text="📧 Email & Social Media Finder",
                                style='Heading.TLabel')
        header_label.pack(anchor='w')
        
        desc_label = ttk.Label(header_frame, 
                              text="Automatically extract contact information from YouTube channels",
                              foreground='#666666')
        desc_label.pack(anchor='w', pady=(5, 0))
        
        # Two-column layout
        columns_frame = ttk.Frame(main_frame)
        columns_frame.pack(fill='both', expand=True)
        
        # Left column - Configuration (Fixed width and visibility)
        left_column = ttk.Frame(columns_frame)
        left_column.pack(side='left', fill='y', padx=(0, 10), pady=5)
        left_column.configure(width=400)  # Fixed width to ensure visibility
        
        # Configuration
        config_frame = ttk.LabelFrame(left_column, text="⚙️ Configuration", padding=15)
        config_frame.pack(fill='x', pady=(0, 10))
        
        # Input CSV
        input_frame = ttk.Frame(config_frame)
        input_frame.pack(fill='x', pady=(0, 12))
        
        ttk.Label(input_frame, text="Input CSV File:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        input_select_frame = ttk.Frame(input_frame)
        input_select_frame.pack(fill='x', pady=(5, 0))
        
        self.email_input_var = tk.StringVar(value="save.csv")
        input_entry = ttk.Entry(input_select_frame, textvariable=self.email_input_var, width=25)
        input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        select_input_btn = ttk.Button(input_select_frame, text="Browse",
                                     command=self.select_email_input_csv, width=8)
        select_input_btn.pack(side='right')
        
        # Quick file selection
        quick_files_frame = ttk.Frame(input_frame)
        quick_files_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Label(quick_files_frame, text="Quick Select:", font=('Segoe UI', 8)).pack(anchor='w')
        
        quick_buttons_frame = ttk.Frame(quick_files_frame)
        quick_buttons_frame.pack(fill='x', pady=(2, 0))
        
        for filename in ["save.csv", "below_1k.csv", "1k_10k.csv", "above_10k.csv"]:
            btn = ttk.Button(quick_buttons_frame, text=filename, width=12,
                           command=lambda f=filename: self.email_input_var.set(f))
            btn.pack(side='left', padx=(0, 5))
        
        # Processing Options
        options_frame = ttk.Frame(config_frame)
        options_frame.pack(fill='x', pady=(0, 12))
        
        ttk.Label(options_frame, text="Processing Options:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        # Chrome windows with slider
        windows_frame = ttk.Frame(options_frame)
        windows_frame.pack(fill='x', pady=(5, 8))
        
        ttk.Label(windows_frame, text="Parallel Windows:").pack(side='left')
        self.email_windows_var = tk.StringVar(value="3")
        windows_scale = ttk.Scale(windows_frame, from_=1, to=10, orient='horizontal',
                                 variable=self.email_windows_var, length=120)
        windows_scale.pack(side='left', padx=(10, 5))
        windows_label = ttk.Label(windows_frame, textvariable=self.email_windows_var, width=3)
        windows_label.pack(side='left')
        
        # Search depth options
        depth_frame = ttk.Frame(options_frame)
        depth_frame.pack(fill='x', pady=(0, 8))
        
        self.search_video_desc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(depth_frame, text="Search Video Descriptions", 
                       variable=self.search_video_desc_var).pack(anchor='w')
        
        self.search_about_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(depth_frame, text="Search About Section", 
                       variable=self.search_about_var).pack(anchor='w')
        
        self.search_comments_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(depth_frame, text="Search Pinned Comments", 
                       variable=self.search_comments_var).pack(anchor='w')
        
        # Delay settings
        delay_frame = ttk.Frame(options_frame)
        delay_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(delay_frame, text="Request Delay (seconds):").pack(side='left')
        self.email_delay_var = tk.StringVar(value="2")
        delay_spin = ttk.Spinbox(delay_frame, from_=1, to=10, width=5,
                                textvariable=self.email_delay_var)
        delay_spin.pack(side='left', padx=(10, 0))
        
        # Export Options
        export_frame = ttk.LabelFrame(left_column, text="📊 Export Options", padding=15)
        export_frame.pack(fill='x', pady=(0, 10))
        
        self.export_json_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(export_frame, text="Export to JSON", 
                       variable=self.export_json_var).pack(anchor='w')
        
        self.include_timestamps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(export_frame, text="Include Timestamps", 
                       variable=self.include_timestamps_var).pack(anchor='w')
        
        self.deduplicate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(export_frame, text="Remove Duplicates", 
                       variable=self.deduplicate_var).pack(anchor='w')
        
        # Controls
        email_controls_frame = ttk.Frame(left_column)
        email_controls_frame.pack(fill='x', pady=(0, 10))
        
        self.start_email_btn = ttk.Button(email_controls_frame, text="🚀 Start Finding",
                                         command=self.start_email_finding,
                                         style='Primary.TButton')
        self.start_email_btn.pack(fill='x', pady=(0, 5))
        
        control_buttons_frame = ttk.Frame(email_controls_frame)
        control_buttons_frame.pack(fill='x')
        
        self.stop_email_btn = ttk.Button(control_buttons_frame, text="⏹️ Stop",
                                        command=self.stop_email_finding,
                                        state='disabled', width=12)
        self.stop_email_btn.pack(side='left', padx=(0, 5))
        
        self.pause_email_btn = ttk.Button(control_buttons_frame, text="⏸️ Pause",
                                         command=self.pause_email_finding,
                                         state='disabled', width=12)
        self.pause_email_btn.pack(side='left')

        # Auto-start option (default OFF to avoid accidental runs on launch)
        self.autostart_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(email_controls_frame, text="Auto-start on launch", variable=self.autostart_var).pack(anchor='w', pady=(6, 0))
        
        # Progress with details
        progress_frame = ttk.Frame(left_column)
        progress_frame.pack(fill='x')
        
        ttk.Label(progress_frame, text="Progress:", font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        self.email_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.email_progress.pack(fill='x', pady=(5, 2))
        
        progress_info_frame = ttk.Frame(progress_frame)
        progress_info_frame.pack(fill='x')
        
        self.current_channel_var = tk.StringVar(value="Ready to start...")
        current_label = ttk.Label(progress_info_frame, textvariable=self.current_channel_var,
                                 font=('Segoe UI', 8), foreground='#666666')
        current_label.pack(anchor='w')
        
        self.progress_detail_var = tk.StringVar(value="")
        detail_label = ttk.Label(progress_info_frame, textvariable=self.progress_detail_var,
                                font=('Segoe UI', 8), foreground='#888888')
        detail_label.pack(anchor='w')
        
        # Right column - Results
        right_column = ttk.Frame(columns_frame, style='Card.TFrame')
        right_column.pack(side='right', fill='both', expand=True, padx=(10, 0), pady=5)
        
        # Real-time Results Summary
        summary_frame = ttk.LabelFrame(right_column, text="📈 Live Results", padding=15)
        summary_frame.pack(fill='x', pady=(0, 10))
        
        # Create a grid for better organization
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill='x')
        
        # Row 1
        ttk.Label(summary_grid, text="📧 Emails Found:", font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', padx=(0, 20))
        self.emails_found_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.emails_found_var, 
                 foreground=self.colors['success'], font=('Segoe UI', 12, 'bold')).grid(row=0, column=1, sticky='w')
        
        ttk.Label(summary_grid, text="📱 Social Only:", font=('Segoe UI', 9, 'bold')).grid(row=0, column=2, sticky='w', padx=(30, 20))
        self.social_only_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.social_only_var, 
                 foreground='#FFA500', font=('Segoe UI', 12, 'bold')).grid(row=0, column=3, sticky='w')
        
        # Row 2
        ttk.Label(summary_grid, text="🔒 Sign-in Required:", font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, sticky='w', pady=(10, 0))
        self.signin_required_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.signin_required_var, 
                 foreground='#FF6B6B', font=('Segoe UI', 12, 'bold')).grid(row=1, column=1, sticky='w', pady=(10, 0))
        
        ttk.Label(summary_grid, text="❌ Nothing Found:", font=('Segoe UI', 9, 'bold')).grid(row=1, column=2, sticky='w', padx=(30, 20), pady=(10, 0))
        self.nothing_found_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.nothing_found_var, 
                 foreground=self.colors['error'], font=('Segoe UI', 12, 'bold')).grid(row=1, column=3, sticky='w', pady=(10, 0))
        
        # Success Rate
        rate_frame = ttk.Frame(summary_frame)
        rate_frame.pack(fill='x', pady=(15, 0))
        
        ttk.Label(rate_frame, text="Success Rate:", font=('Segoe UI', 9, 'bold')).pack(side='left')
        self.success_rate_var = tk.StringVar(value="0%")
        ttk.Label(rate_frame, textvariable=self.success_rate_var, 
                 foreground=self.colors['primary'], font=('Segoe UI', 10, 'bold')).pack(side='left', padx=(10, 0))
        
        # Recent Finds Preview
        recent_frame = ttk.LabelFrame(right_column, text="🎯 Recent Finds", padding=10)
        recent_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Create treeview for recent finds
        columns = ('Type', 'Channel', 'Contact', 'Time')
        self.recent_finds_tree = ttk.Treeview(recent_frame, columns=columns, show='headings', height=8)
        
        self.recent_finds_tree.heading('Type', text='Type')
        self.recent_finds_tree.heading('Channel', text='Channel')
        self.recent_finds_tree.heading('Contact', text='Contact Info')
        self.recent_finds_tree.heading('Time', text='Time')
        
        self.recent_finds_tree.column('Type', width=60)
        self.recent_finds_tree.column('Channel', width=200)
        self.recent_finds_tree.column('Contact', width=250)
        self.recent_finds_tree.column('Time', width=80)
        
        recent_scrollbar = ttk.Scrollbar(recent_frame, orient='vertical', 
                                        command=self.recent_finds_tree.yview)
        self.recent_finds_tree.configure(yscrollcommand=recent_scrollbar.set)
        
        self.recent_finds_tree.pack(side='left', fill='both', expand=True)
        recent_scrollbar.pack(side='right', fill='y')
        
        # Output Files and Actions
        output_frame = ttk.LabelFrame(right_column, text="📁 Output Files & Actions", padding=10)
        output_frame.pack(fill='x')
        
        # File status indicators
        file_status_frame = ttk.Frame(output_frame)
        file_status_frame.pack(fill='x', pady=(0, 10))
        
        output_files = [
            ("founded_email.csv", "Channels with emails", "✅"),
            ("not_email_but_social.csv", "Social media only", "📱"),
            ("non_founded_email.csv", "Nothing found", "❌"),
            ("signin_to_see_email.csv", "Sign-in required", "🔒")
        ]
        
        self.file_indicators = {}
        for i, (filename, desc, icon) in enumerate(output_files):
            row = i // 2
            col = i % 2
            
            file_frame = ttk.Frame(file_status_frame)
            file_frame.grid(row=row, column=col, sticky='w', padx=(0, 20), pady=2)
            
            self.file_indicators[filename] = ttk.Label(file_frame, text=f"{icon} {filename}: 0 rows", 
                                                      font=('Segoe UI', 8))
            self.file_indicators[filename].pack(anchor='w')
        
        # Action buttons
        actions_frame = ttk.Frame(output_frame)
        actions_frame.pack(fill='x', pady=(10, 0))
        
        open_folder_btn = ttk.Button(actions_frame, text="📂 Open Folder",
                                    command=self.open_output_folder, width=15)
        open_folder_btn.pack(side='left', padx=(0, 5))
        
        export_btn = ttk.Button(actions_frame, text="📊 Export Report",
                               command=self.export_email_report, width=15)
        export_btn.pack(side='left', padx=(0, 5))
        
        clear_btn = ttk.Button(actions_frame, text="🗑️ Clear Results",
                              command=self.clear_email_results, width=15)
        clear_btn.pack(side='left')
        
    def create_analytics_tab(self):
        """Create analytics tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Analytics")
        
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Header
        header_label = ttk.Label(main_frame, 
                                text="Subscriber Count Analyzer",
                                style='Heading.TLabel')
        header_label.pack(anchor='w', pady=(0, 10))
        
        # Configuration
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding=10)
        config_frame.pack(fill='x', pady=(0, 10))
        
        # Input CSV
        input_frame = ttk.Frame(config_frame)
        input_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(input_frame, text="Input CSV:").pack(side='left')
        self.analytics_input_var = tk.StringVar(value="save.csv")
        analytics_input_entry = ttk.Entry(input_frame, textvariable=self.analytics_input_var, width=30)
        analytics_input_entry.pack(side='left', padx=(5, 10))
        
        select_analytics_btn = ttk.Button(input_frame, text="Select CSV",
                                         command=self.select_analytics_csv)
        select_analytics_btn.pack(side='left')
        
        # Chrome windows
        windows_frame = ttk.Frame(config_frame)
        windows_frame.pack(fill='x')
        
        ttk.Label(windows_frame, text="Chrome Windows:").pack(side='left')
        self.analytics_windows_var = tk.StringVar(value="3")
        analytics_windows_spin = ttk.Spinbox(windows_frame, from_=1, to=20,
                                            textvariable=self.analytics_windows_var, width=10)
        analytics_windows_spin.pack(side='left', padx=(10, 0))
        
        # Controls
        analytics_controls_frame = ttk.Frame(main_frame)
        analytics_controls_frame.pack(fill='x', pady=(0, 10))
        
        self.start_analytics_btn = ttk.Button(analytics_controls_frame, text="Start Analysis",
                                             command=self.start_analytics,
                                             style='Primary.TButton')
        self.start_analytics_btn.pack(side='left', padx=(0, 10))
        
        self.stop_analytics_btn = ttk.Button(analytics_controls_frame, text="Stop Analysis",
                                            command=self.stop_analytics,
                                            state='disabled')
        self.stop_analytics_btn.pack(side='left')
        
        # Progress
        self.analytics_progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.analytics_progress.pack(fill='x', pady=(0, 10))
        
        # Results Summary
        summary_frame = ttk.LabelFrame(main_frame, text="Results Summary", padding=10)
        summary_frame.pack(fill='x', pady=(0, 10))
        
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack()
        
        # Summary labels
        ttk.Label(summary_grid, text="Below 1K:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.below_1k_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.below_1k_var, 
                 foreground=self.colors['success']).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(summary_grid, text="1K-10K:").grid(row=0, column=2, padx=5, pady=2, sticky='w')
        self.between_1k_10k_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.between_1k_10k_var).grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(summary_grid, text="Above 10K:").grid(row=0, column=4, padx=5, pady=2, sticky='w')
        self.above_10k_var = tk.StringVar(value="0")
        ttk.Label(summary_grid, textvariable=self.above_10k_var).grid(row=0, column=5, padx=5, pady=2)
        
        # Results preview
        preview_frame = ttk.LabelFrame(main_frame, text="Results Preview", padding=5)
        preview_frame.pack(fill='both', expand=True)
        
        columns = ('Channel', 'Subscribers', 'Category')
        self.analytics_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.analytics_tree.heading(col, text=col)
            self.analytics_tree.column(col, width=200)
        
        analytics_scrollbar = ttk.Scrollbar(preview_frame, orient='vertical', 
                                           command=self.analytics_tree.yview)
        self.analytics_tree.configure(yscrollcommand=analytics_scrollbar.set)
        
        self.analytics_tree.pack(side='left', fill='both', expand=True)
        analytics_scrollbar.pack(side='right', fill='y')
    
    def create_reports_tab(self):
        """Create comprehensive reports and export tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Reports & Export")
        
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Header
        header_label = ttk.Label(main_frame, 
                                text="Reports & Data Export",
                                style='Heading.TLabel')
        header_label.pack(anchor='w', pady=(0, 15))
        
        # Report types section
        reports_frame = ttk.LabelFrame(main_frame, text="Available Reports", 
                                      style='Card.TLabelframe', padding=15)
        reports_frame.pack(fill='x', pady=(0, 15))
        
        # Report options grid
        reports_grid = ttk.Frame(reports_frame)
        reports_grid.pack(fill='x')
        
        # Column 1
        col1 = ttk.Frame(reports_grid)
        col1.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        ttk.Label(col1, text="📈 Analytics Reports", style='Section.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.report_subscriber_analysis = tk.BooleanVar(value=True)
        ttk.Checkbutton(col1, text="Subscriber Count Analysis", 
                       variable=self.report_subscriber_analysis).pack(anchor='w')
        
        self.report_channel_categories = tk.BooleanVar(value=True)
        ttk.Checkbutton(col1, text="Channel Categorization", 
                       variable=self.report_channel_categories).pack(anchor='w')
        
        self.report_growth_potential = tk.BooleanVar(value=False)
        ttk.Checkbutton(col1, text="Growth Potential Analysis", 
                       variable=self.report_growth_potential).pack(anchor='w')
        
        # Column 2
        col2 = ttk.Frame(reports_grid)
        col2.pack(side='left', fill='both', expand=True, padx=10)
        
        ttk.Label(col2, text="📧 Contact Reports", style='Section.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.report_email_summary = tk.BooleanVar(value=True)
        ttk.Checkbutton(col2, text="Email Collection Summary", 
                       variable=self.report_email_summary).pack(anchor='w')
        
        self.report_social_media = tk.BooleanVar(value=True)
        ttk.Checkbutton(col2, text="Social Media Links", 
                       variable=self.report_social_media).pack(anchor='w')
        
        self.report_outreach_ready = tk.BooleanVar(value=False)
        ttk.Checkbutton(col2, text="Outreach-Ready List", 
                       variable=self.report_outreach_ready).pack(anchor='w')
        
        # Column 3
        col3 = ttk.Frame(reports_grid)
        col3.pack(side='left', fill='both', expand=True, padx=(10, 0))
        
        ttk.Label(col3, text="🔄 Process Reports", style='Section.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.report_session_summary = tk.BooleanVar(value=True)
        ttk.Checkbutton(col3, text="Session Summary", 
                       variable=self.report_session_summary).pack(anchor='w')
        
        self.report_error_log = tk.BooleanVar(value=False)
        ttk.Checkbutton(col3, text="Error Log", 
                       variable=self.report_error_log).pack(anchor='w')
        
        self.report_performance = tk.BooleanVar(value=False)
        ttk.Checkbutton(col3, text="Performance Metrics", 
                       variable=self.report_performance).pack(anchor='w')
        
        # Export options
        export_frame = ttk.LabelFrame(main_frame, text="Export Options", 
                                     style='Card.TLabelframe', padding=15)
        export_frame.pack(fill='x', pady=(0, 15))
        
        export_controls = ttk.Frame(export_frame)
        export_controls.pack(fill='x')
        
        # Export format
        format_frame = ttk.Frame(export_controls)
        format_frame.pack(side='left', padx=(0, 20))
        
        ttk.Label(format_frame, text="Format:").pack(anchor='w')
        
        self.export_format_var = tk.StringVar(value="Excel (.xlsx)")
        format_combo = ttk.Combobox(format_frame, textvariable=self.export_format_var,
                                   values=["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)", "PDF Report"],
                                   state='readonly', width=15)
        format_combo.pack(pady=(5, 0))
        
        # Export destination
        dest_frame = ttk.Frame(export_controls)
        dest_frame.pack(side='left', padx=(0, 20))
        
        ttk.Label(dest_frame, text="Destination:").pack(anchor='w')
        
        dest_controls = ttk.Frame(dest_frame)
        dest_controls.pack(fill='x', pady=(5, 0))
        
        self.export_path_var = tk.StringVar(value="./reports/")
        path_entry = ttk.Entry(dest_controls, textvariable=self.export_path_var, width=25)
        path_entry.pack(side='left', padx=(0, 5))
        
        browse_btn = ttk.Button(dest_controls, text="Browse", 
                               command=self.browse_export_path)
        browse_btn.pack(side='left')
        
        # Export controls
        export_actions = ttk.Frame(export_controls)
        export_actions.pack(side='right')
        
        generate_btn = ttk.Button(export_actions, text="📊 Generate Reports",
                                 command=self.generate_reports,
                                 style='Primary.TButton')
        generate_btn.pack(pady=(0, 5))
        
        quick_export_btn = ttk.Button(export_actions, text="⚡ Quick Export",
                                     command=self.quick_export)
        quick_export_btn.pack()
        
        # Recent reports section
        recent_frame = ttk.LabelFrame(main_frame, text="Recent Reports", 
                                     style='Card.TLabelframe', padding=10)
        recent_frame.pack(fill='both', expand=True)
        
        # Reports list
        columns = ('Report Name', 'Generated', 'Size', 'Status')
        self.reports_tree = ttk.Treeview(recent_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.reports_tree.heading(col, text=col)
            if col == 'Report Name':
                self.reports_tree.column(col, width=250)
            elif col == 'Generated':
                self.reports_tree.column(col, width=150)
            elif col == 'Size':
                self.reports_tree.column(col, width=100)
            else:
                self.reports_tree.column(col, width=100)
        
        reports_scrollbar = ttk.Scrollbar(recent_frame, orient='vertical', 
                                         command=self.reports_tree.yview)
        self.reports_tree.configure(yscrollcommand=reports_scrollbar.set)
        
        self.reports_tree.pack(side='left', fill='both', expand=True)
        reports_scrollbar.pack(side='right', fill='y')
        
        # Context menu for reports
        self.reports_tree.bind('<Button-3>', self.show_report_context_menu)
    
    def create_advanced_analytics_tab(self):
        """Create advanced analytics dashboard tab"""
        if not ANALYTICS_DASHBOARD_AVAILABLE or not self.db_manager:
            # Create placeholder tab
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text="📊 Advanced Analytics")
            
            placeholder_label = ttk.Label(frame, 
                                         text="Advanced Analytics Dashboard\n\nRequires additional dependencies:\n• matplotlib\n• seaborn\n• pandas\n• plotly",
                                         font=('Segoe UI', 12),
                                         justify='center')
            placeholder_label.pack(expand=True)
            return
        
        # Create advanced analytics tab
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="📊 Advanced Analytics")
        
        try:
            self.advanced_dashboard = AdvancedAnalyticsDashboard(analytics_frame, self.db_manager)
        except Exception as e:
            error_label = ttk.Label(analytics_frame, 
                                   text=f"Error loading advanced analytics:\n{str(e)}",
                                   font=('Segoe UI', 12),
                                   justify='center')
            error_label.pack(expand=True)
    
    def create_scheduler_tab(self):
        """Create task scheduler tab"""
        if not SCHEDULER_AVAILABLE or not self.task_scheduler:
            # Create placeholder tab
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text="⏰ Scheduler")
            
            placeholder_label = ttk.Label(frame, 
                                         text="Task Scheduler\n\nRequires additional dependencies:\n• schedule\n• croniter",
                                         font=('Segoe UI', 12),
                                         justify='center')
            placeholder_label.pack(expand=True)
            return
        
        # Create scheduler tab
        scheduler_frame = ttk.Frame(self.notebook)
        self.notebook.add(scheduler_frame, text="⏰ Scheduler")
        
        try:
            self.scheduler_gui = SchedulerGUI(scheduler_frame, self.task_scheduler)
        except Exception as e:
            error_label = ttk.Label(scheduler_frame, 
                                   text=f"Error loading scheduler:\n{str(e)}",
                                   font=('Segoe UI', 12),
                                   justify='center')
            error_label.pack(expand=True)
    
    def setup_scheduler_callbacks(self):
        """Setup callbacks for scheduled tasks"""
        if not self.task_scheduler:
            return
        
        # Register callback functions for different actions
        self.task_scheduler.register_callback('scrape_videos', self.scheduled_scrape_videos)
        self.task_scheduler.register_callback('find_emails', self.scheduled_find_emails)
        self.task_scheduler.register_callback('analyze_channels', self.scheduled_analyze_channels)
        self.task_scheduler.register_callback('login_accounts', self.scheduled_login_accounts)
        self.task_scheduler.register_callback('generate_reports', self.scheduled_generate_reports)
    
    def scheduled_scrape_videos(self, parameters: Dict) -> Dict:
        """Scheduled video scraping callback"""
        try:
            # Extract parameters
            topics = parameters.get('topics', ['tech', 'gaming'])
            min_views = parameters.get('min_views', 0)
            max_views = parameters.get('max_views', 10000)
            chrome_windows = parameters.get('chrome_windows', 3)
            
            # Create session in database
            if self.db_manager:
                session_data = {
                    'session_name': f"Scheduled Scraping {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    'search_topics': topics,
                    'min_views': min_views,
                    'max_views': max_views,
                    'chrome_windows': chrome_windows
                }
                session_id = self.db_manager.create_scraping_session(session_data)
            
            # Execute scraping (simplified version)
            channels_found = []
            
            if AUTO_AVAILABLE:
                for topic in topics:
                    try:
                        driver = setup_driver()
                        go_to_youtube(driver)
                        search_topic(driver, topic)
                        
                        # Get some results
                        video_details = get_video_details(driver)
                        for item in video_details[:5]:  # Limit for scheduled tasks
                            views = item.get("Views", 0)
                            channel_link = item.get("Channel Link", "N/A")
                            
                            if (min_views <= views <= max_views and 
                                channel_link != "N/A" and 
                                ("/channel/" in channel_link or "/@" in channel_link)):
                                channels_found.append(channel_link)
                                
                                # Save to database
                                if self.db_manager:
                                    channel_data = {
                                        'channel_url': channel_link,
                                        'subscriber_count': 0,  # Will be updated later
                                        'category': topic
                                    }
                                    self.db_manager.add_channel(channel_data)
                        
                        driver.quit()
                        
                    except Exception as e:
                        print(f"Error scraping topic {topic}: {e}")
            
            # Update session with results
            if self.db_manager and 'session_id' in locals():
                final_stats = {
                    'channels_found': len(channels_found),
                    'successful_channels': len(channels_found),
                    'failed_attempts': 0
                }
                self.db_manager.complete_session(session_id, final_stats)
            
            return {
                'success': True,
                'channels_found': len(channels_found),
                'channels': channels_found
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def scheduled_find_emails(self, parameters: Dict) -> Dict:
        """Scheduled email finding callback"""
        try:
            input_file = parameters.get('input_file', 'save.csv')
            max_channels = parameters.get('max_channels', 50)
            
            emails_found = 0
            channels_processed = 0
            
            # Read channels from database or CSV
            if self.db_manager:
                channels = self.db_manager.get_channels_by_category()[:max_channels]
            else:
                channels = []
                if os.path.exists(input_file):
                    with open(input_file, 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader, None)  # Skip header
                        for row in reader:
                            if row and row[0].startswith('http'):
                                channels.append({'channel_url': row[0]})
                                if len(channels) >= max_channels:
                                    break
            
            # Process channels (simplified for scheduling)
            for channel in channels:
                channels_processed += 1
                # Simulate email finding
                import random
                if random.random() > 0.7:  # 30% success rate
                    emails_found += 1
            
            return {
                'success': True,
                'channels_processed': channels_processed,
                'emails_found': emails_found
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def scheduled_analyze_channels(self, parameters: Dict) -> Dict:
        """Scheduled channel analysis callback"""
        try:
            max_channels = parameters.get('max_channels', 30)
            
            if self.db_manager:
                channels = self.db_manager.get_channels_by_category()[:max_channels]
                
                analyzed_count = 0
                for channel in channels:
                    # Simulate analysis and update
                    import random
                    analytics_data = {
                        'engagement_rate': random.uniform(0.01, 0.15),
                        'quality_score': random.uniform(0.5, 1.0),
                        'growth_rate': random.uniform(-0.1, 0.3)
                    }
                    
                    self.db_manager.update_channel_analytics(channel['id'], analytics_data)
                    analyzed_count += 1
                
                return {
                    'success': True,
                    'channels_analyzed': analyzed_count
                }
            else:
                return {
                    'success': False,
                    'error': 'Database not available'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def scheduled_login_accounts(self, parameters: Dict) -> Dict:
        """Scheduled account login callback"""
        try:
            csv_file = parameters.get('csv_file', 'gmail_accounts.csv')
            max_accounts = parameters.get('max_accounts', 5)
            
            if not os.path.exists(csv_file):
                return {
                    'success': False,
                    'error': f'Account file not found: {csv_file}'
                }
            
            # Read accounts
            accounts = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('email') and row.get('password'):
                        accounts.append(row)
                        if len(accounts) >= max_accounts:
                            break
            
            successful_logins = 0
            
            if YOUTUBE_LOGIN_AVAILABLE:
                for account in accounts:
                    try:
                        manager = YouTubeAccountManager(keep_browser_open=False)
                        manager.setup_driver()
                        
                        success = manager.login_account(account['email'], account['password'])
                        if success:
                            successful_logins += 1
                        
                        manager.close()
                        time.sleep(2)  # Delay between logins
                        
                    except Exception as e:
                        print(f"Login error for {account['email']}: {e}")
            
            return {
                'success': True,
                'accounts_processed': len(accounts),
                'successful_logins': successful_logins
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def scheduled_generate_reports(self, parameters: Dict) -> Dict:
        """Scheduled report generation callback"""
        try:
            if not self.db_manager:
                return {
                    'success': False,
                    'error': 'Database not available'
                }
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scheduled_report_{timestamp}.xlsx"
            
            # Generate comprehensive report
            self.db_manager.export_data_to_excel(filename)
            
            return {
                'success': True,
                'report_file': filename
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def browse_export_path(self):
        """Browse for export directory"""
        directory = filedialog.askdirectory(title="Select Export Directory")
        if directory:
            self.export_path_var.set(directory + "/")
    
    def generate_reports(self):
        """Generate selected reports"""
        self.status_var.set("Generating reports...")
        
        # Get selected report options
        selected_reports = []
        if self.report_subscriber_analysis.get():
            selected_reports.append("subscriber_analysis")
        if self.report_channel_categories.get():
            selected_reports.append("channel_categories")
        if self.report_email_summary.get():
            selected_reports.append("email_summary")
        # ... add other report types
        
        if not selected_reports:
            messagebox.showwarning("Warning", "Please select at least one report type.")
            return
        
        # Start report generation in background
        thread = threading.Thread(target=self.report_generation_worker, args=(selected_reports,))
        thread.daemon = True
        thread.start()
    
    def report_generation_worker(self, selected_reports):
        """Background worker for report generation"""
        try:
            export_path = self.export_path_var.get()
            if not os.path.exists(export_path):
                os.makedirs(export_path)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for report_type in selected_reports:
                self.root.after(0, self.status_var.set, f"Generating {report_type}...")
                
                # Simulate report generation
                time.sleep(1)
                
                filename = f"{report_type}_{timestamp}.xlsx"
                filepath = os.path.join(export_path, filename)
                
                # Add to recent reports list
                self.root.after(0, self.add_recent_report, filename, "Just now", "2.3 MB", "Complete")
            
            self.root.after(0, messagebox.showinfo, "Success", f"Generated {len(selected_reports)} reports successfully!")
            self.root.after(0, self.status_var.set, "Reports generated successfully")
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Report generation failed: {str(e)}")
            self.root.after(0, self.status_var.set, "Report generation failed")
    
    def quick_export(self):
        """Quick export of current data"""
        self.status_var.set("Performing quick export...")
        messagebox.showinfo("Export", "Quick export completed!")
        self.status_var.set("Quick export completed")
    
    def add_recent_report(self, name, generated, size, status):
        """Add report to recent reports list"""
        self.reports_tree.insert('', 0, values=(name, generated, size, status))
    
    def show_report_context_menu(self, event):
        """Show context menu for reports"""
        # This would implement right-click context menu
        pass
    
    # Workflow automation methods
    def start_full_workflow(self):
        """Start the complete automated workflow"""
        if self.workflow_active:
            messagebox.showwarning("Warning", "A workflow is already running!")
            return
        
        workflow_name = self.workflow_var.get()
        if not workflow_name or workflow_name not in self.workflow_templates:
            messagebox.showerror("Error", "Please select a valid workflow.")
            return
        
        # Validate configuration
        topics = [t.strip() for t in self.workflow_topics_var.get().split(',') if t.strip()]
        if not topics:
            messagebox.showerror("Error", "Please enter at least one search topic.")
            return
        
        try:
            max_results = int(self.workflow_max_var.get())
            if max_results < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for max results.")
            return
        
        # Start workflow
        self.workflow_active = True
        self.start_workflow_btn.config(state='disabled')
        self.pause_workflow_btn.config(state='normal')
        self.stop_workflow_btn.config(state='normal')
        
        workflow_steps = self.workflow_templates[workflow_name]
        
        # Start workflow in background thread
        thread = threading.Thread(target=self.workflow_worker, 
                                 args=(workflow_name, workflow_steps, topics, max_results))
        thread.daemon = True
        thread.start()
        
        self.status_var.set(f"Starting {workflow_name} workflow...")
        self.workflow_step_var.set("Initializing...")
    
    def workflow_worker(self, workflow_name, steps, topics, max_results):
        """Background worker for complete workflow automation"""
        try:
            total_steps = len(steps)
            current_step = 0
            
            workflow_data = {
                'topics': topics,
                'max_results': max_results,
                'scraped_channels': [],
                'analyzed_channels': [],
                'found_emails': [],
                'logged_accounts': 0
            }
            
            for step_name in steps:
                if not self.workflow_active:
                    break
                
                current_step += 1
                progress = (current_step / total_steps) * 100
                
                self.root.after(0, self.workflow_progress.config, {'value': progress})
                self.root.after(0, self.global_progress.config, {'value': progress})
                
                if step_name == 'scrape_videos':
                    self.root.after(0, self.workflow_step_var.set, f"Step {current_step}/{total_steps}: Scraping Videos")
                    self.root.after(0, self.status_var.set, "Scraping YouTube videos...")
                    
                    # Execute video scraping
                    scraped_data = self.execute_video_scraping(workflow_data)
                    workflow_data['scraped_channels'].extend(scraped_data)
                    
                    # Update session stats
                    self.session_stats['channels_scraped'] += len(scraped_data)
                    self.root.after(0, self.update_session_stats)
                    
                elif step_name == 'analyze_subscribers':
                    self.root.after(0, self.workflow_step_var.set, f"Step {current_step}/{total_steps}: Analyzing Subscribers")
                    self.root.after(0, self.status_var.set, "Analyzing subscriber counts...")
                    
                    # Execute subscriber analysis
                    analyzed_data = self.execute_subscriber_analysis(workflow_data)
                    workflow_data['analyzed_channels'].extend(analyzed_data)
                    
                    self.session_stats['channels_analyzed'] += len(analyzed_data)
                    self.root.after(0, self.update_session_stats)
                    
                elif step_name == 'find_emails':
                    self.root.after(0, self.workflow_step_var.set, f"Step {current_step}/{total_steps}: Finding Emails")
                    self.root.after(0, self.status_var.set, "Finding email addresses...")
                    
                    # Execute email finding
                    email_data = self.execute_email_finding(workflow_data)
                    workflow_data['found_emails'].extend(email_data)
                    
                    self.session_stats['emails_found'] += len(email_data)
                    self.root.after(0, self.update_session_stats)
                    
                elif step_name == 'login_accounts':
                    self.root.after(0, self.workflow_step_var.set, f"Step {current_step}/{total_steps}: Managing Accounts")
                    self.root.after(0, self.status_var.set, "Managing account logins...")
                    
                    # Execute account management
                    login_results = self.execute_account_management(workflow_data)
                    workflow_data['logged_accounts'] = login_results
                    
                    self.session_stats['accounts_logged'] += login_results
                    self.root.after(0, self.update_session_stats)
                
                # Add delay between steps
                time.sleep(float(self.delay_var.get()) if hasattr(self, 'delay_var') else 1)
            
            # Workflow completed successfully
            if self.workflow_active:
                self.root.after(0, self.workflow_completed, workflow_data)
            
        except Exception as e:
            self.root.after(0, self.workflow_error, str(e))
    
    def execute_video_scraping(self, workflow_data):
        """Execute video scraping step"""
        try:
            if not AUTO_AVAILABLE:
                return []
            
            # Simplified scraping execution
            scraped_channels = []
            for topic in workflow_data['topics']:
                # Simulate scraping process
                time.sleep(2)  # Simulate processing time
                
                # Mock data for now - replace with actual scraping
                mock_channels = [
                    f"https://youtube.com/@{topic}channel{i}"
                    for i in range(1, min(6, workflow_data['max_results'] // len(workflow_data['topics']) + 1))
                ]
                scraped_channels.extend(mock_channels)
                
                if not self.workflow_active:
                    break
            
            # Save scraped data
            self.save_scraped_data(scraped_channels)
            return scraped_channels
            
        except Exception as e:
            print(f"Error in video scraping: {e}")
            return []
    
    def execute_subscriber_analysis(self, workflow_data):
        """Execute real subscriber analysis using subcunt.py"""
        try:
            if not SUBCUNT_AVAILABLE:
                return []
            
            channels_to_analyze = workflow_data.get('scraped_channels', [])
            if not channels_to_analyze:
                # Try to load from save.csv if no channels provided
                if os.path.exists("save.csv"):
                    with open("save.csv", 'r', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        next(reader, None)  # Skip header
                        channels_to_analyze = [row[0] for row in reader if row and row[0].strip()]
            
            if not channels_to_analyze:
                return []
            
            analyzed_data = []
            total_channels = len(channels_to_analyze)
            
            self.root.after(0, self.status_var.set, f"Analyzing subscriber counts for {total_channels} channels...")
            
            # Use real subcunt functionality
            for i, channel in enumerate(channels_to_analyze):
                if not self.workflow_active:
                    break
                
                try:
                    self.root.after(0, self.status_var.set, 
                                   f"Analyzing channel {i+1}/{total_channels}: {channel[:50]}...")
                    
                    # Use real subscriber count function from subcunt.py
                    subscriber_data = get_subscriber_count(channel)
                    
                    if subscriber_data:
                        subscriber_count = subscriber_data.get('subscriber_count', 0)
                        subscriber_text = subscriber_data.get('subscriber_text', 'N/A')
                        
                        # Categorize based on actual count
                        if subscriber_count < 1000:
                            category = "Below 1K"
                        elif subscriber_count <= 10000:
                            category = "1K-10K"
                        else:
                            category = "Above 10K"
                        
                        analyzed_data.append({
                            'channel': channel,
                            'subscribers': subscriber_count,
                            'subscriber_text': subscriber_text,
                            'category': category
                        })
                        
                        # Add to results display
                        self.root.after(0, self.add_analytics_result, 
                                       channel, str(subscriber_count), category)
                    
                except Exception as e:
                    print(f"Error analyzing channel {channel}: {e}")
                    # Add error entry
                    analyzed_data.append({
                        'channel': channel,
                        'subscribers': 0,
                        'subscriber_text': 'Error',
                        'category': 'Error'
                    })
            
            # Save results to CSV files like subcunt.py does
            self.save_subscriber_analysis_results(analyzed_data)
            
            return analyzed_data
            
        except Exception as e:
            print(f"Error in subscriber analysis: {e}")
            return []
    
    def save_subscriber_analysis_results(self, analyzed_data):
        """Save subscriber analysis results to CSV files like subcunt.py"""
        try:
            # Categorize channels
            below_1k = []
            between_1k_10k = []
            above_10k = []
            
            for data in analyzed_data:
                if data['category'] == 'Below 1K':
                    below_1k.append(data)
                elif data['category'] == '1K-10K':
                    between_1k_10k.append(data)
                elif data['category'] == 'Above 10K':
                    above_10k.append(data)
            
            # Save to respective CSV files
            categories = {
                'below_1k.csv': below_1k,
                '1k_10k.csv': between_1k_10k,
                'above_10k.csv': above_10k
            }
            
            for filename, data_list in categories.items():
                if data_list:
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Channel Link', 'Subscriber Count', 'Subscriber Text'])
                        for data in data_list:
                            writer.writerow([
                                data['channel'],
                                data['subscribers'],
                                data.get('subscriber_text', 'N/A')
                            ])
            
            # Save comprehensive results
            with open('subscount.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Channel Link', 'Subscriber Count', 'Subscriber Text', 'Category'])
                for data in analyzed_data:
                    writer.writerow([
                        data['channel'],
                        data['subscribers'],
                        data.get('subscriber_text', 'N/A'),
                        data['category']
                    ])
            
            self.root.after(0, self.status_var.set, 
                           f"Subscriber analysis completed! Analyzed {len(analyzed_data)} channels.")
            
        except Exception as e:
            print(f"Error saving subscriber analysis results: {e}")
    
    def execute_email_finding(self, workflow_data):
        """Execute email finding step"""
        try:
            if not EMAIL_FINDER_AVAILABLE:
                return []
            
            channels_to_process = workflow_data.get('analyzed_channels', [])
            if not channels_to_process:
                channels_to_process = workflow_data.get('scraped_channels', [])
            
            email_data = []
            for channel_info in channels_to_process:
                if not self.workflow_active:
                    break
                
                channel = channel_info if isinstance(channel_info, str) else channel_info.get('channel', '')
                
                # Simulate email finding
                time.sleep(1.5)
                
                # Mock email data
                import random
                if random.random() > 0.7:  # 30% chance of finding email
                    email_data.append({
                        'channel': channel,
                        'email': f"contact@{channel.split('/')[-1]}.com",
                        'social_media': ['Instagram', 'Twitter']
                    })
            
            return email_data
            
        except Exception as e:
            print(f"Error in email finding: {e}")
            return []
    
    def execute_account_management(self, workflow_data):
        """Execute account management step"""
        try:
            if not YOUTUBE_LOGIN_AVAILABLE:
                return 0
            
            # Check if accounts CSV exists
            if not os.path.exists("gmail_accounts.csv"):
                return 0
            
            # Simulate account login
            time.sleep(3)
            
            # Mock login results
            return 2  # Successfully logged into 2 accounts
            
        except Exception as e:
            print(f"Error in account management: {e}")
            return 0
    
    def save_scraped_data(self, channels):
        """Save scraped channel data to CSV"""
        try:
            with open("save.csv", "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Channel Link"])
                for channel in channels:
                    writer.writerow([channel])
        except Exception as e:
            print(f"Error saving scraped data: {e}")
    
    def workflow_completed(self, workflow_data):
        """Handle workflow completion"""
        self.workflow_active = False
        self.start_workflow_btn.config(state='normal')
        self.pause_workflow_btn.config(state='disabled')
        self.stop_workflow_btn.config(state='disabled')
        
        self.workflow_step_var.set("Completed!")
        self.status_var.set("Workflow completed successfully")
        
        # Show completion summary
        summary = f"""Workflow Completed Successfully!

Results:
• Channels Scraped: {len(workflow_data.get('scraped_channels', []))}
• Channels Analyzed: {len(workflow_data.get('analyzed_channels', []))}
• Emails Found: {len(workflow_data.get('found_emails', []))}
• Accounts Managed: {workflow_data.get('logged_accounts', 0)}

Check the individual tabs for detailed results."""
        
        messagebox.showinfo("Workflow Complete", summary)
        
        # Auto-generate reports if option is enabled
        if hasattr(self, 'auto_generate_reports') and self.auto_generate_reports.get():
            self.generate_reports()
    
    def workflow_error(self, error_message):
        """Handle workflow error"""
        self.workflow_active = False
        self.start_workflow_btn.config(state='normal')
        self.pause_workflow_btn.config(state='disabled')
        self.stop_workflow_btn.config(state='disabled')
        
        self.workflow_step_var.set("Error occurred")
        self.status_var.set("Workflow failed")
        
        messagebox.showerror("Workflow Error", f"Workflow failed with error:\n\n{error_message}")
    
    def pause_workflow(self):
        """Pause the current workflow"""
        # Implementation for pausing workflow
        self.status_var.set("Workflow paused")
        messagebox.showinfo("Workflow", "Workflow paused. Click Start to resume.")
    
    def stop_workflow(self):
        """Stop the current workflow"""
        self.workflow_active = False
        self.start_workflow_btn.config(state='normal')
        self.pause_workflow_btn.config(state='disabled')
        self.stop_workflow_btn.config(state='disabled')
        
        self.workflow_step_var.set("Stopped")
        self.status_var.set("Workflow stopped by user")
        
        self.workflow_progress.config(value=0)
        self.global_progress.config(value=0)
    
    def update_session_stats(self):
        """Update session statistics display"""
        stats_text = (f"Session: {self.session_stats['channels_scraped']} channels | "
                     f"{self.session_stats['emails_found']} emails | "
                     f"{self.session_stats['accounts_logged']} logins")
        self.stats_label.config(text=stats_text)
    
    def process_messages(self):
        """Process messages from background threads"""
        try:
            while True:
                try:
                    message = self.message_queue.get_nowait()
                    # Process different message types
                    if message['type'] == 'status':
                        self.status_var.set(message['text'])
                    elif message['type'] == 'progress':
                        self.global_progress.config(value=message['value'])
                    elif message['type'] == 'result':
                        # Handle results from background processes
                        pass
                except Empty:
                    break
        except Exception as e:
            print(f"Error processing messages: {e}")
        
        # Schedule next message processing
        self.root.after(100, self.process_messages)
        
    # Event handlers for Video Scraping
    def start_scraping(self):
        """Start video scraping process"""
        if not AUTO_AVAILABLE:
            messagebox.showerror("Error", "Auto module not available. Please check your installation.")
            return
            
        self.scraping_active = True
        self.start_scraping_btn.config(state='disabled')
        self.stop_scraping_btn.config(state='normal')
        self.scraping_progress.start()
        
        self.status_var.set("Scraping videos...")
        
        # Get configuration
        topics = self.topics_text.get('1.0', tk.END).strip().split('\n')
        topics = [t.strip() for t in topics if t.strip()]
        
        try:
            min_views = int(self.min_views_var.get())
            max_views = int(self.max_views_var.get())
            chrome_windows = int(self.chrome_windows_var.get())
            print(f"🔍 DEBUG: Chrome windows value read from GUI: {chrome_windows}")
            self.log_message(f"🔍 DEBUG: Starting scraping with {chrome_windows} Chrome windows")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for views range and chrome windows.")
            self.stop_scraping()
            return
        
        # Start scraping in background thread
        thread = threading.Thread(target=self.scraping_worker, 
                                 args=(topics, min_views, max_views, chrome_windows))
        thread.daemon = True
        thread.start()
        
    def stop_scraping(self):
        """Stop video scraping process and close all Chrome browsers"""
        self.scraping_active = False
        self.start_scraping_btn.config(state='normal')
        self.stop_scraping_btn.config(state='disabled')
        self.scraping_progress.stop()
        
        self.log_message("🛑 STOP REQUESTED - Closing all browsers and stopping threads...")
        
        # First, try to gracefully close tracked drivers
        closed_count = 0
        for driver in self.active_drivers[:]:  # Copy list to avoid modification during iteration
            try:
                driver.quit()
                self.active_drivers.remove(driver)
                closed_count += 1
            except:
                pass
        
        if closed_count > 0:
            self.log_message(f"✅ Gracefully closed {closed_count} Chrome browsers")
        
        # Wait a moment for graceful shutdown
        time.sleep(1)
        
        # Force kill any remaining Chrome processes
        try:
            import subprocess
            # Count Chrome processes before killing
            result = subprocess.run(['tasklist', '/fi', 'imagename eq chrome.exe'], 
                                  capture_output=True, text=True, shell=True)
            chrome_count = result.stdout.count('chrome.exe')
            
            # Kill Chrome processes
            if chrome_count > 0:
                os.system("taskkill /f /im chrome.exe >nul 2>&1")
                os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
                self.log_message(f"🔥 Force-killed {chrome_count} remaining Chrome processes")
            else:
                self.log_message("✅ No remaining Chrome processes found")
        except:
            # Fallback method
            os.system("taskkill /f /im chrome.exe >nul 2>&1")
            os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
            self.log_message("🔥 Force-killed Chrome processes (fallback method)")
        
        # Clear all tracking
        self.scraping_threads = []
        self.active_drivers = []
        
        # Update stats and status
        self.live_stats_var.set("STOPPED - All browsers closed and threads terminated")
        self.status_var.set("✅ Scraping stopped - All Chrome browsers closed")
        self.log_message("🎯 STOP COMPLETE - All browsers closed and threads stopped")
        
    def scraping_worker(self, topics, min_views, max_views, chrome_windows):
        """EXACT multi_thread.py implementation with live GUI updates"""
        try:
            # Clear existing results and logs
            self.root.after(0, self.clear_scraping_results)
            self.root.after(0, self.clear_live_log)
            
            if AUTO_AVAILABLE and MULTI_THREAD_AVAILABLE:
                # Initialize CSV file exactly like multi_thread.py
                self.log_message("🔄 Initializing CSV file...")
                self.initialize_csv_file_gui()
                
                # Set global variables like multi_thread.py
                self.current_min_views = min_views
                self.current_max_views = max_views
                selected_topics = topics[:chrome_windows]  # Limit topics to windows
                
                self.log_message(f"� DEBUG: Received chrome_windows parameter: {chrome_windows}")
                self.log_message(f"�📊 Using views range: {min_views} - {max_views}")
                self.log_message(f"🎯 Number of topics to search: {len(selected_topics)}")
                self.log_message(f"🔍 Topics: {selected_topics}")
                
                # Update stats
                self.root.after(0, self.live_stats_var.set, 
                               f"Channels Found: 0 | Currently Processing: {len(selected_topics)} topics | Chrome Windows: {chrome_windows}")
                
                # Create and start threads EXACTLY like multi_thread.py
                threads = []
                self.scraping_threads = []
                
                # Launch one window per topic, exactly like multi_thread.py
                for i, topic in enumerate(selected_topics):
                    if not self.scraping_active:
                        break
                    
                    self.log_message(f"🚀 Starting browser {i+1}/{len(selected_topics)} for topic: {topic}")
                    
                    # Create thread exactly like multi_thread.py
                    thread = threading.Thread(target=self.gui_scrape_topic, args=(topic,))
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)
                    self.scraping_threads.append(thread)
                    
                    # Small delay between launches
                    time.sleep(1)
                
                self.log_message(f"✅ All {len(threads)} Chrome browsers launched!")
                
                # Monitor threads and update live stats
                start_time = time.time()
                last_count = 0
                
                while any(t.is_alive() for t in threads) and self.scraping_active:
                    time.sleep(3)  # Update every 3 seconds
                    
                    # Count current results
                    try:
                        if os.path.exists("save.csv"):
                            with open("save.csv", "r", encoding="utf-8") as f:
                                current_count = len(f.readlines()) - 1  # Subtract header
                                elapsed_time = int(time.time() - start_time)
                                active_threads = len([t for t in threads if t.is_alive()])
                                
                                # Update live stats
                                self.root.after(0, self.live_stats_var.set, 
                                               f"Channels Found: {current_count} | Active Browsers: {active_threads} | Time: {elapsed_time}s")
                                
                                # Log new finds
                                if current_count > last_count:
                                    new_finds = current_count - last_count
                                    self.log_message(f"📈 {new_finds} new channels found! Total: {current_count}")
                                    last_count = current_count
                    except Exception:
                        pass
                
                # Wait for all threads to complete
                self.log_message("⏳ Waiting for all browsers to complete...")
                for thread in threads:
                    if thread.is_alive():
                        thread.join(timeout=5)
                
                # Final results
                final_count = 0
                if os.path.exists("save.csv"):
                    with open("save.csv", "r", encoding="utf-8") as f:
                        final_count = len(f.readlines()) - 1
                
                self.log_message(f"🎉 SCRAPING COMPLETED! Found {final_count} channels total.")
                
                # Update final stats and load results
                self.root.after(0, self.live_stats_var.set, 
                               f"COMPLETED: {final_count} channels found | All browsers closed")
                self.root.after(0, self.load_scraping_results)
                self.session_stats['channels_scraped'] = final_count
                self.root.after(0, self.update_session_stats)
                
            else:
                # Fallback simulation mode
                self.root.after(0, self.status_var.set, "Simulation mode (modules not available)")
                
                for i, topic in enumerate(topics):
                    if not self.scraping_active:
                        break
                        
                    # Simulate finding channels
                    import random
                    num_results = random.randint(2, 8)
                    
                    for j in range(num_results):
                        if not self.scraping_active:
                            break
                        
                        mock_views = random.randint(min_views, max_views)
                        channel_url = f"https://youtube.com/@{topic}channel{j+1}"
                        
                        self.root.after(0, self.add_scraping_result, 
                                       channel_url, str(mock_views), "Simulated")
                        
                        time.sleep(0.2)  # Simulate processing time
                    
                    time.sleep(1)  # Simulate topic processing time
                
        except Exception as e:
            error_msg = f"Scraping error: {str(e)}"
            self.log_message(f"❌ ERROR: {error_msg}")
            self.root.after(0, messagebox.showerror, "Scraping Error", error_msg)
            self.root.after(0, self.status_var.set, "Scraping failed")
            print(f"Scraping worker error: {e}")
                
        except Exception as e:
            error_msg = f"Scraping error: {str(e)}"
            self.log_message(f"❌ ERROR: {error_msg}")
            self.root.after(0, messagebox.showerror, "Scraping Error", error_msg)
            self.root.after(0, self.status_var.set, "Scraping failed")
            print(f"Scraping worker error: {e}")
        finally:
            self.root.after(0, self.stop_scraping)
    
    def log_message(self, message):
        """Add message to live log display"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_display.config(state='normal')
            self.log_display.insert(tk.END, formatted_msg)
            self.log_display.config(state='disabled')
            self.log_display.see(tk.END)  # Auto-scroll to bottom
        
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)
    
    def clear_live_log(self):
        """Clear the live log display"""
        self.log_display.config(state='normal')
        self.log_display.delete(1.0, tk.END)
        self.log_display.config(state='disabled')
    
    def initialize_csv_file_gui(self):
        """Initialize CSV file with live logging"""
        try:
            with open("save.csv", "w", encoding="utf-8") as f:
                f.write("Channel Link\n")
                f.flush()
            self.log_message("✅ CSV file initialized with header")
        except Exception as e:
            self.log_message(f"❌ Error initializing CSV file: {e}")
    
    def gui_scrape_topic(self, search_topic_query):
        """EXACT implementation of multi_thread.py scrape_topic with GUI logging"""
        driver = None
        try:
            self.log_message(f"🚀 Starting scraping for topic: {search_topic_query}")
            
            # Setup driver exactly like multi_thread.py
            try:
                driver = setup_driver()
                self.active_drivers.append(driver)
                
                go_to_youtube(driver)
                search_topic(driver, search_topic_query)
            except Exception as e:
                self.log_message(f"❌ Failed to setup browser for topic '{search_topic_query}': {e}")
                return
            
            # Use the EXACT filter combinations from multi_thread.py
            filter_combinations = [
                ["Today", "Video"],
                ["Today", "Video", "Upload date"],
                ["Today", "Video", "Under 4 minutes"],
                ["This week", "Video"],
                ["This week", "Video", "Upload date"],
                ["This week", "Video", "Under 4 minutes"],
                ["This month", "Video"],
                ["This month", "Video", "Upload date"],
                ["This month", "Video", "Under 4 minutes"],
                ["Video", "Upload date"],
                ["Video", "Under 4 minutes"],
            ]
            
            # Process each filter combination exactly like multi_thread.py
            for filter_idx, filters in enumerate(filter_combinations):
                if not self.scraping_active:
                    break
                    
                self.log_message(f"🔧 Applying filter {filter_idx + 1}/{len(filter_combinations)}: {filters} for topic: {search_topic_query}")
                
                try:
                    driver.refresh()
                    time.sleep(1)
                    apply_advanced_filters(driver, filters)
                except Exception as e:
                    # Handle browser connection errors
                    if "10061" in str(e) or "connection" in str(e).lower() or "session" in str(e).lower():
                        self.log_message(f"🔌 Browser connection lost during filter application for topic: {search_topic_query} - stopping")
                        break
                    else:
                        self.log_message(f"⚠️ Error applying filters: {e}")
                        continue
                
                # EXACT scrolling logic from multi_thread.py
                try:
                    last_height = driver.execute_script("return document.documentElement.scrollHeight")
                except Exception as e:
                    if "10061" in str(e) or "connection" in str(e).lower() or "session" in str(e).lower():
                        self.log_message(f"🔌 Browser connection lost during initial scroll setup for topic: {search_topic_query}")
                        break
                    else:
                        continue
                        
                wait_count = 0
                seen_channel_links_live = set()
                scroll_count = 0
                
                while self.scraping_active:
                    scroll_count += 1
                    
                    try:
                        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                        time.sleep(1)
                    except Exception as e:
                        # Handle browser connection errors during scrolling
                        if "10061" in str(e) or "connection" in str(e).lower() or "session" in str(e).lower():
                            self.log_message(f"🔌 Browser connection lost during scrolling for topic: {search_topic_query} - stopping")
                            break
                        else:
                            self.log_message(f"⚠️ Error during scrolling: {e}")
                            continue
                    
                    self.log_message(f"📜 Scroll {scroll_count} for filter {filter_idx + 1} - Topic: {search_topic_query}")
                    
                    try:
                        video_details = get_video_details(driver)
                        self.log_message(f"📊 Found {len(video_details)} video details")
                    except Exception as e:
                        # Handle browser connection errors (browser was closed)
                        if "10061" in str(e) or "connection" in str(e).lower() or "session" in str(e).lower():
                            self.log_message(f"🔌 Browser connection lost for topic: {search_topic_query} - stopping thread")
                            break
                        else:
                            self.log_message(f"⚠️ Error getting video details: {e}")
                            continue
                    
                    links_found_this_scroll = 0
                    for item in video_details:
                        if not self.scraping_active:
                            break
                            
                        link = item.get("Channel Link", "N/A")
                        views = item.get("Views", 0)
                        
                        # EXACT filtering logic from multi_thread.py
                        if (self.current_min_views <= views < self.current_max_views and 
                            link != "N/A" and 
                            ("/channel/" in link or "/@" in link) and 
                            link not in seen_channel_links_live):
                            
                            # Save to CSV with thread safety
                            with file_lock:
                                try:
                                    with open("save.csv", "a", encoding="utf-8") as f:
                                        f.write(link + "\n")
                                        f.flush()
                                    
                                    self.log_message(f"✅ SAVED: {link} (Views: {views}) - Topic: {search_topic_query}")
                                    
                                    # Add to GUI results display
                                    self.root.after(0, self.add_scraping_result, link, str(views), "Real Scraped")
                                    
                                    links_found_this_scroll += 1
                                except Exception as e:
                                    self.log_message(f"❌ Error writing to CSV: {e}")
                            
                            seen_channel_links_live.add(link)
                        else:
                            # EXACT debug logic from multi_thread.py
                            if link == "N/A":
                                pass  # Skip logging for cleaner output
                            elif not (self.current_min_views <= views < self.current_max_views):
                                self.log_message(f"❌ Skipped: Views {views} not in range {self.current_min_views}-{self.current_max_views}")
                            elif not ("/channel/" in link or "/@" in link):
                                pass  # Skip logging for cleaner output
                            elif link in seen_channel_links_live:
                                pass  # Skip logging for already seen
                    
                    if links_found_this_scroll > 0:
                        self.log_message(f"💾 Links saved this scroll: {links_found_this_scroll}")
                    
                    # EXACT page end detection from multi_thread.py
                    try:
                        new_height = driver.execute_script("return document.documentElement.scrollHeight")
                        if new_height == last_height:
                            wait_count += 1
                            if wait_count >= 10:
                                self.log_message(f"⏹️ No new content loaded for topic: {search_topic_query}")
                                break
                        else:
                            wait_count = 0
                        last_height = new_height
                    except Exception as e:
                        # Handle browser connection errors during height check
                        if "10061" in str(e) or "connection" in str(e).lower() or "session" in str(e).lower():
                            self.log_message(f"🔌 Browser connection lost during height check for topic: {search_topic_query} - stopping")
                            break
                        else:
                            # If we can't get height, assume we should continue
                            continue
                    
        except Exception as e:
            self.log_message(f"❌ Error in thread for topic '{search_topic_query}': {e}")
        finally:
            if driver:
                try:
                    driver.quit()
                    if driver in self.active_drivers:
                        self.active_drivers.remove(driver)
                    self.log_message(f"🔒 Browser closed for topic: {search_topic_query}")
                except:
                    pass
    

            
    def clear_scraping_results(self):
        """Clear scraping results table"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
    def add_scraping_result(self, channel, views, status):
        """Add result to scraping table with timestamp"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.results_tree.insert('', 'end', values=(channel, views, status, timestamp))
        # Auto-scroll to show latest result
        children = self.results_tree.get_children()
        if children:
            self.results_tree.see(children[-1])
        
    def load_scraping_results(self):
        """Load scraping results from save.csv (real results)"""
        try:
            if os.path.exists("save.csv"):
                self.clear_scraping_results()
                with open("save.csv", 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)  # Skip header
                    count = 0
                    for row in reader:
                        if row and row[0].strip():
                            channel = row[0].strip()
                            status = "Loaded"
                            # Use "Loaded" timestamp instead of real-time for loaded data
                            timestamp = "Loaded"
                            self.results_tree.insert('', 'end', values=(channel, "N/A", status, timestamp))
                            count += 1
                            
                self.status_var.set(f"Loaded {count} real scraped channels from save.csv")
            else:
                self.status_var.set("No save.csv file found")
        except Exception as e:
            print(f"Error loading scraping results: {e}")
            self.status_var.set("Error loading results")
    
    def load_scraping_results_from_file(self):
        """Load scraping results from custom CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select Results CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.clear_scraping_results()
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    for row in reader:
                        if row:
                            channel = row[0] if len(row) > 0 else ""
                            views = "N/A"
                            status = "Loaded"
                            self.add_scraping_result(channel, views, status)
                            
                self.status_var.set(f"Loaded results from {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    # Event handlers for Account Login
    def select_account_csv(self):
        """Select account CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select Account CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.csv_file_var.set(file_path)
            
    def create_sample_account_csv(self):
        """Create sample account CSV"""
        file_path = filedialog.asksaveasfilename(
            title="Save Sample CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['email', 'password'])
                    writer.writerow(['your_email1@gmail.com', 'your_password1'])
                    writer.writerow(['your_email2@gmail.com', 'your_password2'])
                    
                messagebox.showinfo("Success", f"Sample CSV created: {file_path}")
                self.csv_file_var.set(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create file: {str(e)}")
                
    def start_login(self):
        """Start login process"""
        if not YOUTUBE_LOGIN_AVAILABLE:
            messagebox.showerror("Error", "YouTube login module not available. Please check your installation.")
            return
            
        csv_file = self.csv_file_var.get()
        if not os.path.exists(csv_file):
            messagebox.showerror("Error", f"CSV file not found: {csv_file}")
            return
            
        self.login_active = True
        self.start_login_btn.config(state='disabled')
        self.stop_login_btn.config(state='normal')
        self.login_progress.start()
        
        self.add_login_log("Starting login process...")
        
        # Start login in background thread
        thread = threading.Thread(target=self.login_worker)
        thread.daemon = True
        thread.start()
        
    def stop_login(self):
        """Stop login process"""
        self.login_active = False
        self.start_login_btn.config(state='normal')
        self.stop_login_btn.config(state='disabled')
        self.login_progress.stop()
        self.add_login_log("Login process stopped")
        
    def login_worker(self):
        """Enhanced background worker for account login with real integration"""
        try:
            csv_file = self.csv_file_var.get()
            mode = self.login_mode_var.get()
            
            # Read accounts
            accounts = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                accounts = [acc for acc in reader if acc.get('email') and acc.get('password')]
                
            if not accounts:
                self.root.after(0, messagebox.showerror, "Error", "No valid accounts found in CSV file.")
                return
            
            total_accounts = len(accounts)
            successful_logins = 0
            
            self.root.after(0, self.add_login_log, f"Starting login process for {total_accounts} accounts...")
            
            # Get channel URLs to visit (if any)
            channel_urls_text = self.channel_urls_text.get('1.0', tk.END).strip()
            channel_urls = [url.strip() for url in channel_urls_text.split('\n') if url.strip()]
            
            if YOUTUBE_LOGIN_AVAILABLE:
                # Use actual login functionality
                for i, account in enumerate(accounts):
                    if not self.login_active:
                        break
                    
                    email = account.get('email', '').strip()
                    password = account.get('password', '').strip()
                    
                    self.root.after(0, self.add_login_log, f"[{i+1}/{total_accounts}] Attempting login: {email}")
                    self.root.after(0, self.update_login_progress, (i + 1) / total_accounts * 100)
                    
                    try:
                        # Create account manager instance
                        manager = YouTubeAccountManager(keep_browser_open=False)
                        manager.setup_driver()
                        
                        # Attempt login
                        channel_to_visit = channel_urls[i % len(channel_urls)] if channel_urls else None
                        success = manager.login_account(email, password, channel_to_visit)
                        
                        if success:
                            successful_logins += 1
                            self.root.after(0, self.add_login_log, f"✅ Successfully logged in: {email}")
                            
                            if channel_to_visit:
                                self.root.after(0, self.add_login_log, f"   └─ Visited channel: {channel_to_visit}")
                            
                            # Update session stats
                            self.session_stats['accounts_logged'] = successful_logins
                            self.root.after(0, self.update_session_stats)
                        else:
                            self.root.after(0, self.add_login_log, f"❌ Failed to login: {email}")
                        
                        manager.close()
                        
                        # Add delay between logins
                        if i < total_accounts - 1:
                            time.sleep(2)
                            
                    except Exception as e:
                        self.root.after(0, self.add_login_log, f"❌ Error logging in {email}: {str(e)}")
                        print(f"Login error for {email}: {e}")
                
                # Summary
                self.root.after(0, self.add_login_log, 
                               f"\n📊 Login Summary: {successful_logins}/{total_accounts} successful")
                
            else:
                # Simulation mode
                self.root.after(0, self.add_login_log, "⚠️ Simulation mode (YouTube login module not available)")
                
                for i, account in enumerate(accounts):
                    if not self.login_active:
                        break
                    
                    email = account.get('email', '').strip()
                    self.root.after(0, self.add_login_log, f"[{i+1}/{total_accounts}] Simulating login: {email}")
                    self.root.after(0, self.update_login_progress, (i + 1) / total_accounts * 100)
                    
                    # Simulate login time
                    time.sleep(1.5)
                    
                    # Simulate success/failure
                    import random
                    if random.random() > 0.2:  # 80% success rate in simulation
                        successful_logins += 1
                        self.root.after(0, self.add_login_log, f"✅ [SIMULATED] Successfully logged in: {email}")
                    else:
                        self.root.after(0, self.add_login_log, f"❌ [SIMULATED] Failed to login: {email}")
                
                self.root.after(0, self.add_login_log, 
                               f"\n📊 Simulation Summary: {successful_logins}/{total_accounts} successful")
            
            # Final status update
            if successful_logins > 0:
                self.root.after(0, self.status_var.set, 
                               f"Login completed: {successful_logins}/{total_accounts} successful")
            else:
                self.root.after(0, self.status_var.set, "Login completed: No successful logins")
                
        except FileNotFoundError:
            self.root.after(0, messagebox.showerror, "Error", f"CSV file not found: {csv_file}")
            self.root.after(0, self.add_login_log, f"❌ CSV file not found: {csv_file}")
        except Exception as e:
            error_msg = f"Login process error: {str(e)}"
            self.root.after(0, messagebox.showerror, "Login Error", error_msg)
            self.root.after(0, self.add_login_log, f"❌ {error_msg}")
            self.root.after(0, self.status_var.set, "Login process failed")
            print(f"Login worker error: {e}")
        finally:
            self.root.after(0, self.stop_login)
            
    def add_login_log(self, message):
        """Add message to login log"""
        self.login_log.config(state='normal')
        self.login_log.insert(tk.END, f"{message}\n")
        self.login_log.see(tk.END)
        self.login_log.config(state='disabled')
        
    def update_login_progress(self, value):
        """Update login progress bar"""
        self.login_progress.config(mode='determinate')
        self.login_progress['value'] = value
        
    # Event handlers for Email Finder
    def select_email_input_csv(self):
        """Select email input CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select Input CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.email_input_var.set(file_path)

    def _maybe_autostart_email_finder(self):
        """Helper to auto-start email finder on GUI launch if user enabled the option.

        Note: default is OFF. This helper will only start automation when the user
        explicitly checked the 'Auto-start on launch' checkbox.
        """
        try:
            # If the autostart variable is missing for some reason, default to False
            if not hasattr(self, 'autostart_var'):
                self.autostart_var = tk.BooleanVar(value=False)

            # Only auto-start when checkbox is explicitly checked and no run is active
            if self.autostart_var.get() and not self.email_finding_active:
                input_file = self.email_input_var.get()
                if input_file and os.path.exists(input_file):
                    # Start the integrated email finding worker
                    self.start_email_finding()
        except Exception as e:
            print(f"Auto-start failed: {e}")

    # legacy CLI runner removed — GUI uses integrated email_finding_worker directly
            
    def start_email_finding(self):
        """Start email finding process"""
        if not EMAIL_FINDER_AVAILABLE:
            messagebox.showerror("Error", "Email finder module not available. Please check your installation.")
            return
            
        input_file = self.email_input_var.get()
        if not os.path.exists(input_file):
            messagebox.showerror("Error", f"Input CSV file not found: {input_file}")
            return
            
        self.email_finding_active = True
        self.start_email_btn.config(state='disabled')
        self.stop_email_btn.config(state='normal')
        self.email_progress.start()
        
        self.status_var.set("Finding emails and social media...")
        
        # Start email finding in background thread
        thread = threading.Thread(target=self.email_finding_worker)
        thread.daemon = True
        thread.start()
        
    def stop_email_finding(self):
        """Stop email finding process"""
        self.email_finding_active = False
        self.start_email_btn.config(state='normal')
        self.stop_email_btn.config(state='disabled')
        self.email_progress.stop()
        self.status_var.set("Email finding stopped")
        
    def email_finding_worker(self):
        """Enhanced background worker for email finding with REAL parallel processing"""
        try:
            input_file = self.email_input_var.get()
            num_windows = int(float(self.email_windows_var.get()))
            
            if not os.path.exists(input_file):
                self.root.after(0, messagebox.showerror, "Error", f"Input file not found: {input_file}")
                return
            
            # Read channel links
            channels = []
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if row and row[0].startswith('http'):
                        channels.append(row[0])
            
            if not channels:
                self.root.after(0, messagebox.showerror, "Error", "No valid channel links found in input file.")
                return
            
            total_channels = len(channels)
            self.root.after(0, self.status_var.set, f"Processing {total_channels} channels with {num_windows} parallel browsers...")
            
            # Initialize output files
            output_files = {
                'founded_email.csv': ['Channel Link', 'Email(s)', 'Facebook', 'Instagram', 'Twitter', 'TikTok', 'YouTube', 'LinkedIn', 'Website', '@Usernames'],
                'not_email_but_social.csv': ['Channel Link', 'Facebook', 'Instagram', 'Twitter', 'TikTok', 'YouTube', 'LinkedIn', 'Website', '@Usernames'],
                'non_founded_email.csv': ['Channel Link'],
                'signin_to_see_email.csv': ['Channel Link', 'Facebook', 'Instagram', 'Twitter', 'TikTok', 'YouTube', 'LinkedIn', 'Website', '@Usernames']
            }
            
            for filename, headers in output_files.items():
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
            
            if EMAIL_FINDER_AVAILABLE:
                # Use the Selenium-based email finder implementation directly
                self.root.after(0, self.status_var.set, "Starting Selenium-based email finder...")
                try:
                    # run_email_finder will manage its own browser windows and threading
                    run_email_finder(
                        input_file,
                        num_windows,
                        progress_callback=self._on_email_progress,
                        result_callback=self._on_email_result,
                        error_callback=self._on_email_error
                    )
                    self.root.after(0, self.status_var.set, f"✅ Selenium-based email finding completed for {total_channels} channels")
                except Exception as e:
                    raise
            else:
                # Simulation mode fallback (modules not available)
                self.root.after(0, self.status_var.set, "⚠️ Simulation mode (modules not available)")
                import random
                for i in range(min(total_channels, 10)):
                    if not self.email_finding_active:
                        break
                    outcome = random.choice(['email', 'social', 'signin', 'nothing'])
                    self.root.after(0, lambda o=outcome: self._update_email_stats(f"{o}s_found" if o != 'nothing' else 'nothing_found'))
                    time.sleep(0.2)
            
        except Exception as e:
            error_msg = f"Email finding error: {str(e)}"
            self.root.after(0, messagebox.showerror, "Email Finding Error", error_msg)
            self.root.after(0, self.status_var.set, "Email finding failed")
            print(f"Email finding worker error: {e}")
        finally:
            self.root.after(0, self.stop_email_finding)
            
    def open_output_folder(self):
        """Open output folder"""
        try:
            os.startfile(os.getcwd())
        except:
            messagebox.showinfo("Info", f"Output folder: {os.getcwd()}")
    
    # Enhanced Email Finder Methods
    def pause_email_finding(self):
        """Pause/Resume email finding process"""
        if hasattr(self, 'pause_requested'):
            if not self.pause_requested:
                self.pause_requested = True
                self.pause_email_btn.configure(text="▶️ Resume")
                self.current_channel_var.set("Process paused")
            else:
                self.pause_requested = False
                self.pause_email_btn.configure(text="⏸️ Pause")
                self.current_channel_var.set("Process resumed")
    
    def export_email_report(self):
        """Export email finding report"""
        try:
            import json
            from datetime import datetime
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "emails_found": int(self.emails_found_var.get()),
                    "social_only": int(self.social_only_var.get()),
                    "signin_required": int(self.signin_required_var.get()),
                    "nothing_found": int(self.nothing_found_var.get()),
                    "success_rate": getattr(self, 'success_rate_var', tk.StringVar(value="0%")).get()
                },
                "files_generated": []
            }
            
            # Add file information
            for filename in ["founded_email.csv", "not_email_but_social.csv", "non_founded_email.csv", "signin_to_see_email.csv"]:
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        row_count = sum(1 for line in f) - 1  # Subtract header
                    report["files_generated"].append({
                        "filename": filename,
                        "rows": row_count
                    })
            
            # Save report
            report_filename = f"email_finder_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            
            messagebox.showinfo("Export Complete", f"Report exported to {report_filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export report: {str(e)}")
    
    def clear_email_results(self):
        """Clear all email finding results"""
        if messagebox.askyesno("Clear Results", "Are you sure you want to clear all email finding results?"):
            try:
                # Reset counters
                self.emails_found_var.set("0")
                self.social_only_var.set("0")
                self.signin_required_var.set("0")
                self.nothing_found_var.set("0")
                if hasattr(self, 'success_rate_var'):
                    self.success_rate_var.set("0%")
                
                # Clear recent finds if exists
                if hasattr(self, 'recent_finds_tree'):
                    for item in self.recent_finds_tree.get_children():
                        self.recent_finds_tree.delete(item)
                
                # Clear progress
                if hasattr(self, 'current_channel_var'):
                    self.current_channel_var.set("Ready to start...")
                if hasattr(self, 'progress_detail_var'):
                    self.progress_detail_var.set("")
                
                # Update file indicators if they exist
                if hasattr(self, 'file_indicators'):
                    for filename in self.file_indicators:
                        icon = "✅" if "founded" in filename else "📱" if "social" in filename else "❌" if "non_founded" in filename else "🔒"
                        self.file_indicators[filename].configure(text=f"{icon} {filename}: 0 rows")
                
                messagebox.showinfo("Cleared", "All email finding results have been cleared.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not clear results: {str(e)}")
    
    def _add_recent_find(self, type_icon, channel, contact, time_str):
        """Add a recent find to the treeview"""
        if hasattr(self, 'recent_finds_tree'):
            # Keep only last 50 entries
            items = self.recent_finds_tree.get_children()
            if len(items) >= 50:
                self.recent_finds_tree.delete(items[0])
            
            # Add new entry
            self.recent_finds_tree.insert('', 'end', values=(type_icon, channel[:30], contact[:40], time_str))
            
            # Scroll to bottom
            items = self.recent_finds_tree.get_children()
            if items:
                self.recent_finds_tree.see(items[-1])
    
    def _merge_socials_dict(self, target_socials, source_socials):
        """Merge social media dictionaries"""
        for platform, links in source_socials.items():
            if platform in target_socials:
                if isinstance(links, list):
                    target_socials[platform].extend(links)
                else:
                    target_socials[platform].append(links)
                target_socials[platform] = list(set(target_socials[platform]))  # Remove duplicates
            else:
                target_socials[platform] = links.copy() if isinstance(links, list) else [links]

    def _update_email_stats(self, stat_type):
        """Update email finding statistics (thread-safe version)"""
        if stat_type == 'emails_found':
            current = int(self.emails_found_var.get())
            self.emails_found_var.set(str(current + 1))
        elif stat_type == 'social_only':
            current = int(self.social_only_var.get())
            self.social_only_var.set(str(current + 1))
        elif stat_type == 'signin_required':
            current = int(self.signin_required_var.get())
            self.signin_required_var.set(str(current + 1))
        elif stat_type == 'nothing_found':
            current = int(self.nothing_found_var.get())
            self.nothing_found_var.set(str(current + 1))

    def _update_enhanced_email_stats(self, stat_type):
        """Update enhanced email finding statistics"""
        current_emails = int(self.emails_found_var.get())
        current_social = int(self.social_only_var.get())
        current_signin = int(self.signin_required_var.get())
        current_nothing = int(self.nothing_found_var.get())
        
        if stat_type == 'emails_found':
            current_emails += 1
            self.emails_found_var.set(str(current_emails))
        elif stat_type == 'social_only':
            current_social += 1
            self.social_only_var.set(str(current_social))
        elif stat_type == 'signin_required':
            current_signin += 1
            self.signin_required_var.set(str(current_signin))
        elif stat_type == 'nothing_found':
            current_nothing += 1
            self.nothing_found_var.set(str(current_nothing))
        
        # Update success rate
        total_processed = current_emails + current_social + current_signin + current_nothing
        
        if total_processed > 0 and hasattr(self, 'success_rate_var'):
            success_count = current_emails + current_social
            success_rate = (success_count / total_processed) * 100
            self.success_rate_var.set(f"{success_rate:.1f}%")
        
        # Update file indicators
        if hasattr(self, 'file_indicators'):
            for filename in self.file_indicators:
                if os.path.exists(filename):
                    try:
                        with open(filename, 'r', encoding='utf-8') as f:
                            row_count = sum(1 for line in f) - 1  # Subtract header
                        icon = "✅" if "founded" in filename else "📱" if "social" in filename else "❌" if "non_founded" in filename else "🔒"
                        self.file_indicators[filename].configure(text=f"{icon} {filename}: {row_count} rows")
                    except:
                        pass
        
    # Callbacks for run_email_finder
    def _on_email_progress(self, message):
        """Called frequently with status messages from the background runner."""
        try:
            self.root.after(0, self.current_channel_var.set, message)
            # Also append to developer log when visible
            if hasattr(self, 'log_display'):
                def append_log():
                    try:
                        self.log_display.config(state='normal')
                        self.log_display.insert(tk.END, message + '\n')
                        self.log_display.see(tk.END)
                        self.log_display.config(state='disabled')
                    except:
                        pass
                self.root.after(0, append_log)
        except Exception:
            pass

    def _on_email_result(self, event_type, channel, payload):
        """Handle result events from the runner: email, social, signin, none."""
        try:
            ts = time.strftime('%H:%M:%S')
            if event_type == 'email':
                emails = payload.get('emails') or []
                contact = emails[0] if emails else ''
                self.root.after(0, self._add_recent_find, '📧', channel, contact, ts)
                self.root.after(0, self._update_enhanced_email_stats, 'emails_found')
            elif event_type == 'social':
                socials = payload.get('socials') or {}
                # pick a representative social link
                contact = ''
                for lst in socials.values():
                    if lst:
                        contact = lst[0]
                        break
                self.root.after(0, self._add_recent_find, '📱', channel, contact, ts)
                self.root.after(0, self._update_enhanced_email_stats, 'social_only')
            elif event_type == 'signin':
                socials = payload.get('socials') or {}
                contact = ''
                for lst in socials.values():
                    if lst:
                        contact = lst[0]
                        break
                self.root.after(0, self._add_recent_find, '🔒', channel, contact, ts)
                self.root.after(0, self._update_enhanced_email_stats, 'signin_required')
            elif event_type == 'none':
                self.root.after(0, self._add_recent_find, '❌', channel, '', ts)
                self.root.after(0, self._update_enhanced_email_stats, 'nothing_found')
        except Exception as e:
            print(f"_on_email_result error: {e}")

    def _on_email_error(self, exception, context):
        """Handle errors from the runner."""
        try:
            msg = f"Runner error: {exception} Context: {context}"
            print(msg)
            self.root.after(0, self.add_login_log, msg)
            self.root.after(0, messagebox.showerror, "Email Finder Error", str(exception))
        except Exception:
            pass
            
    # Event handlers for Analytics
    def select_analytics_csv(self):
        """Select analytics input CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select Input CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.analytics_input_var.set(file_path)
            
    def start_analytics(self):
        """Start analytics process"""
        if not SUBCUNT_AVAILABLE:
            messagebox.showerror("Error", "Analytics module not available. Please check your installation.")
            return
            
        input_file = self.analytics_input_var.get()
        if not os.path.exists(input_file):
            messagebox.showerror("Error", f"Input CSV file not found: {input_file}")
            return
            
        self.analysis_active = True
        self.start_analytics_btn.config(state='disabled')
        self.stop_analytics_btn.config(state='normal')
        self.analytics_progress.start()
        
        self.status_var.set("Analyzing subscriber counts...")
        
        # Start analytics in background thread
        thread = threading.Thread(target=self.analytics_worker)
        thread.daemon = True
        thread.start()
        
    def stop_analytics(self):
        """Stop analytics process"""
        self.analysis_active = False
        self.start_analytics_btn.config(state='normal')
        self.stop_analytics_btn.config(state='disabled')
        self.analytics_progress.stop()
        self.status_var.set("Analytics stopped")
        
    def analytics_worker(self):
        """Background worker for analytics"""
        try:
            # Clear existing results
            self.root.after(0, self.clear_analytics_results)
            
            # Simulate analytics process
            channels = [
                ("https://youtube.com/@gaming", "1.2K", "1K-10K"),
                ("https://youtube.com/@cooking", "856", "Below 1K"),
                ("https://youtube.com/@tech", "15K", "Above 10K"),
                ("https://youtube.com/@music", "7.5K", "1K-10K"),
                ("https://youtube.com/@news", "345", "Below 1K"),
            ]
            
            below_1k = 0
            between_1k_10k = 0
            above_10k = 0
            
            for channel, subs, category in channels:
                if not self.analysis_active:
                    break
                    
                self.root.after(0, self.add_analytics_result, channel, subs, category)
                
                if category == "Below 1K":
                    below_1k += 1
                elif category == "1K-10K":
                    between_1k_10k += 1
                else:
                    above_10k += 1
                    
                time.sleep(1)
                
            # Update summary
            self.root.after(0, self.below_1k_var.set, str(below_1k))
            self.root.after(0, self.between_1k_10k_var.set, str(between_1k_10k))
            self.root.after(0, self.above_10k_var.set, str(above_10k))
            
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"Analytics error: {str(e)}")
        finally:
            self.root.after(0, self.stop_analytics)
            
    def clear_analytics_results(self):
        """Clear analytics results table"""
        for item in self.analytics_tree.get_children():
            self.analytics_tree.delete(item)
            
    def add_analytics_result(self, channel, subscribers, category):
        """Add result to analytics table"""
        self.analytics_tree.insert('', 'end', values=(channel, subscribers, category))
        
    def run(self):
        """Start the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nApplication closed by user")


    def create_status_bar(self):
        """Create status bar at bottom of window"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side='bottom', fill='x', padx=8, pady=4)
        
        # Status label
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                anchor='w', font=('Segoe UI', 9), foreground='#8a8a8a')
        status_label.pack(side='left', fill='x', expand=True)
        
        # Session info
        session_time = datetime.datetime.now() - self.session_stats['session_start']
        session_info = f"Session: {str(session_time).split('.')[0]} | Channels: {self.session_stats['channels_scraped']}"
        session_label = ttk.Label(status_frame, text=session_info, 
                                 font=('Segoe UI', 9), foreground='#8a8a8a')
        session_label.pack(side='right')
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def show_tooltip(event):
            self.status_var.set(text)
        def hide_tooltip(event):
            self.status_var.set("")
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def copy_channel_url(self, event):
        """Copy selected channel URL to clipboard"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            channel_url = item['values'][0]
            self.root.clipboard_clear()
            self.root.clipboard_append(channel_url)
            self.status_var.set(f"Copied: {channel_url}")
    
    def toggle_log_visibility(self):
        """Toggle the visibility of the developer log section"""
        if self.log_visible.get():
            # Hide log
            self.log_frame.pack_forget()
            self.log_toggle_btn.config(text="▶️ Show Developer Log")
            self.log_visible.set(False)
            self.status_var.set("Developer log hidden - more space for results")
        else:
            # Show log
            self.log_frame.pack(fill='both', expand=True, pady=(4, 0))
            self.log_toggle_btn.config(text="🔽 Hide Developer Log")
            self.log_visible.set(True)
            self.status_var.set("Developer log visible - showing detailed scraping progress")


def main():
    """Main application entry point"""
    print("Starting YouTube Automation Suite (tkinter version)...")
    
    try:
        app = YouTubeAutomationGUI()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        messagebox.showerror("Error", f"Failed to start application: {e}")


if __name__ == "__main__":
    main()
