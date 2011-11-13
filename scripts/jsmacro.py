#!/usr/bin/env python

from datetime import datetime
import getopt
import os
import re
import shutil
import sys

__author__ = "Erik Smartt"
__copyright__ = "Copyright 2010-2011, Erik Smartt"
__license__ = "MIT"
__version__ = "0.2.17"

__usage__ = """Normal usage:
    jsmacro.py -f [INPUT_FILE_NAME] > [OUTPUT_FILE]

    Options:
     --def [VAR]   Sets the supplied variable to True in the parser environment.
     --file [VAR]  Same as -f; Used to load the input file.
     --help        Prints this Help message.
     --savefail    Saves the expected output of a failed test case to disk.
     --test        Run the test suite.
     --version     Print the version number of jsmacro being used.
"""

__credits__ = [
    'aliclark <https://github.com/aliclark>',
    'Rodney Lopes Gomes <https://github.com/rlgomes>',
    'Elan Ruusamae <https://github.com/glensc>',
]

DEFINE_DEFAULT = '0'

class MacroEngine(object):
    """
    The MacroEngine is where the magic happens. It defines methods that are called
    to handle the macros found in a document.
    """
    def __init__(self):
        self.save_expected_failures = False

        self.re_else_pattern = '//[\@|#]else'

        # Compile the main patterns
        # Pattern change in 0.2.17 by aliclark. We're now a little more strict in blocking multi-line define statements,
        # and ensuring that whitespace separates the variable name (and value) from the 'define' text.
        self.re_define_macro = re.compile("([\\t ]*\/\/[\@|#]define[\\t ]+)(\w+)([\\t ]+(\w+))?", re.I)

        self.re_date_sub_macro = re.compile("[\@|#]\_\_date\_\_", re.I)
        self.re_time_sub_macro = re.compile("[\@|#]\_\_time\_\_", re.I)
        self.re_datetime_sub_macro = re.compile("[\@|#]\_\_datetime\_\_", re.I)

        self.re_stripline_macro = re.compile(".*\/\/[\@|#]strip.*", re.I)

        # A wrapped macro takes the following form:
        #
        # //@MACRO <ARGUMENTS>
        # ...some code
        # //@end
        self.re_wrapped_macro = re.compile("(\s*\/\/[\@|#])([a-z]+)\s+(\w*?\s)(.*?)(\s*\/\/[\@|#]end(if)?)", re.M|re.S)

        self.reset()

    def reset(self):
        self.env = {}

    def handle_define(self, key, value=DEFINE_DEFAULT):
        if key in self.env:
            return

        self.env[key] = eval(value)

    def handle_if(self, arg, text):
        """
        Returns the text to output based on the value of 'arg'.  E.g., if arg evaluates to false,
        expect to get an empty string back.

        @param    arg    String    Statement found after the 'if'. Currently expected to be a variable (i.e., key) in the env dictionary.
        @param    text   String    The text found between the macro statements
        """
        # To handle the '//@else' statement, we'll split text on the statement.
        parts = re.split(self.re_else_pattern, text)

        try:
            if self.env[arg]:
                return "\n{s}".format(s=parts[0])

            else:
                try:
                    return "{s}".format(s=parts[1])

                except IndexError:
                    return ''

        except KeyError:
            return "\n{s}".format(s=text)

    def handle_ifdef(self, arg, text):
        """
        @param    arg    String    Statement found after the 'ifdef'. Currently expected to be a variable (i.e., key) in the env dictionary.
        @param    text   String    The text found between the macro statements

        An ifdef is true if the variable 'arg' exists in the environment, regardless of whether
        it resolves to True or False.
        """
        parts = re.split(self.re_else_pattern, text)

        if arg in self.env:
            return "\n{s}".format(s=parts[0])

        else:
            try:
                return "{s}".format(s=parts[1])

            except IndexError:
                return ''

    def handle_ifndef(self, arg, text):
        """
        @param    arg    String    Statement found after the 'ifndef'. Currently expected to be a variable (i.e., key) in the env dictionary.
        @param    text   String    The text found between the macro statements

        An ifndef is true if the variable 'arg' does not exist in the environment.
        """
        parts = re.split(self.re_else_pattern, text)

        if arg in self.env:
            try:
                return "{s}".format(s=parts[1])

            except IndexError:
                return ''

        else:
            return "\n{s}".format(s=parts[0])

    def handle_macro(self, mo):
        method = mo.group(2)
        args = mo.group(3).strip()
        code = "\n{s}".format(s=mo.group(4))

        # This is a fun line.  We construct a method name using the string found in the regex, and call that method on self
        # with the arguments we have.  So, we can dynamically call methods... (and eventually, we'll support adding methods
        # at runtime :-)
        return getattr(self, "handle_{m}".format(m=method))(args, code)


    def parse(self, file_name):
        now = datetime.now()

        fp = open(file_name, 'r')
        text = fp.read()
        fp.close()

        # Replace supported __foo__ statements
        text = self.re_date_sub_macro.sub('{s}'.format(s=now.strftime("%b %d, %Y")),
            self.re_time_sub_macro.sub('{s}'.format(s=now.strftime("%I:%M%p")),
            self.re_datetime_sub_macro.sub('{s}'.format(s=now.strftime("%b %d, %Y %I:%M%p")), text)))

        # Parse for DEFINE statements
        for mo in self.re_define_macro.finditer(text):
            if mo:
                k = mo.group(2) # key
                v = mo.group(3) # value

                if v is None:
                    v = DEFINE_DEFAULT

                self.handle_define(k, v)

        # Delete the DEFINE statements
        text = self.re_define_macro.sub('', text)

        # Drop any lines containing a //@strip statement
        text = self.re_stripline_macro.sub('', text)

        # Do the magic...
        text = self.re_wrapped_macro.sub(self.handle_macro, text)

        return text

def scan_and_parse_dir(srcdir, destdir, parser):
    count = 0

    for root, dirs, files in os.walk(srcdir):
        for filename in files:
            dir = root[len(srcdir)+1:]

            if srcdir != root:
                dir = '{d}/'.format(d=dir)

            in_path = "{s}/{d}".format(s=srcdir, d=dir)
            out_path = "{s}/{d}".format(s=destdir, d=dir)

            in_file_path = "{p}/{f}".format(p=in_path, f=filename)
            out_file_path = "{p}/{f}".format(p=out_path, f=filename)

            if not(os.path.exists(out_path)):
                os.makedirs(out_path)

            # Copy non-js files to the output dir, even though we're not going to process them.  This is useful in
            # production environments where you might have other needed media files mixed-in with your JavaScript.
            if not(filename.endswith('.js')):
                shutil.copy(in_file_path, out_file_path)
                print("Copying {i} -> {o}".format(i=in_file_path, o=out_file_path))
                continue

            print(("Processing {i} -> {o}".format(i=in_file_path, o=out_file_path)))

            data = parser.parse(in_file_path)
            outfile = open(out_file_path,'w')
            outfile.write(data)
            outfile.close()

            count += 1

    print(("Processed {c} files.".format(c=count)))

# ---------------------------------
#          TEST
# ---------------------------------
def scan_for_test_files(dirname, parser):
    for root, dirs, files in os.walk(dirname):
        for in_filename in files:
            if in_filename.endswith('in.js'):
                in_file_path = "{d}/{f}".format(d=dirname, f=in_filename)
                out_file_path = "{d}/{f}out.js".format(d=dirname, f=in_filename[:-5])

                in_parsed = parser.parse(in_file_path)

                out_file = open(out_file_path, 'r')
                out_target_output = out_file.read()
                out_file.close()

                expect_failure = False
                if "always_fail" in in_file_path:
                    expect_failure = True

                if out_target_output == in_parsed:
                    if expect_failure:
                        print(("FAIL [{s}]".format(s=in_file_path)))
                    else:
                        print(("PASS [{s}]".format(s=in_file_path)))
                else:
                    if expect_failure:
                        print(("PASS [{s}]".format(s=in_file_path)))
                    else:
                        print(("FAIL [{s}]".format(s=in_file_path)))

                    if parser.save_expected_failures:
                        # Write the expected output file for local diffing
                        fout = open('{s}_expected'.format(s=out_file_path), 'w')
                        fout.write(in_parsed)
                        fout.close()

                    else:
                        print(("\n-- EXPECTED --\n{s}".format(s=out_target_output)))
                        print(("\n-- GOT --\n{s}".format(s=in_parsed)))

                parser.reset()


# --------------------------------------------------
#               MAIN
# --------------------------------------------------
if __name__ == "__main__":
    p = MacroEngine()

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "hf:s:d:",
                               ["help", "file=", "srcdir=","dstdir=", "test", "def=", "savefail", "version"])

    except getopt.GetoptError as err:
        print((str(err)))
        print(__usage__)

        sys.exit(2)


    # First handle commands that exit
    for o, a in opts:
        if o in ["-h", "--help"]:
            print(__usage__)

            sys.exit(0)

        if o in ["--version"]:
            print(__version__)

            sys.exit(0)


    # Next, handle commands that config
    for o, a in opts:
        if o in ["--def"]:
            p.handle_define(a)
            continue

        if o in ["--savefail"]:
            p.save_expected_failures = True
            continue

    srcdir = None
    dstdir = None

    # Now handle commands the execute based on the config
    for o, a in opts:
        if o in ["-s", "--srcdir"]:
            srcdir = a

        if o in ["-d", "--dstdir"]:
            dstdir = a

            if srcdir == None:
                raise Exception("you must set the srcdir when setting a dstdir.")

            else:
                scan_and_parse_dir(srcdir, dstdir, p)

            break

        if o in ["-f", "--file"]:
            print((p.parse(a)))

            break

        if o in ["--test"]:
            print("Testing...")
            scan_for_test_files("testfiles", p)
            print("Done.")

            break

    sys.exit(0)

