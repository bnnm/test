import logging, os


VALID_EXTENSIONS = ['.wem', ".wav", ".lwav", ".xma", ".ogg", ".logg"]

# !tags.m3u helper

#******************************************************************************

class Tags(object):
    def __init__(self, banks, locator=None, names=None):
        self._banks = banks
        self._names = names
        self._locator = locator

        self.make_event = False
        self.make_wem = False
        self.shortevent = False
        self.add = False
        self.limit = None

        self._tag_names = {}

    #--------------------------------------------------------------------------

    def add_tag_names(self, shortname, longname):
        self._tag_names[shortname] = longname

    def set_locator(self, locator):
        self._locator = locator

    def set_make_event(self, flag):
        self.make_event = flag
        self.shortevent = flag

    def set_make_wem(self, flag):
        self.make_wem = flag

    def set_add(self, flag):
        self.add = flag

    def set_limit(self, value):
        self.limit = value

    def get_limit(self):
        return self._limit

    #--------------------------------------------------------------------------
  

    def make(self):
        try:
            self._write_event()
            self._write_wem()

        except Exception: # as e
            logging.warn("tags: PROCESS ERROR! (report)")
            logging.exception("")
            raise
        return


    def _write_event(self):
        if not self.make_event:
            return
        if not self._tag_names: #no names registered
            return

        logging.info("tags: start making tags for events")

        basepath = self.__get_basepath() #TODO

        tags = self._tag_names
        files = list(tags.keys())
        files.sort()
        if not files:
            return

        outdir = self._locator.get_txtp_rootpath()
        if outdir:
            outdir = os.path.join(basepath, outdir)
            os.makedirs(outdir, exist_ok=True)

        outname = os.path.join(outdir, "!tags.m3u")
        
        mode = 'w'
        if self.add and os.path.exists(outname):
            mode = 'a'

        with open(outname, mode, newline="\r\n") as outfile:
            if not mode == 'a':
                outfile.write("## @ALBUM    \n")
                outfile.write("## $AUTOALBUM\n")
                outfile.write("## $AUTOTRACK\n")
                outfile.write("# AUTOGENERATED BY WWISER\n")
                outfile.write("\n")

            for file in files:
                longname = tags[file]

                outfile.write("# %%TITLE    %s\n" %(longname))
                outfile.write('%s\n' % (file))

        return


    def _write_wem(self):
        if not self.make_wem:
            return
        if not self._names:
            return

        logging.info("tags: start making tags for wem")

        # try in current dir
        root_path = self._locator.get_root_fullpath()

        done = 0
        for root, _, files in os.walk(root_path):
            items = []

            has_info = False
            for file in files:
                basename = os.path.basename(file)
                name, ext = os.path.splitext(basename)

                if ext not in VALID_EXTENSIONS:
                    continue
                if not name.isnumeric():
                    continue

                # only make tags.m3u if at least one when some of the items have info
                # (that is, if 10 wems have info and 1 doesn't, should make tags for all wems)
                id = int(name)
                row = self._names.get_namerow(id)
                if row and (row.guidname or row.path or row.objpath):
                    has_info = True
                items.append((file, row))

            if not items or not has_info:
                continue

            items.sort()
            self._write_wem_tags(root, items)
            done += 1

        if not done:
            logging.info("tags: couldn't generate tags (no .wem found or no .wem names in companion files)")
            return

    def _write_wem_tags(self, basepath, items):
        outname = os.path.join(basepath, "!tags.m3u")

        mode = 'w'
        if self.add and os.path.exists(outname):
            mode = 'a'

        with open(outname, mode, newline="\r\n") as outfile:
            if not mode == 'a':
                outfile.write("## @ALBUM    \n")
                outfile.write("## $AUTOALBUM\n")
                outfile.write("## $AUTOTRACK\n")
                outfile.write("# AUTOGENERATED BY WWISER\n")
                outfile.write("\n")

            for file, row in items:
                if row:
                    if row.guidname:
                        outfile.write("# %%TITLE    %s\n" %(row.guidname))
                    if row.path:
                        outfile.write("# %%PATH     %s\n" %(row.path))
                    if row.objpath:
                        outfile.write("# %%OBJPATH  %s\n" %(row.objpath))
                outfile.write('%s\n' % (file))

        logging.info("tags: wrote %s", outname)
        return

    def __get_basepath(self):
        # take first bank as base folder
        if self._banks:
            basepath = self._banks[0].get_root().get_path()
        else:
            basepath = os.getcwd() #self._txtpcache.basedir
        if not basepath:
            basepath = '.'

        return basepath