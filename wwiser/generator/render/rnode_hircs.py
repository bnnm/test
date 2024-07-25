from ..txtp import hnode_misc
from .rnode_base import RN_CAkHircNode


#non-audio node, doesn't contribute to txtp
class RN_CAkNone(RN_CAkHircNode):
    
    def _render_base(self, bnode, txtp):
        #don't print node info in txtp
        return

    #def _render_txtp(self, txtp):
    #    return

#******************************************************************************

class RN_CAkEvent(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        # N play actions are layered (may set a delay)
        txtp.group_layer(bnode.ntids, config)
        for ntid in bnode.ntids:
            self._render_next(ntid, txtp)
        txtp.group_done(bnode.ntids)
        return

#******************************************************************************

class RN_CAkDialogueEvent(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        if bnode.ntid:
            # tree plays a single object with any state
            txtp.group_single(config)
            self._render_next(bnode.ntid, txtp)
            txtp.group_done()
            return

        if not bnode.tree:
            return 

        ws = self._ws
        if ws.gs_registrable():
            # find all possible gamesyncs paths (won't generate txtp)
            for path, ntid in bnode.tree.paths:
                unreachable = ws.gspaths.adds(path)
                if not unreachable:
                    self._render_next(ntid, txtp)
                ws.gspaths.done()
            ws.gspaths.sort()
            return

        # find if current gamesync combo matches one of the paths
        npath_combo = bnode.tree.get_npath(ws.gsparams)
        if npath_combo:
            npath, ntid = npath_combo
            txtp.info.gamesyncs(npath)

            txtp.group_single(config)
            self._render_next(ntid, txtp)
            txtp.group_done()
        return

#******************************************************************************

class RN_CAkAction(RN_CAkHircNode):
    #not used, just a parent
    pass

#******************************************************************************

class RN_CAkActionPlayAndContinue(RN_CAkAction):
    pass

#******************************************************************************

class RN_CAkActionTrigger(RN_CAkAction):

    def _render_txtp(self, bnode, txtp):
        # Event w/ ActionTrigger posts a "trigger". If music object currently playing
        # has a defined CAkStinger (that points to musicsegment) of that "trigger",
        # the musicsegment will play on top.
        # 
        # One trigger may call stingers from any song (1 trigger > N stingers),
        # and games may post triggers via API instead of play_trigger events,
        # so trigger/stinger generation must be handled like paths during music's
        # render_txtp, and this shouldn't try to make anything.
        return

#******************************************************************************

class RN_CAkActionPlay(RN_CAkAction):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        txtp.group_single(config)
        self._render_next(bnode.ntid, txtp, nbankid=bnode.nbankid)
        txtp.group_done()
        return

#******************************************************************************

class RN_CAkActionPlayEvent(RN_CAkAction):
    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        txtp.group_single(config)
        self._render_next_event(bnode.ntid, txtp)
        txtp.group_done()
        return

#******************************************************************************

class RN_CAkSwitchCntr(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        gtype = bnode.gtype
        gname = bnode.ngname.value()

        ws = self._ws
        if ws.gs_registrable():
            # find all possible gamesyncs paths (won't generate txtp)
            for ntids, ngvalue in bnode.gvalue_ntids.values(): #order doesn't matter
                gvalue = ngvalue.value()
                unreachable = ws.gspaths.add(gtype, gname, ngvalue.value())
                if not unreachable:
                    for ntid in ntids:
                        self._render_next(ntid, txtp)
                ws.gspaths.done()
            ws.gspaths.sort(True)
            return

        #get current gamesync
        gvalue = ws.gsparams.current(gtype, gname)
        if gvalue is None:
            return
        if not gvalue in bnode.gvalue_ntids: #exact match (no * like MusicSwitches)
            return
        ntids, ngvalue = bnode.gvalue_ntids[gvalue]


        txtp.info.gamesync(gtype, bnode.ngname, ngvalue)
        txtp.group_layer(ntids, config)
        for ntid in ntids: #multi IDs are possible but rare (KOF13)
            self._render_next(ntid, txtp)
        txtp.group_done()
        return

#******************************************************************************

class RN_CAkRanSeqCntr(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        if   bnode.mode == 0 and bnode.continuous: #random + continuous (plays all objects randomly, on loop/next call restarts)
            txtp.group_random_continuous(bnode.ntids, config)

        elif bnode.mode == 0: #random + step (plays one object at random, on next call plays another object / cannot loop)
            txtp.group_random_step(bnode.ntids, config)

        elif bnode.mode == 1 and bnode.continuous: #sequence + continuous (plays all objects in sequence, on loop/next call restarts)
            txtp.group_sequence_continuous(bnode.ntids, config)

        elif bnode.mode == 1: #sequence + step (plays one object from first, on next call plays next object / cannot loop)
            txtp.group_sequence_step(bnode.ntids, config)

        else:
            self._barf('unknown ranseq mode')

        for ntid in bnode.ntids:
            self._render_next(ntid, txtp)
        txtp.group_done(bnode.ntids)

        return

#******************************************************************************

class RN_CAkLayerCntr(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        txtp.group_layer(bnode.ntids, config)
        for ntid in bnode.ntids:
            self._render_next(ntid, txtp)
        txtp.group_done(bnode.ntids)
        return

#******************************************************************************

class RN_CAkSound(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        txtp.info.source(bnode.sound.nsrc, bnode.sound.source)
        txtp.source_sound(bnode.sound, config)
        return

#******************************************************************************

class RN_CAkMusicSwitchCntr(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        self._register_transitions(bnode.rules)
        self._register_stingers(bnode.stingerlist)

        if bnode.ntid:
            # rarely tree plays a single object with any state
            txtp.group_single(config)
            self._render_next(bnode.ntid, txtp)
            txtp.group_done()
            return

        ws = self._ws
        if bnode.tree:
            if ws.gs_registrable():
                # find all possible gamesyncs paths (won't generate txtp)
                for path, ntid in bnode.tree.paths:
                    unreachable = ws.gspaths.adds(path)
                    if not unreachable:
                        self._render_next(ntid, txtp)
                    ws.gspaths.done()
                ws.gspaths.sort()
                return

            # find if current gamesync combo matches one of the paths
            npath_combo = bnode.tree.get_npath(ws.gsparams)
            if npath_combo:
                npath, ntid = npath_combo
                txtp.info.gamesyncs(npath)

                txtp.group_single(config)
                self._render_next(ntid, txtp)
                txtp.group_done()
            return

        else:
            gtype = bnode.gtype
            gname = bnode.ngname.value()

            if ws.gs_registrable():
                # find all possible gamesyncs paths (won't generate txtp)
                for ntid, ngvalue in bnode.gvalue_ntid.values(): #order doesn't matter
                    gvalue = ngvalue.value()
                    unreachable = ws.gspaths.add(gtype, gname, ngvalue.value())
                    if not unreachable:
                        self._render_next(ntid, txtp)
                    ws.gspaths.done()
                ws.gspaths.sort(True)
                return

            # get current gamesync
            gvalue = ws.gsparams.current(gtype, gname)
            if gvalue is None:
                return
            if not gvalue in bnode.gvalue_ntid:
                return
            ntid, ngvalue = bnode.gvalue_ntid[gvalue]
            txtp.info.gamesync(gtype, bnode.ngname, ngvalue)

            txtp.group_single(config)
            self._render_next(ntid, txtp)
            txtp.group_done()
            return

        return

#******************************************************************************

class RN_CAkMusicRanSeqCntr(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)
        config.rules = bnode.rules

        self._register_transitions(bnode.rules)
        self._register_stingers(bnode.stingerlist)

        txtp.group_single(config)
        self._render_playlist(txtp, bnode.items)
        txtp.group_done()

    def _render_playlist(self, txtp, items):
        if not items:
            return

        for item in items:
            type = item.type
            subitems = item.items

            iconfig = hnode_misc.NodeConfig()
            iconfig.loop = item.loop

            txtp.info.next(item.nitem, item.fields)
            #leaf node uses -1 in newer versions, sid in older (ex. Enslaved)
            if type == -1 or item.ntid:
                txtp.group_single(iconfig)
                self._render_next(item.ntid, txtp)
                txtp.group_done()
            else:
                if   type == 0: #0: ContinuousSequence (plays all objects in sequence, on loop/next call restarts)
                    txtp.group_sequence_continuous(subitems, iconfig)

                elif type == 1: #1: StepSequence (plays one object from first, on loop/next call plays next object)
                    txtp.group_sequence_step(subitems, iconfig)

                elif type == 2: #2: ContinuousRandom (plays all objects randomly, on loop/next call restarts)
                    txtp.group_random_continuous(subitems, iconfig)

                elif type == 3: #3: StepRandom (plays one object at random, on loop/next call plays another object)
                    txtp.group_random_step(subitems, iconfig)

                else:
                    self._barf('unknown musicranseq type')

                self._render_playlist(txtp, item.items)
                txtp.group_done(subitems)
            txtp.info.done()

        return


#******************************************************************************

class RN_CAkMusicSegment(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        config = self._calculate_config(bnode, txtp)

        config.duration = bnode.duration
        config.entry = bnode.entry
        config.exit = bnode.exit

        self._register_stingers(bnode.stingerlist)

        # empty segments are allowed as silence
        if not bnode.ntids:
            elems = [bnode.sound] #force some list to fool group_layer
            txtp.group_layer(elems, config)
            txtp.source_sound(bnode.sound, None)
            txtp.group_done(elems)

        else:
            txtp.group_layer(bnode.ntids, config)
            for ntid in bnode.ntids:
                self._render_next(ntid, txtp)
            txtp.group_done(bnode.ntids)
        return


#******************************************************************************

class RN_CAkMusicTrack(RN_CAkHircNode):

    def _render_txtp(self, bnode, txtp):
        if not bnode.subtracks: #empty / no clips
            return
        config = self._calculate_config(bnode, txtp)

        # musictrack can play in various ways
        if   bnode.type == 0: #normal (plays one subtrack, N aren't allowed)
            if len(bnode.subtracks) > 1:
                raise ValueError("more than 1 track")
            txtp.group_single(config)
            for subtrack in bnode.subtracks:
                self._render_clips(bnode, subtrack, txtp)
            txtp.group_done()

        elif bnode.type == 1: #random (plays random subtrack, on next call plays another)
            txtp.group_random_step(bnode.subtracks, config)
            for subtrack in bnode.subtracks:
                self._render_clips(bnode, subtrack, txtp)
            txtp.group_done(bnode.subtracks)

        elif bnode.type == 2: #sequence (plays first subtrack, on next call plays next)
            txtp.group_sequence_step(bnode.subtracks, config)
            for subtrack in bnode.subtracks:
                self._render_clips(bnode, subtrack, txtp)
            txtp.group_done(bnode.subtracks)

        elif bnode.type == 3: #switch (plays one subtrack depending on variables)
            gtype = bnode.gtype
            gname = bnode.ngname.value()

            ws = self._ws
            if ws.gs_registrable():
                # find all possible gamesyncs paths (won't generate txtp)
                for ngvalue in bnode.gvalue_names.values(): #order doesn't matter
                    if not ngvalue:
                        gvalue = 0
                    else:
                        gvalue = ngvalue.value()
                    ws.gspaths.add(gtype, gname, gvalue)
                    #no subnodes
                    ws.gspaths.done()
                ws.gspaths.sort(True)
                return

            # get current gamesync
            gvalue = ws.gsparams.current(gtype, gname)
            if gvalue is None:
                return
            if not gvalue in bnode.gvalue_indexes:
                return
            indexes = bnode.gvalue_indexes[gvalue]
            ngvalue = bnode.gvalue_names[gvalue]

            #play subtrack based on index (assumed to follow order as defined)
            txtp.info.gamesync(gtype, bnode.ngname, ngvalue)

            if not indexes:
                return # no subtrack, after adding path to gamesync (NHM3)

            # usually only 1 subtrack though
            subtracks = []
            for index in indexes:
                subtracks.append( bnode.subtracks[index] )

            txtp.group_layer(subtracks, None)
            for subtrack in subtracks:
                self._render_clips(bnode, subtrack, txtp)
            txtp.group_done(subtracks)

        else:
            self._barf('unknown musictrack mode')

        return

    def _render_clips(self, bnode, subtrack, txtp):
        if not subtrack:
            # rarely may happen with default = no track = silence (NMH3, Tetris Effect)
            # or if uDefaultSwitch = 0 meanings no group selected (can't select subtrack),
            # silence does play (from tests)
            sound = bnode.silence
            elems = [sound]
            txtp.group_layer(elems, None)
            txtp.source_sound(sound, None)
            txtp.group_done(elems)
            return

        txtp.group_layer(subtrack, None)
        for clip in subtrack:
            if clip.neid and clip.neid.value():
                # When a neid (event id) is set clip will be a full event, and since
                # it uses FPA to set when to start that clip, we can simulate it by using delay.
                #
                # In Wwise this event becomes separate/layered audio (may loop forever), so this isn't too
                # realistic but can't easily simulate that with .txtp, but for simple uses may work ok.
                econfig = hnode_misc.NodeConfig()
                econfig.delay = clip.sound.fpa
                econfig.playevent = True

                txtp.group_single(econfig)
                self._render_next_event(clip.neid, txtp)
                txtp.group_done()
            else:
                sound = clip.sound
                txtp.info.next(clip.nitem, clip.fields)
                txtp.info.source(clip.sound.nsrc, clip.sound.source)
                txtp.info.done()
                txtp.source_sound(clip.sound, None)
        txtp.group_done(subtrack)
        return
