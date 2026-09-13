import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import warnings
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

class SurfaceExplorerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Surface Explorer — Multi-Variable Function Visualizer")
        self.root.geometry("1500x950")
        self.root.configure(bg='#1a1a2e')
        
        # Default function
        self.default_function = "sqrt(x1**2 + x2**2 + x3**2 + x4**2)"
        self.x_val = 1.0
        self.y_val = 1.0
        self.n_vars = 4
        
        # Store values for all variables (index 0 = x1, 1 = x2, etc.)
        self.var_values = [1.0, 1.0]  # Will be extended as needed
        
        self._build_ui()
        self._update_function_label()
        self.root.after(50, self._update_surface)
    
    def _update_function_label(self):
        try:
            n = int(self.n_vars_entry.get())
            if n < 1:
                n = 1
                self.n_vars_entry.delete(0, tk.END)
                self.n_vars_entry.insert(0, "1")
            self.n_vars = n
            if n == 1:
                label = "Function f(x1) = "
            elif n == 2:
                label = "Function f(x1, x2) = "
            elif n == 3:
                label = "Function f(x1, x2, x3) = "
            else:
                label = "Function f(x1, ..., xn) = "
            self.func_label.config(text=label)
        except ValueError:
            pass
    
    def _build_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ===== TOP BAR: Function Input =====
        top_frame = tk.Frame(main_frame, bg='#16213e', padx=10, pady=8)
        top_frame.pack(fill='x', pady=(0, 8))
        
        tk.Label(top_frame, text="Num variables:", bg='#16213e', fg='#e0e0e0', font=('Segoe UI', 11, 'bold')).pack(side='left')
        self.n_vars_entry = tk.Entry(top_frame, width=4, font=('Consolas', 11), bg='#0f3460', fg='#00ff88', insertbackground='#00ff88')
        self.n_vars_entry.insert(0, "4")
        self.n_vars_entry.pack(side='left', padx=5)
        self.n_vars_entry.bind('<Return>', lambda e: self._on_n_vars_change())
        self.n_vars_entry.bind('<FocusOut>', lambda e: self._on_n_vars_change())
        
        self.func_label = tk.Label(top_frame, text="Function f(x1, x2, x3, x4) = ", 
                 bg='#16213e', fg='#e0e0e0', font=('Segoe UI', 12, 'bold'))
        self.func_label.pack(side='left', padx=(10, 0))
        
        self.func_entry = tk.Entry(top_frame, width=50, font=('Consolas', 11), bg='#0f3460', fg='#00ff88', insertbackground='#00ff88')
        self.func_entry.insert(0, self.default_function)
        self.func_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        update_btn = tk.Button(top_frame, text="Update", command=self._update_surface,
                               bg='#e94560', fg='white', font=('Segoe UI', 10, 'bold'),
                               relief='flat', cursor='hand2', padx=15)
        update_btn.pack(side='left', padx=5)
        
        # ===== MAIN TWO PANELS =====
        panels_frame = tk.Frame(main_frame, bg='#1a1a2e')
        panels_frame.pack(fill='both', expand=True)
        
        # --- LEFT PANEL: Scrollable XY Planes ---
        self.left_frame = tk.Frame(panels_frame, bg='#1a1a2e')
        self.left_frame.pack(side='left', fill='both', expand=True, padx=(0, 6))
        
        # Create a canvas and inner scrollable frame
        self.left_canvas = tk.Canvas(self.left_frame, bg='#1a1a2e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.left_frame, orient='vertical', command=self.left_canvas.yview)
        self.scrollable_left = tk.Frame(self.left_canvas, bg='#1a1a2e')
        
        self.scrollable_left.bind(
            "<Configure>",
            lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))
        )
        
        self.left_canvas.create_window((0, 0), window=self.scrollable_left, anchor="nw")
        self.left_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.left_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind mouse wheel to scroll
        self.left_canvas.bind_all("<MouseWheel>", lambda e: self.left_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # --- Build XY plane for x1, x2 ---
        self.xy_plane_12 = self._build_xy_plane(self.scrollable_left, 1, 2, 0)
        # Store convenient references
        self.ax_xy = self.xy_plane_12['ax']
        self.canvas_xy = self.xy_plane_12['canvas']
        self.scatter_marker = self.xy_plane_12['scatter']
        
        # --- Build additional XY planes for remaining variable pairs ---
        self.additional_xy_planes = []  # Store references to clean up later
        self._build_additional_xy_planes(3)
        
        # --- RIGHT PANEL: Final Variable Plot ---
        self.right_frame = tk.LabelFrame(panels_frame, text="  Final Variable Plot  ",
                                         bg='#16213e', fg='#e0e0e0', font=('Segoe UI', 11, 'bold'),
                                         padx=8, pady=8)
        self.right_frame.pack(side='left', fill='both', expand=True, padx=(6, 0))
        
        # Bounds entry row
        bounds_frame = tk.Frame(self.right_frame, bg='#16213e')
        bounds_frame.pack(fill='x', pady=(0, 4))
        
        tk.Label(bounds_frame, text="z range:", bg='#16213e', fg='#aaa', font=('Segoe UI', 9)).pack(side='left')
        self.z_min_entry = tk.Entry(bounds_frame, width=7, font=('Consolas', 9), bg='#0f3460', fg='#00ff88', insertbackground='#00ff88')
        self.z_min_entry.insert(0, "-3")
        self.z_min_entry.pack(side='left', padx=2)
        tk.Label(bounds_frame, text="to", bg='#16213e', fg='#aaa', font=('Segoe UI', 9)).pack(side='left')
        self.z_max_entry = tk.Entry(bounds_frame, width=7, font=('Consolas', 9), bg='#0f3460', fg='#00ff88', insertbackground='#00ff88')
        self.z_max_entry.insert(0, "3")
        self.z_max_entry.pack(side='left', padx=2)
        
        tk.Label(bounds_frame, text="w range:", bg='#16213e', fg='#aaa', font=('Segoe UI', 9)).pack(side='left', padx=(8, 0))
        self.w_min_entry = tk.Entry(bounds_frame, width=7, font=('Consolas', 9), bg='#0f3460', fg='#00ff88', insertbackground='#00ff88')
        self.w_min_entry.insert(0, "-3")
        self.w_min_entry.pack(side='left', padx=2)
        tk.Label(bounds_frame, text="to", bg='#16213e', fg='#aaa', font=('Segoe UI', 9)).pack(side='left')
        self.w_max_entry = tk.Entry(bounds_frame, width=7, font=('Consolas', 9), bg='#0f3460', fg='#00ff88', insertbackground='#00ff88')
        self.w_max_entry.insert(0, "3")
        self.w_max_entry.pack(side='left', padx=2)
        
        update_bounds_btn = tk.Button(bounds_frame, text="Apply", command=self._update_surface,
                                       bg='#0f3460', fg='#00ff88', font=('Segoe UI', 9, 'bold'),
                                       relief='flat', cursor='hand2')
        update_bounds_btn.pack(side='left', padx=(8, 0))
        
        # Single plot canvas
        self.fig_plot = Figure(figsize=(5, 4.5), dpi=100, facecolor='#1a1a2e')
        self.canvas_plot = FigureCanvasTkAgg(self.fig_plot, master=self.right_frame)
        self.canvas_plot.draw()
        self.canvas_plot.get_tk_widget().pack(fill='both', expand=True)
    
    def _on_n_vars_change(self):
        """Called when the number of variables changes."""
        try:
            n = int(self.n_vars_entry.get())
            if n < 1:
                n = 1
                self.n_vars_entry.delete(0, tk.END)
                self.n_vars_entry.insert(0, "1")
            self.n_vars = n
            
            # Show/hide left panel based on n
            if n <= 2:
                self.left_frame.pack_forget()
                self.right_frame.pack(side='left', fill='both', expand=True)
            else:
                self.right_frame.pack_forget()
                self.left_frame.pack(side='left', fill='both', expand=True, padx=(0, 6))
                self.right_frame.pack(side='left', fill='both', expand=True, padx=(6, 0))
            
            # Clear old additional planes
            for plane in self.additional_xy_planes:
                plane['frame'].destroy()
            self.additional_xy_planes.clear()
            
            # Rebuild additional planes only if n >= 3
            if n >= 3:
                self._build_additional_xy_planes(3)
            
            # Update surface
            self._update_surface()
        except ValueError:
            pass
    
    def _build_xy_plane(self, parent, var_i, var_j, row_idx):
        """Build a 2D plot panel for picking two variables. Returns a dict with references."""
        frame = tk.LabelFrame(parent, 
                              text=f"  Pick (x{var_i}, x{var_j})  ",
                              bg='#16213e', fg='#e0e0e0', font=('Segoe UI', 10, 'bold'),
                              padx=6, pady=6)
        frame.pack(fill='x', pady=(4, 4))
        
        # Get initial values
        val_i = self.var_values[var_i - 1] if var_i <= len(self.var_values) else 1.0
        val_j = self.var_values[var_j - 1] if var_j <= len(self.var_values) else 1.0
        
        # Coordinate entry row
        coord_frame = tk.Frame(frame, bg='#16213e')
        coord_frame.pack(fill='x', pady=(0, 4))
        
        tk.Label(coord_frame, text=f"x{var_i} =", bg='#16213e', fg='#aaa', font=('Segoe UI', 9)).pack(side='left')
        entry_i = tk.Entry(coord_frame, width=8, font=('Consolas', 9), bg='#0f3460', fg='#00ff88', insertbackground='#00ff88')
        entry_i.insert(0, f"{val_i:.2f}")
        entry_i.pack(side='left', padx=2)
        
        tk.Label(coord_frame, text=f"x{var_j} =", bg='#16213e', fg='#aaa', font=('Segoe UI', 9)).pack(side='left', padx=(6, 0))
        entry_j = tk.Entry(coord_frame, width=8, font=('Consolas', 9), bg='#0f3460', fg='#00ff88', insertbackground='#00ff88')
        entry_j.insert(0, f"{val_j:.2f}")
        entry_j.pack(side='left', padx=2)
        
        set_btn = tk.Button(coord_frame, text="Set", 
                            command=lambda vi=var_i, vj=var_j, ei=entry_i, ej=entry_j: self._update_from_xy_entries(vi, vj, ei, ej),
                            bg='#0f3460', fg='#00ff88', font=('Segoe UI', 8, 'bold'),
                            relief='flat', cursor='hand2')
        set_btn.pack(side='left', padx=4)
        
        # XY plot canvas
        fig = Figure(figsize=(4, 3), dpi=100, facecolor='#1a1a2e')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0f3460')
        ax.grid(True, alpha=0.3, color='#ffffff')
        ax.set_xlabel(f"x{var_i}", color='#e0e0e0', fontsize=9)
        ax.set_ylabel(f"x{var_j}", color='#e0e0e0', fontsize=9)
        ax.set_title(f"Click to pick", color='#e0e0e0', fontsize=10)
        ax.tick_params(colors='#e0e0e0', labelsize=8)
        ax.set_xlim(-5, 5)
        ax.set_ylim(-5, 5)
        
        scatter = ax.scatter([], [], c='#e94560', s=150, marker='o', 
                             edgecolors='white', linewidths=1.5, zorder=5)
        ax.axhline(y=0, color='#ffffff', linewidth=0.5, alpha=0.5)
        ax.axvline(x=0, color='#ffffff', linewidth=0.5, alpha=0.5)
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Store reference
        plane_info = {
            'frame': frame, 'fig': fig, 'ax': ax, 'canvas': canvas, 
            'scatter': scatter, 'entry_i': entry_i, 'entry_j': entry_j,
            'var_i': var_i, 'var_j': var_j
        }
        
        # Bind click event
        def make_click_handler(pi):
            def handler(event):
                if event.inaxes != pi['ax']:
                    return
                xdata = float(event.xdata)
                ydata = float(event.ydata)
                
                # Update stored values
                if pi['var_i'] <= len(self.var_values):
                    self.var_values[pi['var_i'] - 1] = xdata
                if pi['var_j'] <= len(self.var_values):
                    self.var_values[pi['var_j'] - 1] = ydata
                
                pi['entry_i'].delete(0, tk.END)
                pi['entry_i'].insert(0, f"{xdata:.3f}")
                pi['entry_j'].delete(0, tk.END)
                pi['entry_j'].insert(0, f"{ydata:.3f}")
                
                self._update_surface()
            return handler
        
        canvas.mpl_connect('button_press_event', make_click_handler(plane_info))
        
        return plane_info
    
    def _build_additional_xy_planes(self, start_var):
        """Build additional XY planes for variable pairs beyond x1,x2."""
        n = self.n_vars
        # Determine which variables need pickers
        if n % 2 == 0:
            # Even n: right panel shows 3D surface of (x(n-1), xn), so pick x3...xn-2
            end_var = n - 2
        else:
            # Odd n: right panel shows line graph of xn, so pick x3...xn-1
            end_var = n - 1
        
        var = start_var
        while var <= end_var:
            var_j = var + 1
            if var_j > end_var:
                var_j = end_var
            plane = self._build_xy_plane(self.scrollable_left, var, var_j, 0)
            self.additional_xy_planes.append(plane)
            var = var_j + 1
    
    def _update_from_xy_entries(self, var_i, var_j, entry_i, entry_j):
        """Update values from entry boxes for a variable pair."""
        try:
            val_i = float(entry_i.get())
            val_j = float(entry_j.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers.")
            return
        
        # Update stored values
        if var_i <= len(self.var_values):
            self.var_values[var_i - 1] = val_i
        if var_j <= len(self.var_values):
            self.var_values[var_j - 1] = val_j
        
        self._update_surface()
    
    def _update_surface(self):
        # Get number of variables
        try:
            n = int(self.n_vars_entry.get())
            if n < 1:
                n = 1
                self.n_vars_entry.delete(0, tk.END)
                self.n_vars_entry.insert(0, "1")
            self.n_vars = n
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number of variables.")
            return
        
        func_str = self.func_entry.get().strip()
        
        # Ensure var_values has enough entries
        while len(self.var_values) < n:
            self.var_values.append(1.0)
        
        # Build the evaluation function
        try:
            eval_func = self._build_eval_func(func_str, n)
            
            # Quick sanity test with sample values
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                test_val = eval_func(*self.var_values[:n])
            if not np.isfinite(test_val):
                raise ValueError(f"Function returned non-finite value for test point")
            
        except Exception as e:
            messagebox.showerror("Function Error", f"Could not evaluate function:\n\n{func_str}\n\nError: {e}")
            return
        
        # Read bounds from entry fields
        try:
            z_min = float(self.z_min_entry.get())
            z_max = float(self.z_max_entry.get())
            w_min = float(self.w_min_entry.get())
            w_max = float(self.w_max_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for z and w ranges.")
            return
        
        # For n <= 2, skip XY panel updates (left panel is hidden)
        if n >= 3:
            # Update first XY panel (x1, x2)
            self.ax_xy.clear()
            self.ax_xy.set_facecolor('#0f3460')
            self.ax_xy.grid(True, alpha=0.3, color='#ffffff')
            self.ax_xy.set_xlabel("x1", color='#e0e0e0', fontsize=10)
            self.ax_xy.set_ylabel("x2", color='#e0e0e0', fontsize=10)
            self.ax_xy.set_title(f"Current point: (x1={self.var_values[0]:.2f}, x2={self.var_values[1]:.2f})", 
                                 color='#e0e0e0', fontsize=11)
            self.ax_xy.tick_params(colors='#e0e0e0', labelsize=9)
            
            # Auto-scale: origin stays centered, axes grow to show the point
            dist = np.sqrt(self.var_values[0]**2 + self.var_values[1]**2)
            half_range = 1.0 if dist == 0 else dist * 1.2
            self.ax_xy.set_xlim(-half_range, half_range)
            self.ax_xy.set_ylim(-half_range, half_range)
            self.ax_xy.set_aspect('equal')
            
            self.ax_xy.axhline(y=0, color='#ffffff', linewidth=0.5, alpha=0.5)
            self.ax_xy.axvline(x=0, color='#ffffff', linewidth=0.5, alpha=0.5)
            self.scatter_marker = self.ax_xy.scatter(self.var_values[0], self.var_values[1], c='#e94560', s=200, 
                                                      marker='o', edgecolors='white', linewidths=2, zorder=5)
            self.canvas_xy.draw()
            
            # Update additional XY panels
            for plane in self.additional_xy_planes:
                vi = plane['var_i']
                vj = plane['var_j']
                ax = plane['ax']
                fig = plane['fig']
                scatter = plane['scatter']
                
                ax.clear()
                ax.set_facecolor('#0f3460')
                ax.grid(True, alpha=0.3, color='#ffffff')
                ax.set_xlabel(f"x{vi}", color='#e0e0e0', fontsize=9)
                ax.set_ylabel(f"x{vj}", color='#e0e0e0', fontsize=9)
                val_i = self.var_values[vi - 1] if vi <= len(self.var_values) else 1.0
                val_j = self.var_values[vj - 1] if vj <= len(self.var_values) else 1.0
                ax.set_title(f"Current: (x{vi}={val_i:.2f}, x{vj}={val_j:.2f})", color='#e0e0e0', fontsize=10)
                ax.tick_params(colors='#e0e0e0', labelsize=8)
                
                dist = np.sqrt(val_i**2 + val_j**2)
                half_range = 1.0 if dist == 0 else dist * 1.2
                ax.set_xlim(-half_range, half_range)
                ax.set_ylim(-half_range, half_range)
                ax.set_aspect('equal')
                
                ax.axhline(y=0, color='#ffffff', linewidth=0.5, alpha=0.5)
                ax.axvline(x=0, color='#ffffff', linewidth=0.5, alpha=0.5)
                scatter = ax.scatter(val_i, val_j, c='#e94560', s=150, marker='o', 
                                     edgecolors='white', linewidths=1.5, zorder=5)
                plane['scatter'] = scatter
                plane['canvas'].draw()
        
        # Clear old plot
        self.fig_plot.clear()
        
        # Build fixed values from var_values
        fixed_values = self.var_values[:n]
        
        # Handle special cases for n=1 and n=2
        if n == 1:
            # 2D line plot: x1 vs f(x1)
            x1_vals = np.linspace(z_min, z_max, 200)
            X_list = [x1_vals]
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                f_vals = eval_func(*X_list)
            f_vals = np.asarray(f_vals)
            f_vals = np.where(np.isfinite(f_vals), f_vals, np.nan)
            
            ax = self.fig_plot.add_subplot(111)
            ax.set_facecolor('#0f3460')
            ax.plot(x1_vals, f_vals, color='#00ff88', linewidth=2)
            ax.set_xlabel('x1', color='#e0e0e0', fontsize=10)
            ax.set_ylabel('f(x1)', color='#e0e0e0', fontsize=10)
            ax.set_title('Line graph: x1 vs f(x1)', color='#e0e0e0', fontsize=11)
            ax.tick_params(colors='#e0e0e0', labelsize=9)
            ax.axhline(y=0, color='#ffffff', linewidth=0.5, alpha=0.5)
            ax.axvline(x=0, color='#ffffff', linewidth=0.5, alpha=0.5)
        
        elif n == 2:
            # 3D surface plot: x1, x2 vs f(x1, x2)
            x1_vals = np.linspace(z_min, z_max, 50)
            x2_vals = np.linspace(w_min, w_max, 50)
            X1, X2 = np.meshgrid(x1_vals, x2_vals)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                V = eval_func(X1, X2)
            V = np.where(np.isfinite(V), V, np.nan)
            
            ax = self.fig_plot.add_subplot(111, projection='3d')
            ax.set_facecolor('#0f3460')
            ax.set_xlabel('x1', color='#e0e0e0', fontsize=10)
            ax.set_ylabel('x2', color='#e0e0e0', fontsize=10)
            ax.set_zlabel('f(x1, x2)', color='#e0e0e0', fontsize=10)
            ax.set_title('3D surface: f(x1, x2)', color='#e0e0e0', fontsize=11)
            ax.tick_params(colors='#e0e0e0', labelsize=9)
            surf = ax.plot_surface(X1, X2, V, cmap='viridis', edgecolor='none', alpha=0.9)
            self.fig_plot.colorbar(surf, ax=ax, shrink=0.5, aspect=10, pad=0.15)
            ax.view_init(elev=25, azim=-60)
        
        else:
            # n >= 3: The right panel shows the LAST variable: xn
            # For even n: 3D surface plot of f(fixed x1...xn-2, x(n-1), xn)
            # For odd n:  line graph of xn vs f(x1,...,xn) with x1...xn-1 all fixed
            is_even = (n % 2 == 0)
            
            if is_even:
                # 3D surface plot: x(n-1) and xn vary, x1...xn-2 fixed
                var_a = f'x{n-1}'
                var_b = f'xn'
                
                z_vals = np.linspace(z_min, z_max, 50)
                w_vals = np.linspace(w_min, w_max, 50)
                Z, W = np.meshgrid(z_vals, w_vals)
                
                X_list = []
                for i in range(n):
                    if i + 1 == n - 1:
                        X_list.append(Z)
                    elif i + 1 == n:
                        X_list.append(W)
                    else:
                        X_list.append(fixed_values[i])
                
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    V = eval_func(*X_list)
                V = np.broadcast_to(np.asarray(V), Z.shape)
                V = np.where(np.isfinite(V), V, np.nan)
                
                ax = self.fig_plot.add_subplot(111, projection='3d')
                ax.set_facecolor('#0f3460')
                ax.set_xlabel(var_a, color='#e0e0e0', fontsize=10)
                ax.set_ylabel(var_b, color='#e0e0e0', fontsize=10)
                ax.set_zlabel("f(...)", color='#e0e0e0', fontsize=10)
                ax.set_title(f"f(fixed, {var_a}, {var_b})", color='#e0e0e0', fontsize=11)
                ax.tick_params(colors='#e0e0e0', labelsize=9)
                surf = ax.plot_surface(Z, W, V, cmap='viridis', edgecolor='none', alpha=0.9)
                self.fig_plot.colorbar(surf, ax=ax, shrink=0.5, aspect=10, pad=0.15)
                ax.view_init(elev=25, azim=-60)
            else:
                # Line graph: xn varies, x1...xn-1 all fixed
                xn_vals = np.linspace(z_min, z_max, 200)
                
                X_list = []
                for i in range(n):
                    if i + 1 == n:  # last variable (xn) varies
                        X_list.append(xn_vals)
                    else:
                        # Broadcast scalar to same shape as xn_vals
                        X_list.append(np.broadcast_to(fixed_values[i], xn_vals.shape))
                
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    f_vals = eval_func(*X_list)
                f_vals = np.asarray(f_vals)
                f_vals = np.where(np.isfinite(f_vals), f_vals, np.nan)
                
                ax = self.fig_plot.add_subplot(111)
                ax.set_facecolor('#0f3460')
                ax.plot(xn_vals, f_vals, color='#00ff88', linewidth=2)
                ax.set_xlabel(f'xn', color='#e0e0e0', fontsize=10)
                ax.set_ylabel(f'f(x1,...,xn)', color='#e0e0e0', fontsize=10)
                ax.set_title(f'Line graph: xn vs f(fixed x1,...,xn-1, xn)', color='#e0e0e0', fontsize=11)
                ax.tick_params(colors='#e0e0e0', labelsize=9)
                ax.axhline(y=0, color='#ffffff', linewidth=0.5, alpha=0.5)
                ax.axvline(x=0, color='#ffffff', linewidth=0.5, alpha=0.5)
        
        self.fig_plot.tight_layout()
        self.canvas_plot.draw()

    def _build_eval_func(self, func_str, n):
        """Build an evaluation function for the given expression."""
        local_vars = {
            'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
            'exp': np.exp, 'log': np.log, 'log10': np.log10,
            'sqrt': np.sqrt, 'abs': abs, 'pi': np.pi, 'e': np.e,
            'sinh': np.sinh, 'cosh': np.cosh, 'tanh': np.tanh,
            'arcsin': np.arcsin, 'arccos': np.arccos, 'arctan': np.arctan,
            'pow': pow, 'log2': np.log2, 'ceil': np.ceil, 'floor': np.floor,
            'maximum': np.maximum, 'minimum': np.minimum
        }
        
        def eval_func(*args):
            for i, val in enumerate(args):
                local_vars[f'x{i+1}'] = val
            return eval(func_str, {"__builtins__": {}}, local_vars)
        
        return eval_func


def main():
    root = tk.Tk()
    app = SurfaceExplorerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
