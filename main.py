import os
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from tkinter.scrolledtext import ScrolledText
import markdown
from tkinterweb import HtmlFrame
import re
from tkinter import ttk

class BamBam:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Bam Bam - It's NotePad with a Sidebar")
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        self.file_frame = tk.Frame(self.paned_window, width=200, bg='lightgrey')
        self.paned_window.add(self.file_frame, stretch="always")
        self.file_listbox = tk.Listbox(self.file_frame)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        self.load_files()
        self.create_button(self.file_frame, "Search (CTRL-F)", self.search_files)
        self.create_button(self.file_frame, "New (CTRL-N)", self.new_file)
        self.create_button(self.file_frame, "Open (CTRL-O)", self.open_file)
        self.create_button(self.file_frame, "Save (CTRL-S)", self.save_file)
        self.create_button(self.file_frame, "Delete (Delete)", self.delete_file)
        self.editor_frame = tk.Frame(self.paned_window, width=300)
        self.paned_window.add(self.editor_frame, stretch="always")
        self.editor = ScrolledText(self.editor_frame, wrap=tk.WORD)
        self.editor.pack(fill=tk.BOTH, expand=True)
        self.editor.bind("<<Modified>>", self.update_preview)
        self.editor.bind("<<Modified>>", self.on_modified)
        self.preview_frame = tk.Frame(self.paned_window, width=400, bg='white')
        self.paned_window.add(self.preview_frame, stretch="always")
        self.preview = HtmlFrame(self.preview_frame, horizontal_scrollbar="auto")
        self.preview.pack(fill=tk.BOTH, expand=True)
        self.paned_window.paneconfigure(self.file_frame, minsize=200)
        self.paned_window.paneconfigure(self.editor_frame, minsize=500)
        self.paned_window.paneconfigure(self.preview_frame, minsize=800)
        self.root.bind('<Control-n>', lambda event: self.new_file())
        self.root.bind('<Control-o>', lambda event: self.open_file())
        self.root.bind('<Control-s>', lambda event: self.save_file())
        self.root.bind('<Delete>', lambda event: self.delete_file())
        self.root.bind('<Control-f>', lambda event: self.search_files())
        self.current_file = None
        self.file_modified = False

    def create_button(self, parent, text, command):
        button = tk.Button(parent, text=text, command=command)
        button.pack(fill=tk.X)

    def load_files(self):
        self.file_listbox.delete(0, tk.END)
        notes_dir = 'notes'
        files_with_timestamps = []
        for root, dirs, files in os.walk(notes_dir):
            if 'assets' in dirs:
                dirs.remove('assets')
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    timestamp = os.path.getmtime(file_path)
                    files_with_timestamps.append((file_path, timestamp))

        files_with_timestamps.sort(key=lambda x: x[1], reverse=True)
        for file_path, _ in files_with_timestamps:
            self.file_listbox.insert(tk.END, file_path)
            
    def new_file(self):
        self.editor.delete('1.0', tk.END)
        self.root.title("New File - Bam Bam")
        self.current_file = None 
        self.file_modified = False

    def open_file(self):
        file_path = self.file_dialog(filedialog.askopenfilename, "Open File")
        if file_path:
            self._open_file(file_path)
    
    def _open_file(self, file_path):
        content = self.read_file(file_path)
        self.editor.delete('1.0', tk.END)
        self.editor.insert(tk.END, content)
        self.root.title(f"{os.path.basename(file_path)} - Bam Bam")
        self.current_file = file_path
        self.file_modified = False

    def save_file(self):
        if self.current_file:
            file_path = self.current_file
        else:
            file_path = self.file_dialog(filedialog.asksaveasfilename, "Save File")
            if not file_path:
                return
        content = self.editor.get('1.0', tk.END)
        self.write_file(file_path, content)
        self.root.title(f"{os.path.basename(file_path)} - Bam Bam")
        self.current_file = file_path
        self.load_files()

    def delete_file(self):
        selected_file = self.file_listbox.get(tk.ACTIVE)
        if selected_file:
            confirm = messagebox.askyesno("Delete File", f"Are you sure you want to delete {os.path.basename(selected_file)}?")
            if confirm:
                os.remove(selected_file)
                self.load_files()

    def on_file_select(self, event):
        selected_index = self.file_listbox.curselection()
        if selected_index:
            file_path = self.file_listbox.get(selected_index)
            self._open_file(file_path)
    
    def open_file_from_link(self, url):
        file_path = url.replace('file://', '')
        if os.path.exists(file_path):
            self._open_file(file_path)
        else:
            messagebox.showerror("Error", f"File not found: {file_path}")
    
    def on_modified(self, event=None):
        if not self.file_modified:
            self.file_modified = True
            if self.current_file:
                self.root.title(os.path.basename(self.current_file) + "* - Bam Bam")
            else:
                self.root.title("Untitled* - Bam Bam")
        self.update_preview()
        self.editor.edit_modified(False)

    def update_preview(self, event=None):
        content = self.editor.get('1.0', tk.END)
        html_content = markdown.markdown(content)
        notes_dir = os.path.abspath('notes')
        html_content = html_content.replace('src="assets/', f'src="{notes_dir}/assets/')
        html_content = html_content.replace('<img ', '<img style="width:500px; height:500px;" ')
        self.preview.load_html(html_content)
        self.editor.edit_modified(False)
    
    def search_files(self):
        search_term = simpledialog.askstring("Search Files", "Enter search term:")
        if search_term:
            matching_files = []
            notes_dir = 'notes'
            for root, dirs, files in os.walk(notes_dir):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r') as f:
                            content = f.read()
                            matches = re.finditer(search_term, content, re.IGNORECASE)
                            for match in matches:
                                start = max(match.start() - 20, 0)
                                end = min(match.end() + 20, len(content))
                                snippet = content[start:end].replace('\n', ' ')
                                matching_files.append((file_path, snippet))
            if matching_files:
                self.show_search_results(matching_files, search_term)
            else:
                messagebox.showinfo("Search Results", "No matching files found.")

    def show_search_results(self, matching_files, search_term):
        result_window = tk.Toplevel(self.root)
        result_window.title("Search Results")
        result_listbox = tk.Listbox(result_window)
        result_listbox.pack(fill=tk.BOTH, expand=True)
        for file in matching_files:
            result_listbox.insert(tk.END, file)
        result_listbox.bind("<<ListboxSelect>>", lambda event: self.on_search_result_select(event, result_listbox))

    def on_search_result_select(self, event, listbox):
        selected_index = listbox.curselection()
        if selected_index:
            file_path = listbox.get(selected_index)[0]
            self._open_file(os.path.join(file_path))

    def file_dialog(self, dialog_func, title):
        return dialog_func(defaultextension=".md", filetypes=[("Markdown files", "*.md"), ("All files", "*.*")], title=title)

    def read_file(self, file_path):
        with open(file_path, 'r') as file:
            return file.read()

    def write_file(self, file_path, content):
        with open(file_path, 'w') as file:
            file.write(content)

if __name__ == "__main__":
    root = tk.Tk()
    app = BamBam(root)
    root.mainloop()
