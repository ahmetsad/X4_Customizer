
from Framework.Documentation import Doc_Category_Default
_doc_category = Doc_Category_Default('GUI')

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QTextCursor
from .XML_Syntax_Highlighter import XML_Syntax_Highlighter

class File_Text_Brower(QtWidgets.QPlainTextEdit):
    '''
    QPlainTextEdit holding a version of the file text, in readonly mode.
    TODO: record and use information on modified lines of text,
    for highlighting tweaks. Also, a re-highlight function.
    TODO: move the line number annotation from the main window
    to here, along with recording pre-numbered text.

    Attributes:
    * cursor
      - QTextCursor used to edit or analyze the document.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.modified = False
        # Set up the cursor, attached to the document.
        self.cursor = QTextCursor(self.document())
        
        # Set up the QSyntaxHighlighter.
        self.highlighter = XML_Syntax_Highlighter(self.document())
        return
