
from Framework.Documentation import Doc_Category_Default
_doc_category = Doc_Category_Default('GUI')

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QTextCursor
from .Syntax_Highlighter import Script_Syntax_Highlighter

class Widget_Script(QtWidgets.QPlainTextEdit):
    '''
    Text edit box holding the current script.

    Attributes:
    * modified
      - Bool, True if this has been modified since Clear_Modified
        was called.
      - Handled manually since the widget isModified is missing
        from pyqt.
    * cursor
      - QTextCursor used to edit or analyze the document.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = False
        # Set up the cursor, attached to the document.
        self.cursor = QTextCursor(self.document())
        
        # Set up dragging. (TODO: maybe remove if set up in qt designer.)
        self.setAcceptDrops(True)

        self.modificationChanged.connect(self.Handle_modificationChanged)
        # Hook up a handler to the document's content change signal.
        self.document().contentsChange.connect(self.Handle_contentsChange)

        # Set up the QSyntaxHighlighter.
        # Note: this also connect to contentsChange, and qt will handle
        # connected handlers in their connection order; since the custom
        # handler edits the text, it needs to run before the highlighter
        # otherwise the highlight position can get thrown off (pointing
        # at changed positions). So, add this after setting up
        # the above connections to avoid the problem.
        self.highlighter = Script_Syntax_Highlighter(self.document())

        return


    def Clear_Modified(self):
        'Clears the modified flag.'
        # Clear the local flag and the hidden widget flag,
        # so that the widget triggers modificationChanged later.
        self.modified = False
        self.setWindowModified(False)
        return


    def Is_Modified(self):
        'Returns True if the text has been modified since Clear_Modified.'
        return self.modified


    def Handle_modificationChanged(self, arg = None):
        '''
        The text was modified since setModified(False) was called
        on it (from the main window).
        '''
        self.modified = True
        return


    def Handle_contentsChange(self, position, chars_removed, chars_added):
        '''
        Detect text changes, and maybe do some edits to clean them up.
        '''
        self.modified = True

        # Note: position is the start of the edited section, after
        # which chars are added (or from after which chars were removed,
        # or both).
        # Quirk: when a file is opened, there is a hidden EoL character
        # which is included in chars_added but cannot be positioned to.
        # As a workaround, check against the total document size, -1
        # for the eof.
        total_chars = self.document().characterCount() -1
        
        #-Removed; de-indent is handled by keyPressEvent with shift-tab,
        # instead of with space deletion (which is clumsy in practice).
        ## If a space is deleted, can try to detect if it is a multiple
        ##  of 4 from the start of the line, and if so, delete another 3.
        ## Only do this on a single character removal, with at least
        ##  3 characters prior to it, for backspaces; deletes will need
        ##  to check for 3 following spaces instead.
        ## It is unclear on how to detect what was removed, so this will
        ##  be blind to if it was a space or something else.
        #if chars_removed == 1 and chars_added == 0:
        #
        #    # Look back to check alignment with the start of the line.
        #    # TODO
        #
        #    # Loop over this, trying to look back, then forward.
        #    for start, end in [(position -3, position),
        #                       (position, position + 3)]:
        #        # Don't search past doc boundaries.
        #        # (Note: cursor can move to before or after a character,
        #        #  so the position range is char count +1.)
        #        if start < 0:
        #            continue
        #        if end > total_chars:
        #            continue
        #        # TODO: how to know when near the end of the doc.
        #
        #        # Set the anchor and position for implicit selection.
        #        self.cursor.setPosition(start, QTextCursor.MoveAnchor)
        #        self.cursor.setPosition(end, QTextCursor.KeepAnchor)
        #
        #        # Pull the chars.
        #        text = self.cursor.selectedText()
        #
        #        # If 3 spaces, remove the selection.
        #        if text == '   ':
        #            self.cursor.removeSelectedText()
        #            # Limit to one direction deletion
        #            break
        
        
        # For char additions, look for tabs and replace them.
        # Note: this can happen when text is copy/pasted in, with
        # tabs included, so this logic should try to catch any tab
        # within the new text body.
        if chars_added:
            # Limit the end point to the last non-eof character.
            start = position
            end = position + chars_added
            if end > total_chars:
                end = total_chars
                
            # Save the cursor position.
            old_position = self.textCursor().position()
            old_anchor   = self.textCursor().anchor()

            # Use the cursor to select what was added.
            # This involves setting the anchor to the selection start,
            # and cursor position to selection end.
            self.cursor.setPosition(start, QTextCursor.MoveAnchor)
            self.cursor.setPosition(end, QTextCursor.KeepAnchor)
            text = self.cursor.selectedText()
            if '\t' in text:
                # Replace the selected text with a copy that has
                # tabs swapped to spaces.
                # TODO: for some reason this clears the undo history,
                # though docs don't mention this behavior; look into why.
                self.cursor.insertText(text.replace('\t','    '))
                
            # TODO: fix this bit of code; it is giving a '-1' index
            # error for some reason; also, it may not be necessary.
            # Reset the cursor selection back to the original.
            #self.cursor.setPosition(old_anchor, QTextCursor.MoveAnchor)
            #self.cursor.setPosition(old_position, QTextCursor.KeepAnchor)
            
        return


    # TODO: the above could be better done by intercepting key pressed,
    # which would also allow adding shift-tab support.
    # https://stackoverflow.com/questions/13579116/qtextedit-shift-tab-wrong-behaviour
       
    def keyPressEvent(self, event):
        '''
        This function is called automatically when a key is pressed.
        The original version handles up/down/left/right/pageup/pagedown
        and ignores other keys.
        This wrapper will also catch shift-tab.
        This is triggered prior to contentsChange.
        '''
        if event.key() == QtCore.Qt.Key_Backtab:
            # The text cursor will need to be updated appropriately.
            # self.textCursor()
            # Get the place the edit is occurring.
            # The anchor may indicate a section of text is highlighted.
            # Proper handling of highlights in VS/notepad style would
            # be a little complicated...
            # TODO: think about this.

            # Get the current text cursor position/anchor.
            # Note: anchor can be before or after the position.
            position = self.textCursor().position()
            anchor   = self.textCursor().anchor()

            # Standardize the locations so 'start' is first, 'end' is second.
            if position > anchor:
                start = anchor
                end = position
            else:
                start = position
                end = anchor

            # If these differ, then a chunk of text is highlighted,
            # in which case all involved lines can have their
            # indentation changed. TODO.

            # Move the cursor to select 4 characters prior to
            # the original selection, to find out if they are
            # a group of spaces.
            self.cursor.setPosition(start, QTextCursor.MoveAnchor)
            self.cursor.setPosition(start -4, QTextCursor.KeepAnchor)
            text = self.cursor.selectedText()
            if text == '    ':
                # If there, shift-tab was pressed with 4 spaces prior
                # to the selected text. In this case, remove the
                # 4 spaces but do not modify the text selection.
                self.cursor.removeSelectedText()
                # Offset the original position/anchor back by 4.
                position -= 4
                anchor   -= 4

            # Reset the cursor selection back to the original, accounting
            # for the deleted text.
            self.cursor.setPosition(anchor, QTextCursor.MoveAnchor)
            self.cursor.setPosition(position, QTextCursor.KeepAnchor)

        else:
            # Just pass the call upward for now.
            super().keyPressEvent(event)
        return


    def New_Script(self):
        '''
        Create a new script.
        '''
        # Set up a default header, the function to apply hand edits,
        # and a function to write results.
        lines = [
            '# X4 Customizer input script.',
            'from Plugins import *',
            '',
            '# Apply hand edits from the GUI tables.',
            'Apply_Live_Editor_Patches()',
            '',
            '# Write modified files to the output extension.',
            'Write_To_Extension()',
            ]
        self.setPlainText('\n'.join(lines))
        self.Clear_Modified()
        return