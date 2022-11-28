# This is a sample commands.py.  You can add your own commands here.
#
# Please refer to commands_full.py for all the default commands and a complete
# documentation.  Do NOT add them all here, or you may end up with defunct
# commands when upgrading ranger.

# A simple command for demonstration purposes follows.
# -----------------------------------------------------------------------------

from __future__ import (absolute_import, division, print_function)

# You can import any python module as needed.
import os

# You always need to import ranger.api.commands here to get the Command class:
from ranger.api.commands import Command


# Any class that is a subclass of "Command" will be integrated into ranger as a
# command.	Try typing ":my_edit<ENTER>" in ranger!
class my_edit(Command):
	# The so-called doc-string of the class will be visible in the built-in
	# help that is accessible by typing "?c" inside ranger.
	""":my_edit <filename>

	A sample command for demonstration purposes that opens a file in an editor.
	"""

	# The execute method is called when you run this command in ranger.
	def execute(self):
		# self.arg(1) is the first (space-separated) argument to the function.
		# This way you can write ":my_edit somefilename<ENTER>".
		if self.arg(1):
			# self.rest(1) contains self.arg(1) and everything that follows
			target_filename = self.rest(1)
		else:
			# self.fm is a ranger.core.filemanager.FileManager object and gives
			# you access to internals of ranger.
			# self.fm.thisfile is a ranger.container.file.File object and is a
			# reference to the currently selected file.
			target_filename = self.fm.thisfile.path

		# This is a generic function to print text in ranger.
		self.fm.notify("Let's edit the file " + target_filename + "!")

		# Using bad=True in fm.notify allows you to print error messages:
		if not os.path.exists(target_filename):
			self.fm.notify("The given file does not exist!", bad=True)
			return

		# This executes a function from ranger.core.actions, a module with a
		# variety of subroutines that can help you construct commands.
		# Check out the source, or run "pydoc ranger.core.actions" for a list.
		self.fm.edit_file(target_filename)

	# The tab method is called when you press tab, and should return a list of
	# suggestions that the user will tab through.
	# tabnum is 1 for <TAB> and -1 for <S-TAB> by default
	def tab(self, tabnum):
		# This is a generic tab-completion function that iterates through the
		# content of the current directory.
		return self._tab_directory_content()

# copyed fzf
class fzf_select(Command):
    """
    :fzf_select
    Find a file using fzf.
    With a prefix argument to select only directories.

    See: https://github.com/junegunn/fzf
    """

    def execute(self):
        import subprocess
        from ranger.ext.get_executables import get_executables

        if 'fzf' not in get_executables():
            self.fm.notify('Could not find fzf in the PATH.', bad=True)
            return

        fd = None
        if 'fdfind' in get_executables():
            fd = 'fdfind'
        elif 'fd' in get_executables():
            fd = 'fd'

        if fd is not None:
            hidden = ('--hidden' if self.fm.settings.show_hidden else '')
            exclude = "--no-ignore-vcs --exclude '.git' --exclude '*.py[co]' --exclude '__pycache__'"
            only_directories = ('--type directory' if self.quantifier else '')
            fzf_default_command = '{} --follow {} {} {} --color=always'.format(
                fd, hidden, exclude, only_directories
            )
        else:
            hidden = ('-false' if self.fm.settings.show_hidden else r"-path '*/\.*' -prune")
            exclude = r"\( -name '\.git' -o -iname '\.*py[co]' -o -fstype 'dev' -o -fstype 'proc' \) -prune"
            only_directories = ('-type d' if self.quantifier else '')
            fzf_default_command = 'find -L . -mindepth 1 {} -o {} -o {} -print | cut -b3-'.format(
                hidden, exclude, only_directories
            )

        env = os.environ.copy()
        env['FZF_DEFAULT_COMMAND'] = fzf_default_command
        env['FZF_DEFAULT_OPTS'] = '--height=40% --layout=reverse --ansi --preview="{}"'.format('''
            (
                batcat --color=always {} ||
                bat --color=always {} ||
                cat {} ||
                tree -ahpCL 3 -I '.git' -I '*.py[co]' -I '__pycache__' {}
            ) 2>/dev/null | head -n 100
        ''')

        fzf = self.fm.execute_command('fzf --no-multi', env=env,
                                      universal_newlines=True, stdout=subprocess.PIPE)
        stdout, _ = fzf.communicate()
        if fzf.returncode == 0:
            selected = os.path.abspath(stdout.strip())
            if os.path.isdir(selected):
                self.fm.cd(selected)
            else:
                self.fm.select_file(selected)
# copy mkcd
class mkcd(Command):
    """
    :mkcd <dirname>

    Creates a directory with the name <dirname> and enters it.
    """

    def execute(self):
        from os.path import join, expanduser, lexists
        from os import makedirs
        import re

        dirname = join(self.fm.thisdir.path, expanduser(self.rest(1)))
        if not lexists(dirname):
            makedirs(dirname)

            match = re.search('^/|^~[^/]*/', dirname)
            if match:
                self.fm.cd(match.group(0))
                dirname = dirname[match.end(0):]

            for m in re.finditer('[^/]+', dirname):
                s = m.group(0)
                if s == '..' or (s.startswith('.') and not self.fm.settings['show_hidden']):
                    self.fm.cd(s)
                else:
                    ## We force ranger to load content before calling `scout`.
                    self.fm.thisdir.load_content(schedule=False)
                    self.fm.execute_console('scout -ae ^{}$'.format(s))
        else:
            self.fm.notify("file/directory exists!", bad=True)

# 01 setImageAsBg
class setAsBg(Command):
	
	"""
	 target on a image and set it as backgrand picture
	"""

	def execute(self):
		target_filename = self.fm.thisfile.path
		self.fm.execute_command("feh --bg-center --no-fehbg " + target_filename)

# 02 paste2su
p2filepath=""
class p2yank(Command):
	def execute(self):
		global p2filepath
		p2filepath = self.fm.thisfile.path

class p2paste(Command):
	def execute(self):
		global p2filepath
		cmd = "sudo cp {} {}"
		ppath ="/".join(self.fm.thisfile.path.split("/")[:-1]) + "/" + p2filepath.split("/")[-1]
		self.fm.execute_command(cmd.format(p2filepath,ppath))

# 03 func for acm
"""
gdb need to check if c is -g , need to createfile to remind

gcc *.cpp -o .c
gcc *.cpp -o .c -g
gdb ./c
./.c

"""
class ffacreate_file(Command):
	def execute(self):
		if self.arg(1):
			target_filename = self.rest(1)
		else:
			return
		#cmd="touch {}" default open method is gvim(wtf?
		#cmd="vim {}" edit config file can solve the problem
		cmd="touch {}"
		self.fm.execute_command(cmd.format(target_filename))
		
class ffagcc(Command):
	def execute(self):
		filename = self.fm.thisfile.path.split("/")[-1]
		#cmd="clear"
		#self.fm.execute_command(cmd)
		cmd="g++ {} -o .c"
		self.fm.execute_command(cmd.format(filename))
		#cmd="echo -e \"ok \n\""
		#self.fm.execute_command(cmd)
		print("  ")
		cmd="read"
		self.fm.execute_command(cmd)
# 04 function for daily use
class ffdutypora(Command):
	def execute(self):
		filename = self.fm.thisfile.path.split("/")[-1]
		cmd="typora {}"
		self.fm.execute_command(cmd.format(filename))
#05 make e to vim everything
class ffduvim(Command):
	def execute(self):
		filename = self.fm.thisfile.path.split("/")[-1]
		cmd="vim {}"
		self.fm.execute_command(cmd.format(filename))
"""
# make console in ranger is not perfect , i find the ` :vert term ` in vim doc , that is what i wanted

class ffarun(Command):
	def execute(self):
		thepath ="/".join(self.fm.thisfile.path.split("/")[:-1])
		cmd=thepath+"/"+".c"
		self.fm.execute_command(cmd)
class ffagdb(Command):
	def execute(self):

class ffapy(Command):
	def execute(self):
"""
